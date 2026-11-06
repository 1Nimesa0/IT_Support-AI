"""
Tests for Knowledge Grounding Rules, Zero-Hallucination Guardrails, and SOP Retrieval.
Verifies proactive slot filling, breakdown recovery, and streaming early JSON parsing.
"""

import pytest
import asyncio
from app.knowledge.loader import sop_loader
from app.knowledge.vector_store import vector_store
from app.modules.nlu_grounding import NLUGroundingEngine, nlu_engine
from app.modules.dialogue_state import dialogue_state_manager
from app.schemas.dialogue_schema import BreakdownTypeEnum, IntentEnum


def test_sop_loader_ten_documents():
    docs = sop_loader.all()
    assert len(docs) >= 10, f"Expected at least 10 SOP documents, got {len(docs)}"
    
    sop_ids = [d.sop_id for d in docs]
    assert "SOP-WIFI-001" in sop_ids
    assert "SOP-WIFI-002" in sop_ids
    assert "SOP-WIFI-003" in sop_ids
    assert "SOP-WIFI-004" in sop_ids
    assert "SOP-WIFI-005" in sop_ids
    assert "SOP-AUTH-001" in sop_ids
    assert "SOP-AUTH-002" in sop_ids
    assert "SOP-AUTH-003" in sop_ids
    assert "SOP-AUTH-004" in sop_ids
    assert "SOP-NET-001" in sop_ids


def test_vector_store_retrieval():
    results_wifi = vector_store.search("mạng chấm than vàng không vào được web", top_k=1)
    assert len(results_wifi) > 0
    assert results_wifi[0].sop.sop_id == "SOP-WIFI-001"

    results_lockout = vector_store.search("tài khoản nhân viên bị khóa không đăng nhập được", top_k=1)
    assert len(results_lockout) > 0
    assert results_lockout[0].sop.sop_id == "SOP-AUTH-001"

    results_vpn = vector_store.search("vpn không kết nối được dừng ở 40%", top_k=1)
    assert len(results_vpn) > 0
    assert results_vpn[0].sop.sop_id == "SOP-NET-001"


def test_proactive_slot_filling_guardrail():
    """
    CRITICAL ACCEPTANCE CRITERIA:
    When user inputs 'Mạng cơ quan tôi không vào được', system must immediately ask:
    'Bạn đang dùng máy tính Windows, Mac hay điện thoại vậy?' (proactive slot filling).
    """
    session = dialogue_state_manager.reset_session("test_slot_fill")
    res = nlu_engine._grounded_rule_inference("Mạng cơ quan tôi không vào được", session)

    assert "Bạn đang dùng máy tính Windows, Mac hay điện thoại vậy?" in res.spoken_response
    assert "device_type" in res.missing_slots
    assert res.intent == IntentEnum.CLARIFY_MISSING_INFO.value


def test_slot_filling_resolution_flow():
    """Test full 2-turn slot filling -> grounded execution progression."""
    session_id = "test_slot_fill_resolve"
    session = dialogue_state_manager.reset_session(session_id)

    # Turn 1: User states generic network issue -> proactive slot filling
    t1 = nlu_engine._grounded_rule_inference("Mạng cơ quan tôi không vào được", session)
    dialogue_state_manager.transition(session_id, t1, "Mạng cơ quan tôi không vào được")
    assert session.fsm_state.value == "SLOT_FILLING"
    assert session.active_sop_id == "SOP-WIFI-001"

    # Turn 2: User answers with device type -> transitions to Step 1 grounded execution
    t2 = nlu_engine._grounded_rule_inference("Tôi dùng máy tính Windows", session)
    dialogue_state_manager.transition(session_id, t2, "Tôi dùng máy tính Windows")
    assert session.slots["device_type"] == "Windows"
    assert session.fsm_state.value == "GROUNDED_EXECUTING"
    assert "ipconfig" in t2.spoken_response


def test_sop_final_step_resolved():
    """Test confirming the final step 3 with 'vào được mạng rồi' marks the session as RESOLVED."""
    session_id = "test_sop_resolve"
    session = dialogue_state_manager.reset_session(session_id)
    session.active_sop_id = "SOP-WIFI-001"
    session.current_step_id = 3
    session.completed_steps = [1, 2]

    res = nlu_engine._grounded_rule_inference("vào được mạng rồi", session)
    dialogue_state_manager.transition(session_id, res, "vào được mạng rồi")

    assert res.intent == IntentEnum.RESOLVE.value
    assert session.fsm_state.value == "RESOLVED"
    assert 3 in session.completed_steps
    assert "hoàn tất" in res.spoken_response.lower()


def test_execution_failure_breakdown_recovery():
    """
    CRITICAL ACCEPTANCE CRITERIA:
    When bot asks to run ipconfig and user responds 'Nó báo lệnh không hợp lệ hoặc tôi gõ sai',
    system must gracefully detect execution_failure and explain fallback:
    'Bạn hãy kiểm tra xem có gõ đúng chữ i-p-c-o-n-f-i-g viết liền không dấu nhé'.
    """
    session = dialogue_state_manager.reset_session("test_exec_failure")
    session.active_sop_id = "SOP-WIFI-001"
    session.current_step_id = 1
    session.slots["device_type"] = "Windows"

    res = nlu_engine._grounded_rule_inference("Nó báo lệnh không hợp lệ hoặc tôi gõ sai", session)

    assert res.is_breakdown_detected is True
    assert res.breakdown_type == BreakdownTypeEnum.EXECUTION_FAILURE.value
    assert "i-p-c-o-n-f-i-g" in res.spoken_response or "kiểm tra" in res.spoken_response


def test_early_json_extraction():
    """
    CRITICAL ACCEPTANCE CRITERIA:
    Test streaming partial JSON parsing extracts spoken_response before remainder finishes.
    """
    partial_buffer = (
        '{\n  "spoken_response": "Trước tiên bạn mở cửa sổ Run bằng phím Win R nhé.",\n'
        '  "intent": "diagnose_wifi",\n'
    )
    early_spoken = NLUGroundingEngine.extract_spoken_response_early(partial_buffer)
    assert early_spoken == "Trước tiên bạn mở cửa sổ Run bằng phím Win R nhé."

    # Partial buffer with escaped quotes
    partial_escaped = '{"spoken_response": "Gõ lệnh \\"ipconfig\\" rồi nhấn Enter."}'
    early_escaped = NLUGroundingEngine.extract_spoken_response_early(partial_escaped)
    assert 'Gõ lệnh "ipconfig" rồi nhấn Enter.' in early_escaped
