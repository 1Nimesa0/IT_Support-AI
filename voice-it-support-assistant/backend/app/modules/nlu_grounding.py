"""
NLU Grounding & Structured Output Orchestration.
Integrates Groq (llama-3.3-70b-versatile) / OpenAI with strict JSON output,
zero-hallucination guardrails, and streaming partial JSON parser for < 1.5s TTS latency.
"""

from __future__ import annotations
import json
import re
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, Tuple, List
from app.core.config import settings
from app.core.logging import logger
from app.schemas.dialogue_schema import (
    StructuredResponse,
    IntentEnum,
    BreakdownTypeEnum,
    SessionState,
    DialogueStateEnum,
)
from app.knowledge.loader import SOPDocument, SOPStep, sop_loader
from app.knowledge.vector_store import vector_store

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class NLUGroundingEngine:
    SYSTEM_INSTRUCTION = """Bạn là trợ lý AI chuyên gia hỗ trợ kỹ thuật IT Helpdesk (Voice-Based IT Support Assistant).
Nhiệm vụ của bạn là chẩn đoán và hướng dẫn người dùng khắc phục sự cố máy tính và mạng dựa CHÍNH XÁC trên Quy Trình Chuẩn (SOP) được cung cấp.

CÁC NGUYÊN TẮC CỐT LÕI (ZERO-HALLUCINATION & GUARDRAILS):
1. KHÔNG ĐƯỢC TỰ BỊA ĐẶT CÁC BƯỚC NGOÀI QUY TRÌNH SOP:
   Mọi chỉ dẫn kỹ thuật, lệnh Command Prompt phải được rút ra chuẩn xác từ tài liệu SOP được gắn kèm.
2. CHỦ ĐỘNG HỎI LÀM RÕ (SLOT FILLING):
   Nếu chưa biết thiết bị của người dùng (Windows, Mac hay điện thoại) hoặc triệu chứng mơ hồ, TUYỆT ĐỐI KHÔNG đoán mò. Hãy hỏi ngay: "Bạn đang dùng máy tính Windows, Mac hay điện thoại vậy?".
3. PHÁT HIỆN SỰ CỐ HỘI THOẠI (BREAKDOWN DETECTION):
   - execution_failure: Khi người dùng báo lỗi, gõ sai lệnh ("báo lệnh không hợp lệ", "không bấm được phím tắt"), hãy chuyển sang hướng dẫn dự phòng (fallback_instruction) hoặc phím tắt thay thế.
   - digression: Khi người dùng hỏi chuyện bên lề trong lúc làm, trả lời ngắn gọn 1 câu rồi kéo người dùng quay lại bước đang làm.
4. TỐC ĐỘ PHẢN HỒI (LATENCY TARGET):
   Câu trả lời thoại ('spoken_response') PHẢI NGẮN GỌN (tối đa 2 câu), tự nhiên, hướng dẫn rõ ràng.

QUY ĐỊNH BẮT BUỘC ĐỊNH DẠNG JSON:
Bạn PHẢI trả về đúng định dạng JSON có khóa 'spoken_response' ĐỨNG ĐẦU TIÊN để hệ thống phân tách stream TTS:
{
  "spoken_response": "Câu nói thoại ngắn gọn tự nhiên để phát ra loa",
  "intent": "diagnose_wifi | reset_password | mfa_issue | vpn_failure | clarify_missing_info | escalate",
  "matched_sop_id": "Mã SOP hoặc null",
  "current_step_id": 1,
  "missing_slots": ["device_type"],
  "is_breakdown_detected": false,
  "breakdown_type": "none | misrecognition | execution_failure | digression",
  "action_summary": "Tóm tắt hành động hiển thị lên bảng điều khiển"
}
"""

    def __init__(self):
        self.groq_client = None
        self.openai_client = None

        if settings.GROQ_API_KEY and Groq:
            try:
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to init Groq client: {e}")

        if settings.OPENAI_API_KEY and OpenAI:
            try:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to init OpenAI client: {e}")

    @staticmethod
    def extract_spoken_response_early(partial_text: str) -> Optional[str]:
        """
        Parses the first 'spoken_response' key from the streaming JSON buffer
        as soon as its string value is closed. Enables immediate TTS chunk synthesis (<1.5s).
        """
        # Look for "spoken_response": "..."
        pattern = r'"spoken_response"\s*:\s*"((?:\\.|[^"\\])*)"'
        match = re.search(pattern, partial_text)
        if match:
            # Unescape JSON string
            try:
                return json.loads(f'"{match.group(1)}"')
            except Exception:
                return match.group(1)
        return None

    def build_prompt_context(self, user_text: str, session: SessionState) -> str:
        """
        Retrieves relevant SOP chunks from Vector Store and formats system context.
        """
        context_parts = []

        # Current session state info
        context_parts.append(f"--- TRẠNG THÁI HIỆN TẠI CỦA PHIÊN ---")
        context_parts.append(f"- FSM State: {session.fsm_state.value}")
        context_parts.append(f"- Đã lưu Slots: {json.dumps(session.slots, ensure_ascii=False)}")
        context_parts.append(f"- Active SOP: {session.active_sop_id or 'Chưa có'}")
        context_parts.append(f"- Current Step: {session.current_step_id or 'Chưa có'}")
        context_parts.append(f"- Completed Steps: {session.completed_steps}")

        # Active or Retrieved SOP
        sop = None
        if session.active_sop_id:
            sop = sop_loader.get(session.active_sop_id)

        if not sop:
            # Retrieve candidate SOP from vector store
            matches = vector_store.search(user_text, top_k=2)
            if matches:
                sop = matches[0].sop
                context_parts.append(f"\n--- TÀI LIỆU SOP ĐƯỢC TRÍCH XUẤT (ĐỘ TỰ TIN: {matches[0].score}) ---")
                context_parts.append(sop.to_chunk_text())
                if len(matches) > 1:
                    context_parts.append(f"\n[Gợi ý phụ: {matches[1].sop.sop_id} - {matches[1].sop.title}]")
        else:
            context_parts.append(f"\n--- TÀI LIỆU SOP ĐANG THỰC HIỆN ---")
            context_parts.append(sop.to_chunk_text())

        return "\n".join(context_parts)

    async def stream_nlu_response(
        self,
        user_text: str,
        session: SessionState
    ) -> AsyncGenerator[Tuple[str, Optional[StructuredResponse]], None]:
        """
        Streams LLM generation:
        Yields ('spoken_chunk', spoken_response_string) as soon as early parser detects it.
        Finally yields ('completed_json', final_StructuredResponse).
        """
        # If in Mock mode or offline, use deterministic grounded rule engine
        if settings.is_mock_mode or (not self.groq_client and not self.openai_client):
            logger.info("Executing NLU Grounding via Rule-Based Grounded Engine (Mock/Fast Mode).")
            structured = self._grounded_rule_inference(user_text, session)
            # Yield spoken response immediately
            yield ("spoken_early", structured.spoken_response)
            await asyncio.sleep(0.05)
            yield ("completed_json", structured)
            return

        # Real LLM API call with streaming
        prompt_context = self.build_prompt_context(user_text, session)
        messages = [
            {"role": "system", "content": self.SYSTEM_INSTRUCTION},
            {"role": "system", "content": prompt_context},
            {"role": "user", "content": user_text}
        ]

        stream_buffer = ""
        spoken_early_sent = False

        try:
            if self.groq_client:
                response = self.groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    stream=True,
                )
            else:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    stream=True,
                )

            for chunk in response:
                delta = chunk.choices[0].delta.content or ""
                stream_buffer += delta

                if not spoken_early_sent:
                    spoken = self.extract_spoken_response_early(stream_buffer)
                    if spoken:
                        spoken_early_sent = True
                        yield ("spoken_early", spoken)

            # Parse full JSON object
            final_data = json.loads(stream_buffer)
            structured = StructuredResponse(**final_data)
            yield ("completed_json", structured)

        except Exception as e:
            logger.error(f"Streaming LLM failed: {e}. Falling back to grounded rule engine.")
            structured = self._grounded_rule_inference(user_text, session)
            if not spoken_early_sent:
                yield ("spoken_early", structured.spoken_response)
            yield ("completed_json", structured)

    def _grounded_rule_inference(
        self,
        user_text: str,
        session: SessionState
    ) -> StructuredResponse:
        """
        High-fidelity Grounded Dialogue Decision Engine.
        Implements strict grounding, proactive slot filling, breakdown detection,
        and fallback execution matching exact acceptance criteria.
        """
        user_lower = user_text.lower()

        # 1. Proactive Slot Filling Check: Device type missing for general connectivity issues
        has_device = "device_type" in session.slots
        is_generic_net_issue = any(
            p in user_lower for p in ("mạng cơ quan tôi không vào được", "không vào được mạng", "mất mạng", "không lướt web được")
        )
        if is_generic_net_issue and not has_device and not session.active_sop_id:
            # Bind candidate SOP so dialogue state remembers it
            matches = vector_store.search(user_text, top_k=1)
            candidate_sop_id = matches[0].sop.sop_id if matches else "SOP-WIFI-001"

            return StructuredResponse(
                spoken_response="Bạn đang dùng máy tính Windows, Mac hay điện thoại vậy?",
                intent=IntentEnum.CLARIFY_MISSING_INFO.value,
                matched_sop_id=candidate_sop_id,
                current_step_id=1,
                missing_slots=["device_type"],
                is_breakdown_detected=False,
                breakdown_type=BreakdownTypeEnum.NONE.value,
                action_summary="Yêu cầu làm rõ loại thiết bị (Windows / macOS / Mobile)"
            )

        # 1b. Slot-filling resolution: User provides missing device type
        just_provided_device = any(w in user_lower for w in ("windows", "win", "mac", "macbook", "điện thoại", "pc", "laptop", "máy tính"))
        if (session.fsm_state == DialogueStateEnum.SLOT_FILLING or session.active_sop_id) and just_provided_device:
            target_sop_id = session.active_sop_id or "SOP-WIFI-001"
            sop = sop_loader.get(target_sop_id)
            if sop:
                first_step = sop.get_step(1)
                spoken = first_step.instruction_spoken if first_step else f"Đã bắt đầu quy trình {sop.title}."
                return StructuredResponse(
                    spoken_response=f"Đã nhận diện thiết bị của bạn. {spoken}",
                    intent=IntentEnum.DIAGNOSE_WIFI.value,
                    matched_sop_id=sop.sop_id,
                    current_step_id=1,
                    missing_slots=[],
                    is_breakdown_detected=False,
                    breakdown_type=BreakdownTypeEnum.NONE.value,
                    action_summary=f"Đã lưu thiết bị -> Bắt đầu Bước 1: {first_step.action if first_step else ''}"
                )

        # 2. Check for Execution Failure Breakdown
        is_exec_failure = any(
            p in user_lower for p in (
                "báo lệnh không hợp lệ", "gõ sai", "không tìm thấy lệnh", "không ấn được phím tắt",
                "không ra gì", "bị lỗi rồi", "báo lỗi", "không làm được", "is not recognized"
            )
        )
        if is_exec_failure and session.active_sop_id:
            sop = sop_loader.get(session.active_sop_id)
            current_step = sop.get_step(session.current_step_id or 1) if sop else None
            fallback_msg = (
                current_step.fallback_instruction if current_step
                else "Bạn hãy kiểm tra lại câu lệnh hoặc dùng giao diện cài đặt nhé."
            )
            # Custom guidance for ipconfig misspelling
            if "ipconfig" in (current_step.action.lower() if current_step else ""):
                spoken = "Bạn hãy kiểm tra xem có gõ đúng chữ i-p-c-o-n-f-i-g viết liền không dấu nhé."
            else:
                spoken = fallback_msg

            return StructuredResponse(
                spoken_response=spoken,
                intent=IntentEnum.REPORT_ERROR.value,
                matched_sop_id=session.active_sop_id,
                current_step_id=session.current_step_id or 1,
                missing_slots=[],
                is_breakdown_detected=True,
                breakdown_type=BreakdownTypeEnum.EXECUTION_FAILURE.value,
                action_summary=f"Kích hoạt hướng dẫn dự phòng cho Bước {session.current_step_id}"
            )

        # 3. Check for Digression Breakdown (Side question during active troubleshooting)
        is_digression = any(
            p in user_lower for p in (
                "có mất dữ liệu không", "có nguy hiểm không", "mất bao lâu",
                "lệnh này là gì", "tại sao phải làm vậy", "ai tạo ra mạng này"
            )
        )
        if is_digression and session.active_sop_id:
            sop = sop_loader.get(session.active_sop_id)
            step_num = session.current_step_id or 1
            return StructuredResponse(
                spoken_response=f"Lệnh này hoàn toàn an toàn và không làm mất bất kỳ dữ liệu nào của bạn. Chúng ta tiếp tục bước {step_num} nhé.",
                intent=IntentEnum.DIGRESSION.value,
                matched_sop_id=session.active_sop_id,
                current_step_id=step_num,
                missing_slots=[],
                is_breakdown_detected=True,
                breakdown_type=BreakdownTypeEnum.DIGRESSION.value,
                action_summary="Giải đáp câu hỏi bên lề và điều hướng quay lại quy trình"
            )

        # 4. Check for Step Confirmation when active SOP exists
        if session.active_sop_id:
            sop = sop_loader.get(session.active_sop_id)
            if sop:
                curr_step_id = session.current_step_id or 1
                curr_step = sop.get_step(curr_step_id)

                is_confirm = False
                if curr_step:
                    for exp in curr_step.expected_confirmation:
                        if exp.lower() in user_lower:
                            is_confirm = True
                            break

                if not is_confirm:
                    generic_confirmations = [
                        "xong rồi", "đã gõ xong", "hiện ra địa chỉ rồi", "đã thấy ip", "có ip rồi",
                        "có reply", "reply from", "thành công rồi", "đã xong", "rồi nhé", "được rồi",
                        "ok rồi", "đã làm rồi", "đã gõ rồi", "vào được mạng rồi", "vào được rồi",
                        "lướt web được rồi", "mạng bình thường rồi", "được rồi nhé", "ổn rồi",
                        "vào mạng được rồi", "đã vào được mạng", "lướt web bình thường rồi"
                    ]
                    is_confirm = any(c in user_lower for c in generic_confirmations)

                if is_confirm:
                    if curr_step_id >= sop.get_step_count():
                        # Completed all steps in SOP -> RESOLVED
                        return StructuredResponse(
                            spoken_response="Tuyệt vời! Tất cả các bước đã hoàn tất và kết nối mạng của bạn đã hoạt động bình thường trở lại. Chúc bạn làm việc hiệu quả nhé!",
                            intent=IntentEnum.RESOLVE.value,
                            matched_sop_id=sop.sop_id,
                            current_step_id=curr_step_id,
                            missing_slots=[],
                            is_breakdown_detected=False,
                            breakdown_type=BreakdownTypeEnum.NONE.value,
                            action_summary=f"Đã hoàn thành toàn bộ quy trình {sop.sop_id} thành công!"
                        )
                    else:
                        next_step_id = curr_step_id + 1
                        next_step = sop.get_step(next_step_id)
                        return StructuredResponse(
                            spoken_response=next_step.instruction_spoken if next_step else "Tiếp tục bước tiếp theo.",
                            intent=IntentEnum.CONFIRM_STEP.value,
                            matched_sop_id=sop.sop_id,
                            current_step_id=next_step_id,
                            missing_slots=[],
                            is_breakdown_detected=False,
                            breakdown_type=BreakdownTypeEnum.NONE.value,
                            action_summary=f"Xác nhận bước {curr_step_id} thành công -> Chuyển bước {next_step_id}"
                        )

        # 5. Semantic Search & Match from Knowledge Base
        matches = vector_store.search(user_text, top_k=1)
        if matches and matches[0].score >= 0.2:
            matched_sop = matches[0].sop
            first_step = matched_sop.steps[0] if matched_sop.steps else None
            spoken = first_step.instruction_spoken if first_step else f"Đã xác định quy trình {matched_sop.title}."

            return StructuredResponse(
                spoken_response=spoken,
                intent=IntentEnum.DIAGNOSE_WIFI.value,
                matched_sop_id=matched_sop.sop_id,
                current_step_id=1,
                missing_slots=[],
                is_breakdown_detected=False,
                breakdown_type=BreakdownTypeEnum.NONE.value,
                action_summary=f"Khởi động quy trình {matched_sop.sop_id}: {matched_sop.title}"
            )

        # 6. Fallback escalation if unknown
        return StructuredResponse(
            spoken_response="Tôi chưa hiểu rõ sự cố của bạn. Bạn có thể mô tả chi tiết hơn hoặc tôi sẽ chuyển sang nhân viên IT nhé?",
            intent=IntentEnum.ESCALATE.value,
            matched_sop_id=None,
            current_step_id=None,
            missing_slots=[],
            is_breakdown_detected=False,
            breakdown_type=BreakdownTypeEnum.NONE.value,
            action_summary="Chuyển tiếp hỗ trợ kỹ thuật viên IT trực tiếp"
        )


# Global singleton instance
nlu_engine = NLUGroundingEngine()
