export type DialogueState =
  | 'IDLE'
  | 'LISTENING'
  | 'SLOT_FILLING'
  | 'GROUNDED_EXECUTING'
  | 'CONFIRMING_STEP'
  | 'BREAKDOWN_RECOVERY'
  | 'RESOLVED'
  | 'ESCALATED';

export type Intent =
  | 'diagnose_wifi'
  | 'reset_password'
  | 'mfa_issue'
  | 'vpn_failure'
  | 'clarify_missing_info'
  | 'escalate'
  | 'confirm_step'
  | 'report_error'
  | 'digression'
  | 'resolve'
  | 'unknown';

export type BreakdownType = 'none' | 'misrecognition' | 'execution_failure' | 'digression';

export interface StructuredResponse {
  spoken_response: string;
  intent: Intent | string;
  matched_sop_id?: string | null;
  current_step_id?: number | null;
  missing_slots: string[];
  is_breakdown_detected: boolean;
  breakdown_type: BreakdownType | string;
  action_summary: string;
}

export interface SOPStep {
  step_id: number;
  action: string;
  instruction_spoken: string;
  expected_confirmation: string[];
  fallback_instruction: string;
  shortcut?: string | null;
}

export interface SOPDocument {
  sop_id: string;
  title: string;
  category: string;
  symptoms: string[];
  prerequisites: Record<string, any>;
  steps: SOPStep[];
  body_text?: string;
}

export interface ChatMessage {
  id: string;
  speaker: 'user' | 'assistant' | 'system';
  text: string;
  timestamp: number;
  structured?: StructuredResponse;
  sop_id?: string;
  step_id?: number;
  confidence?: number;
  breakdown_type?: string;
}

export interface WebSocketMessage {
  type:
    | 'connected'
    | 'transcription'
    | 'nlu_start'
    | 'spoken_response_early'
    | 'tts_chunk'
    | 'tts_end'
    | 'dialogue_update'
    | 'barge_in_confirmed'
    | 'session_reset'
    | 'error';
  session_id?: string;
  fsm_state?: DialogueState;
  raw_text?: string;
  normalized_text?: string;
  confidence?: number;
  spoken_text?: string;
  audio_base64?: string;
  chunk_index?: number;
  structured?: StructuredResponse;
  slots?: Record<string, any>;
  active_sop_id?: string | null;
  current_step_id?: number | null;
  completed_steps?: number[];
  query?: string;
  status?: string;
}
