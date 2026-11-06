"""
Tests for Dialogue State Manager and Finite State Machine (FSM).
Verifies state transitions, barge-in interruption, context stack push/pop, and slot filling.
"""

import pytest
from app.modules.dialogue_state import DialogueStateManager
from app.schemas.dialogue_schema import (
    DialogueStateEnum,
    IntentEnum,
    BreakdownTypeEnum,
    StructuredResponse,
)
from app.knowledge.loader import sop_loader


def test_session_lifecycle():
    mgr = DialogueStateManager()
    session_id = "test_sess_001"
    session = mgr.get_or_create_session(session_id)
    assert session.session_id == session_id
    assert session.fsm_state == DialogueStateEnum.IDLE
    assert len(session.slots) == 0

    session.slots["device_type"] = "Windows"
    assert session.slots["device_type"] == "Windows"

    reset = mgr.reset_session(session_id)
    assert reset.fsm_state == DialogueStateEnum.IDLE
    assert len(reset.slots) == 0


def test_barge_in_handling():
    mgr = DialogueStateManager()
    session = mgr.get_or_create_session("sess_barge")
    session.is_speaking = True
    session.fsm_state = DialogueStateEnum.GROUNDED_EXECUTING

    # User interrupts via speech
    updated = mgr.handle_barge_in("sess_barge")
    assert updated.is_speaking is False
    assert updated.is_interrupted is True
    assert updated.fsm_state == DialogueStateEnum.LISTENING


def test_context_stack_digression():
    mgr = DialogueStateManager()
    session = mgr.get_or_create_session("sess_digress")
    session.active_sop_id = "SOP-WIFI-001"
    session.current_step_id = 2
    session.slots["device_type"] = "Windows"

    # User asks a digression question
    structured_digression = StructuredResponse(
        spoken_response="Lệnh này hoàn toàn an toàn.",
        intent=IntentEnum.DIGRESSION.value,
        matched_sop_id="SOP-WIFI-001",
        current_step_id=2,
        missing_slots=[],
        is_breakdown_detected=True,
        breakdown_type=BreakdownTypeEnum.DIGRESSION.value,
        action_summary="Side question"
    )

    updated = mgr.transition("sess_digress", structured_digression, "Lệnh này có mất dữ liệu không?")
    assert updated.fsm_state == DialogueStateEnum.BREAKDOWN_RECOVERY
    assert len(updated.state_stack) == 1
    assert updated.state_stack[0].sop_id == "SOP-WIFI-001"
    assert updated.state_stack[0].step_id == 2

    # User confirms after digression answered
    structured_confirm = StructuredResponse(
        spoken_response="Tiếp tục bước 3",
        intent=IntentEnum.CONFIRM_STEP.value,
        matched_sop_id="SOP-WIFI-001",
        current_step_id=3,
        missing_slots=[],
        is_breakdown_detected=False,
        breakdown_type=BreakdownTypeEnum.NONE.value,
        action_summary="Confirmed"
    )
    resumed = mgr.transition("sess_digress", structured_confirm, "Đã thấy reply rồi")
    assert resumed.fsm_state == DialogueStateEnum.GROUNDED_EXECUTING
    assert len(resumed.state_stack) == 0  # Context stack popped


def test_full_sop_step_progression_to_resolved():
    mgr = DialogueStateManager()
    session = mgr.get_or_create_session("sess_progression")
    session.active_sop_id = "SOP-WIFI-001"
    session.current_step_id = 1
    sop = sop_loader.get("SOP-WIFI-001")
    assert sop is not None

    # Step 1 confirmation
    struct_s1 = StructuredResponse(
        spoken_response="Chuyển sang bước 2",
        intent=IntentEnum.CONFIRM_STEP.value,
        matched_sop_id="SOP-WIFI-001",
        current_step_id=2,
        action_summary="Step 1 done"
    )
    mgr.transition("sess_progression", struct_s1, "Tôi đã thấy IP rồi")
    assert session.current_step_id == 2
    assert 1 in session.completed_steps

    # Step 2 confirmation
    struct_s2 = StructuredResponse(
        spoken_response="Chuyển sang bước 3",
        intent=IntentEnum.CONFIRM_STEP.value,
        matched_sop_id="SOP-WIFI-001",
        current_step_id=3,
        action_summary="Step 2 done"
    )
    mgr.transition("sess_progression", struct_s2, "Có reply from rồi")
    assert session.current_step_id == 3
    assert 2 in session.completed_steps

    # Step 3 confirmation (Final step)
    struct_s3 = StructuredResponse(
        spoken_response="Hoàn tất quy trình",
        intent=IntentEnum.CONFIRM_STEP.value,
        matched_sop_id="SOP-WIFI-001",
        current_step_id=3,
        action_summary="Step 3 done"
    )
    mgr.transition("sess_progression", struct_s3, "Đã làm mới xong và vào mạng bình thường rồi")
    assert 3 in session.completed_steps
    assert session.fsm_state == DialogueStateEnum.RESOLVED
