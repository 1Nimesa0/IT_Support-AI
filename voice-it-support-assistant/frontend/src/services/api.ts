import { SOPDocument, StructuredResponse, DialogueState } from '../types/dialogue';

const API_BASE = '/api/v1';

export async function fetchAllSOPs(): Promise<SOPDocument[]> {
  const res = await fetch(`${API_BASE}/sops/`);
  if (!res.ok) throw new Error(`Failed to fetch SOPs: ${res.statusText}`);
  return res.json();
}

export async function fetchSOPById(sopId: string): Promise<SOPDocument> {
  const res = await fetch(`${API_BASE}/sops/${sopId}`);
  if (!res.ok) throw new Error(`Failed to fetch SOP ${sopId}: ${res.statusText}`);
  return res.json();
}

export async function searchSOPs(query: string): Promise<any[]> {
  const res = await fetch(`${API_BASE}/sops/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: 3 }),
  });
  if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
  return res.json();
}

export async function sendDialogueTurn(
  sessionId: string,
  userText: string,
  deviceType?: string
): Promise<{
  session_id: string;
  fsm_state: DialogueState;
  structured: StructuredResponse;
  slots: Record<string, any>;
  active_sop_id?: string;
  current_step_id?: number;
  completed_steps: number[];
}> {
  const res = await fetch(`${API_BASE}/dialogue/turn`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      user_text: userText,
      device_type: deviceType,
    }),
  });
  if (!res.ok) throw new Error(`Dialogue turn failed: ${res.statusText}`);
  return res.json();
}

export async function uploadAudioTranscribe(
  audioBlob: Blob
): Promise<{ raw_text: string; normalized_text: string; confidence: number }> {
  const formData = new FormData();
  formData.append('file', audioBlob, 'mic_recording.wav');

  const res = await fetch(`${API_BASE}/audio/transcribe`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`Audio upload failed: ${res.statusText}`);
  return res.json();
}

export async function checkBackendHealth(): Promise<{ status: string; vector_store_indexed: boolean }> {
  const res = await fetch('/health');
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}
