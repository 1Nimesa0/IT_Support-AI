"""
Dialogue Orchestration Endpoints: Turn-based REST API and Real-Time WebSocket.
Handles low-latency streaming (<1.5s), voice barge-in, and dialogue breakdown recovery.
"""

from __future__ import annotations
import base64
import json
import time
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.modules.dialogue_state import dialogue_state_manager
from app.modules.nlu_grounding import nlu_engine
from app.modules.asr_service import asr_service
from app.modules.tts_service import tts_service
from app.schemas.dialogue_schema import (
    DialogueTurnRequest,
    DialogueTurnResponse,
    StructuredResponse,
    DialogueTurn,
    DialogueStateEnum,
)
from app.core.logging import logger

router = APIRouter()


@router.post("/turn", response_model=DialogueTurnResponse)
async def process_dialogue_turn(request: DialogueTurnRequest):
    """
    REST endpoint to execute a single turn of grounded dialogue troubleshooting.
    """
    session = dialogue_state_manager.get_or_create_session(request.session_id)
    if request.device_type:
        session.slots["device_type"] = request.device_type

    # Execute NLU Grounding
    structured_response = None
    async for kind, payload in nlu_engine.stream_nlu_response(request.user_text, session):
        if kind == "completed_json":
            structured_response = payload

    if not structured_response:
        raise HTTPException(status_code=500, detail="NLU failed to generate grounded response")

    # Apply FSM Transitions
    updated_session = dialogue_state_manager.transition(
        session_id=request.session_id,
        structured=structured_response,
        user_text=request.user_text,
    )

    # Record turns in history
    now = time.time()
    updated_session.turn_history.append(
        DialogueTurn(speaker="user", text=request.user_text, timestamp=now)
    )
    updated_session.turn_history.append(
        DialogueTurn(
            speaker="assistant",
            text=structured_response.spoken_response,
            timestamp=now,
            structured=structured_response,
            sop_id=updated_session.active_sop_id,
            step_id=updated_session.current_step_id,
        )
    )

    return DialogueTurnResponse(
        session_id=request.session_id,
        fsm_state=updated_session.fsm_state,
        structured=structured_response,
        slots=updated_session.slots,
        active_sop_id=updated_session.active_sop_id,
        current_step_id=updated_session.current_step_id,
        completed_steps=updated_session.completed_steps,
    )


