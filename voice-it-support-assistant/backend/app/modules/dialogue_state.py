"""
Dialogue State Manager and Finite State Machine (FSM).
Handles Slot Tracking, Context Stack for Digression, Execution Failure Fallback,
and Barge-in / Interruption state transitions.
"""

from __future__ import annotations
import time
from typing import Dict, Any, Optional, List, Tuple
from app.schemas.dialogue_schema import (
    DialogueStateEnum,
    IntentEnum,
    BreakdownTypeEnum,
    StructuredResponse,
    DialogueTurn,
    ContextStackItem,
    SessionState,
)
from app.knowledge.loader import SOPDocument, SOPStep, sop_loader
from app.core.logging import logger


class DialogueStateManager:
    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}

    def get_or_create_session(self, session_id: str) -> SessionState:
        """Retrieves an existing session or initializes a fresh one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(
                session_id=session_id,
                fsm_state=DialogueStateEnum.IDLE,
                slots={},
                active_sop_id=None,
                current_step_id=None,
                completed_steps=[],
                state_stack=[],
                turn_history=[],
                last_user_input="",
                is_speaking=False,
                is_interrupted=False,
            )
        return self._sessions[session_id]

    def reset_session(self, session_id: str) -> SessionState:
        """Resets dialogue state for a fresh conversation."""
        self._sessions[session_id] = SessionState(
            session_id=session_id,
            fsm_state=DialogueStateEnum.IDLE,
            slots={},
            active_sop_id=None,
            current_step_id=None,
            completed_steps=[],
            state_stack=[],
            turn_history=[],
            last_user_input="",
            is_speaking=False,
            is_interrupted=False,
        )
        return self._sessions[session_id]

    def handle_barge_in(self, session_id: str) -> SessionState:
        """
        Handles Barge-in / Interruption event:
        Fired when user speech is detected while the bot is speaking.
        Instantly halts bot speech and transitions state to LISTENING.
        """
        session = self.get_or_create_session(session_id)
        logger.info(f"Barge-in triggered for session {session_id}. Canceling TTS playback.")
        session.is_speaking = False
        session.is_interrupted = True
        session.fsm_state = DialogueStateEnum.LISTENING
        return session

    def push_context_stack(self, session: SessionState, prompt_context: str = ""):
        """Pushes current grounded SOP step to context stack to handle digressions."""
        if session.active_sop_id and session.current_step_id:
            session.state_stack.append(
                ContextStackItem(
                    sop_id=session.active_sop_id,
                    step_id=session.current_step_id,
                    slots=session.slots.copy(),
                    prompt_context=prompt_context,
                )
            )
            logger.info(
                f"Pushed context stack: SOP={session.active_sop_id}, Step={session.current_step_id}. "
                f"Stack depth: {len(session.state_stack)}"
            )

    def pop_context_stack(self, session: SessionState) -> Optional[ContextStackItem]:
        """Pops previous troubleshooting context after resolving a digression."""
        if session.state_stack:
            item = session.state_stack.pop()
            session.active_sop_id = item.sop_id
            session.current_step_id = item.step_id
            session.slots.update(item.slots)
            logger.info(
                f"Popped context stack: Resumed SOP={item.sop_id}, Step={item.step_id}. "
                f"Remaining stack depth: {len(session.state_stack)}"
            )
            return item
        return None

    def update_slots_from_text(self, session: SessionState, text: str) -> Dict[str, Any]:
        """Heuristic slot extraction for device types, OS, and usernames."""
        text_lower = text.lower()

        # Device / OS extraction
        if any(w in text_lower for w in ("windows", "win 10", "win 11", "win 7", "máy tính bàn", "pc", "laptop win")):
            session.slots["device_type"] = "Windows"
        elif any(w in text_lower for w in ("mac", "macbook", "macos", "apple", "máy mac")):
            session.slots["device_type"] = "macOS"
        elif any(w in text_lower for w in ("điện thoại", "iphone", "android", "samsung", "ipad")):
            session.slots["device_type"] = "Mobile"

        # Connection type
        if "wifi" in text_lower or "wi-fi" in text_lower or "không dây" in text_lower:
            session.slots["connection_type"] = "Wi-Fi"
        elif "dây mạng" in text_lower or "cáp mạng" in text_lower or "lan" in text_lower:
            session.slots["connection_type"] = "Ethernet"

        return session.slots

    def check_step_confirmation(
        self,
        session: SessionState,
        user_text: str,
        active_sop: SOPDocument
    ) -> bool:
        """
        Determines if user input satisfies the expected confirmation for the current step.
        """
        if not session.current_step_id:
            return False

        step = active_sop.get_step(session.current_step_id)
        if not step:
            return False

        user_lower = user_text.lower()

        # Check explicit expected confirmations from SOP metadata
        for expected in step.expected_confirmation:
            if expected.lower() in user_lower:
                return True

        # Generic positive confirmations in Vietnamese
        generic_confirmations = [
            "xong rồi", "đã xong", "rồi nhé", "được rồi", "thấy rồi", "ra rồi",
            "ok rồi", "đã gõ rồi", "làm xong rồi", "thành công rồi", "đã làm rồi",
            "vào được mạng rồi", "vào được rồi", "lướt web được rồi", "mạng bình thường rồi",
            "được rồi nhé", "ổn rồi", "vào mạng được rồi", "đã vào được mạng"
        ]
        return any(c in user_lower for c in generic_confirmations)

    def transition(
        self,
        session_id: str,
        structured: StructuredResponse,
        user_text: str
    ) -> SessionState:
        """
        Core FSM Transition Function.
        Applies LLM NLU structured output and grounding rules to advance the state machine.
        """
        session = self.get_or_create_session(session_id)
        session.last_user_input = user_text
        session.is_interrupted = False

        # 1. Update Slots
        self.update_slots_from_text(session, user_text)

        # 2. Check for Escalation
        if structured.intent == IntentEnum.ESCALATE.value:
            session.fsm_state = DialogueStateEnum.ESCALATED
            return session

        # 3. Check for Digression Breakdown
        if structured.is_breakdown_detected and structured.breakdown_type == BreakdownTypeEnum.DIGRESSION.value:
            # Save current step if active
            if session.active_sop_id and session.current_step_id:
                self.push_context_stack(session, prompt_context=user_text)
            session.fsm_state = DialogueStateEnum.BREAKDOWN_RECOVERY
            return session

        # 4. Check for Execution Failure Breakdown
        if structured.is_breakdown_detected and structured.breakdown_type == BreakdownTypeEnum.EXECUTION_FAILURE.value:
            session.fsm_state = DialogueStateEnum.BREAKDOWN_RECOVERY
            return session

        # 5. Check Missing Slots (Proactive Clarification)
        if structured.missing_slots:
            session.fsm_state = DialogueStateEnum.SLOT_FILLING
            if structured.matched_sop_id:
                session.active_sop_id = structured.matched_sop_id
            return session

        # 6. Bind Active SOP
        if structured.matched_sop_id:
            session.active_sop_id = structured.matched_sop_id

        # If we have an active SOP, evaluate step progression
        if session.active_sop_id:
            sop = sop_loader.get(session.active_sop_id)
            if sop:
                # If step is not set yet, initialize to step 1
                if session.current_step_id is None:
                    session.current_step_id = structured.current_step_id or 1
                    session.fsm_state = DialogueStateEnum.GROUNDED_EXECUTING
                else:
                    # Check if user confirmed the current step
                    is_confirmed = (
                        structured.intent in (IntentEnum.CONFIRM_STEP.value, IntentEnum.RESOLVE.value) or
                        self.check_step_confirmation(session, user_text, sop)
                    )

                    if is_confirmed:
                        if session.current_step_id not in session.completed_steps:
                            session.completed_steps.append(session.current_step_id)

                        # Advance to next step or resolve
                        if structured.intent == IntentEnum.RESOLVE.value or session.current_step_id >= sop.get_step_count():
                            session.fsm_state = DialogueStateEnum.RESOLVED
                        else:
                            session.current_step_id += 1
                            session.fsm_state = DialogueStateEnum.GROUNDED_EXECUTING
                    else:
                        session.fsm_state = DialogueStateEnum.CONFIRMING_STEP
            else:
                session.fsm_state = DialogueStateEnum.GROUNDED_EXECUTING
        else:
            session.fsm_state = DialogueStateEnum.LISTENING

        # If previous digression existed and user is back on track, pop stack
        if session.state_stack and session.fsm_state in (DialogueStateEnum.GROUNDED_EXECUTING, DialogueStateEnum.CONFIRMING_STEP):
            self.pop_context_stack(session)

        return session


# Global singleton instance
dialogue_state_manager = DialogueStateManager()
