"""
Pydantic Schemas for Dialogue State, NLU Grounding, and Structured Output.
"""

from __future__ import annotations
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DialogueStateEnum(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    SLOT_FILLING = "SLOT_FILLING"
    GROUNDED_EXECUTING = "GROUNDED_EXECUTING"
    CONFIRMING_STEP = "CONFIRMING_STEP"
    BREAKDOWN_RECOVERY = "BREAKDOWN_RECOVERY"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"


class IntentEnum(str, Enum):
    DIAGNOSE_WIFI = "diagnose_wifi"
    RESET_PASSWORD = "reset_password"
    MFA_ISSUE = "mfa_issue"
    VPN_FAILURE = "vpn_failure"
    CLARIFY_MISSING_INFO = "clarify_missing_info"
    ESCALATE = "escalate"
    CONFIRM_STEP = "confirm_step"
    REPORT_ERROR = "report_error"
    DIGRESSION = "digression"
    RESOLVE = "resolve"
    UNKNOWN = "unknown"


class BreakdownTypeEnum(str, Enum):
    NONE = "none"
    MISRECOGNITION = "misrecognition"
    EXECUTION_FAILURE = "execution_failure"
    DIGRESSION = "digression"


class StructuredResponse(BaseModel):
    """
    CRITICAL: spoken_response is the first key to enable real-time streaming JSON parsing
    and initiate TTS streaming before the remainder of the JSON finishes generating.
    """
    spoken_response: str = Field(
        ...,
        description="Natural, concise conversational Vietnamese speech (1-2 sentences) to be sent directly to TTS"
    )
    intent: str = Field(
        default=IntentEnum.UNKNOWN.value,
        description="Classified user dialogue intent"
    )
    matched_sop_id: Optional[str] = Field(
        default=None,
        description="Locked SOP ID from knowledge base (e.g. SOP-WIFI-001) or null"
    )
    current_step_id: Optional[int] = Field(
        default=None,
        description="Active 1-based step index in the matched SOP"
    )
    missing_slots: List[str] = Field(
        default_factory=list,
        description="List of mandatory slots that require proactive clarification (e.g. ['device_type'])"
    )
    is_breakdown_detected: bool = Field(
        default=False,
        description="Whether a conversation breakdown occurred (phonetic error, execution failure, digression)"
    )
    breakdown_type: str = Field(
        default=BreakdownTypeEnum.NONE.value,
        description="Classification of breakdown: none | misrecognition | execution_failure | digression"
    )
    action_summary: str = Field(
        default="",
        description="Summary of action to render on frontend stepper and telemetry cards"
    )


class DialogueTurn(BaseModel):
    speaker: str = Field(..., description="user or assistant")
    text: str = Field(..., description="Raw or spoken transcript text")
    timestamp: float = Field(..., description="Epoch timestamp of message")
    structured: Optional[StructuredResponse] = None
    sop_id: Optional[str] = None
    step_id: Optional[int] = None
    breakdown_type: Optional[str] = None


class ContextStackItem(BaseModel):
    sop_id: str
    step_id: int
    slots: Dict[str, Any] = Field(default_factory=dict)
    prompt_context: str = ""


class SessionState(BaseModel):
    session_id: str
    fsm_state: DialogueStateEnum = DialogueStateEnum.IDLE
    slots: Dict[str, Any] = Field(default_factory=dict)
    active_sop_id: Optional[str] = None
    current_step_id: Optional[int] = None
    completed_steps: List[int] = Field(default_factory=list)
    state_stack: List[ContextStackItem] = Field(default_factory=list)
    turn_history: List[DialogueTurn] = Field(default_factory=list)
    last_user_input: str = ""
    is_speaking: bool = False
    is_interrupted: bool = False


class DialogueTurnRequest(BaseModel):
    session_id: str
    user_text: str
    device_type: Optional[str] = None
    client_timestamp: Optional[float] = None


class DialogueTurnResponse(BaseModel):
    session_id: str
    fsm_state: DialogueStateEnum
    structured: StructuredResponse
    slots: Dict[str, Any]
    active_sop_id: Optional[str]
    current_step_id: Optional[int]
    completed_steps: List[int]
    audio_base64: Optional[str] = None