@router.websocket("/ws/{session_id}")
async def dialogue_websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Full-duplex WebSocket connection for real-time speech dialogue.
    Handles VAD barge-in interruptions, instant TTS chunk streaming, and state sync.
    """
    await websocket.accept()
    session = dialogue_state_manager.get_or_create_session(session_id)
    logger.info(f"WebSocket client connected for session: {session_id}")

    # Reference to currently active TTS streaming background task
    active_tts_task: Optional[asyncio.Task] = None

    async def stream_audio_to_client(spoken_text: str):
        """Asynchronously streams TTS audio chunks over WebSocket."""
        try:
            chunk_idx = 0
            session.is_speaking = True
            async for audio_chunk in tts_service.stream_audio_chunks(spoken_text):
                if session.is_interrupted or not session.is_speaking:
                    logger.info("Halting TTS stream due to barge-in.")
                    break

                b64_audio = base64.b64encode(audio_chunk).decode("utf-8")
                await websocket.send_json({
                    "type": "tts_chunk",
                    "chunk_index": chunk_idx,
                    "audio_base64": b64_audio,
                    "is_final": False,
                })
                chunk_idx += 1
                # Tiny yield to allow event loop to process incoming barge-in frames
                await asyncio.sleep(0.005)

            if not session.is_interrupted and session.is_speaking:
                await websocket.send_json({"type": "tts_end", "total_chunks": chunk_idx})
        except asyncio.CancelledError:
            logger.info("TTS streaming task canceled by barge-in.")
        except Exception as e:
            logger.error(f"Error in TTS streaming: {e}")
        finally:
            session.is_speaking = False

    try:
        # Send initial greeting state
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "fsm_state": session.fsm_state.value,
            "slots": session.slots,
        })

        while True:
            raw_msg = await websocket.receive_text()
            try:
                data = json.loads(raw_msg)
            except Exception:
                continue

            msg_type = data.get("type", "")

            # 1. BARGE-IN INTERRUPTION EVENT
            if msg_type == "barge_in":
                logger.info(f"Received BARGE_IN event from client for session {session_id}")
                dialogue_state_manager.handle_barge_in(session_id)
                if active_tts_task and not active_tts_task.done():
                    active_tts_task.cancel()
                    active_tts_task = None

                await websocket.send_json({
                    "type": "barge_in_confirmed",
                    "status": "tts_stopped",
                    "fsm_state": DialogueStateEnum.LISTENING.value,
                })
                continue

            # 2. SESSION RESET EVENT
            if msg_type == "reset":
                session = dialogue_state_manager.reset_session(session_id)
                if active_tts_task and not active_tts_task.done():
                    active_tts_task.cancel()
                await websocket.send_json({
                    "type": "session_reset",
                    "fsm_state": session.fsm_state.value,
                    "slots": session.slots,
                })
                continue

            # Extract user input (audio or text)
            user_text = ""
            if msg_type == "user_speech":
                # Audio base64 payload
                b64_audio = data.get("audio_base64", "")
                if not b64_audio:
                    continue
                audio_bytes = base64.b64decode(b64_audio)
                
                # Transcribe with domain biasing & normalization
                asr_result = await asr_service.transcribe_audio(audio_bytes)
                user_text = asr_result.normalized_text

                await websocket.send_json({
                    "type": "transcription",
                    "raw_text": asr_result.raw_text,
                    "normalized_text": asr_result.normalized_text,
                    "confidence": asr_result.confidence,
                })
            elif msg_type == "user_text":
                user_text = asr_service.apply_text_normalization(data.get("text", ""))
            else:
                continue

            if not user_text.strip():
                continue

            logger.info(f"Processing dialogue turn for user text: '{user_text}'")
            await websocket.send_json({"type": "nlu_start", "query": user_text})

            # Check if previous TTS was still active, cancel it before new turn
            if active_tts_task and not active_tts_task.done():
                active_tts_task.cancel()
                active_tts_task = None

            # Stream NLU with partial JSON early parser (<1.5s latency)
            structured_res: Optional[StructuredResponse] = None
            spoken_started = False

            async for kind, payload in nlu_engine.stream_nlu_response(user_text, session):
                if kind == "spoken_early" and not spoken_started:
                    spoken_started = True
                    spoken_text = str(payload)
                    # Send early spoken text info to client
                    await websocket.send_json({
                        "type": "spoken_response_early",
                        "spoken_text": spoken_text,
                    })
                    # Kick off Edge-TTS streaming task immediately in background
                    active_tts_task = asyncio.create_task(stream_audio_to_client(spoken_text))

                elif kind == "completed_json":
                    structured_res = payload

            if not structured_res:
                structured_res = StructuredResponse(
                    spoken_response="Tôi đang kiểm tra lại hệ thống, bạn chờ giây lát nhé.",
                    intent="unknown",
                    action_summary="Lỗi xử lý luồng suy luận"
                )

            # Update FSM State
            updated_session = dialogue_state_manager.transition(
                session_id=session_id,
                structured=structured_res,
                user_text=user_text,
            )

            # Record turn
            now = time.time()
            updated_session.turn_history.append(
                DialogueTurn(speaker="user", text=user_text, timestamp=now)
            )
            updated_session.turn_history.append(
                DialogueTurn(
                    speaker="assistant",
                    text=structured_res.spoken_response,
                    timestamp=now,
                    structured=structured_res,
                    sop_id=updated_session.active_sop_id,
                    step_id=updated_session.current_step_id,
                    breakdown_type=structured_res.breakdown_type,
                )
            )

            # Broadcast dialogue update to frontend
            await websocket.send_json({
                "type": "dialogue_update",
                "session_id": session_id,
                "fsm_state": updated_session.fsm_state.value,
                "structured": structured_res.dict(),
                "slots": updated_session.slots,
                "active_sop_id": updated_session.active_sop_id,
                "current_step_id": updated_session.current_step_id,
                "completed_steps": updated_session.completed_steps,
            })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        if active_tts_task and not active_tts_task.done():
            active_tts_task.cancel()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if active_tts_task and not active_tts_task.done():
            active_tts_task.cancel()
