import { useState, useEffect, useRef, useCallback } from 'react';
import {
  DialogueState,
  StructuredResponse,
  WebSocketMessage,
  ChatMessage,
} from '../types/dialogue';

interface UseDialogueSocketProps {
  sessionId: string;
}

export function useDialogueSocket({ sessionId }: UseDialogueSocketProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [fsmState, setFsmState] = useState<DialogueState>('IDLE');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeSopId, setActiveSopId] = useState<string | null>(null);
  const [currentStepId, setCurrentStepId] = useState<number | null>(null);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [slots, setSlots] = useState<Record<string, any>>({});
  const [isBotSpeaking, setIsBotSpeaking] = useState(false);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const currentSourceNodeRef = useRef<AudioBufferSourceNode | null>(null);
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const isPlayingAudioRef = useRef(false);
  const turnStartTimeRef = useRef<number | null>(null);

  // Initialize playback AudioContext on first user interaction
  const getAudioContext = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    if (audioContextRef.current.state === 'suspended') {
      audioContextRef.current.resume();
    }
    return audioContextRef.current;
  }, []);

  // Stop currently playing bot speech instantly
  const stopAudioPlayback = useCallback(() => {
    if (currentSourceNodeRef.current) {
      try {
        currentSourceNodeRef.current.stop();
        currentSourceNodeRef.current.disconnect();
      } catch (e) {
        // Source node might already be stopped
      }
      currentSourceNodeRef.current = null;
    }
    audioQueueRef.current = [];
    isPlayingAudioRef.current = false;
    setIsBotSpeaking(false);
  }, []);

  // Play next chunk from audio queue
  const playNextChunk = useCallback(async () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingAudioRef.current = false;
      setIsBotSpeaking(false);
      return;
    }

    isPlayingAudioRef.current = true;
    setIsBotSpeaking(true);

    const chunkData = audioQueueRef.current.shift()!;
    const audioCtx = getAudioContext();

    try {
      // Decode MP3/WAV chunk
      const audioBuffer = await audioCtx.decodeAudioData(chunkData.slice(0));
      const source = audioCtx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioCtx.destination);
      currentSourceNodeRef.current = source;

      source.onended = () => {
        currentSourceNodeRef.current = null;
        playNextChunk();
      };

      source.start(0);
    } catch (err) {
      console.warn('Audio decoding chunk error (skipping chunk):', err);
      playNextChunk();
    }
  }, [getAudioContext]);

  // Connect WebSocket with auto-reconnect
  useEffect(() => {
    let isMounted = true;
    let reconnectTimer: number | null = null;

    const connect = () => {
      if (!isMounted) return;

      // In dev mode (Vite on port 5173), connect directly to backend port 8000 for maximum reliability
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname || '127.0.0.1';
      const wsUrl = window.location.port === '5173'
        ? `ws://${host}:8000/api/v1/dialogue/ws/${sessionId}`
        : `${protocol}//${window.location.host}/api/v1/dialogue/ws/${sessionId}`;

      try {
        const ws = new WebSocket(wsUrl);
        socketRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) return;
          setIsConnected(true);
          console.log('Dialogue WebSocket successfully connected to:', wsUrl);
        };

        ws.onclose = () => {
          if (!isMounted) return;
          setIsConnected(false);
          console.log('Dialogue WebSocket disconnected. Retrying in 2.5s...');
          reconnectTimer = window.setTimeout(connect, 2500);
        };

        ws.onerror = (error) => {
          console.warn('Dialogue WebSocket error:', error);
          ws.close();
        };

        ws.onmessage = async (event) => {
          try {
            const data: WebSocketMessage = JSON.parse(event.data);

            switch (data.type) {
              case 'connected':
                if (data.fsm_state) setFsmState(data.fsm_state);
                if (data.slots) setSlots(data.slots);
                break;

              case 'transcription':
                // Add user turn to messages list
                if (data.normalized_text) {
                  setMessages((prev) => [
                    ...prev,
                    {
                      id: `user-${Date.now()}`,
                      speaker: 'user',
                      text: data.normalized_text!,
                      confidence: data.confidence,
                      timestamp: Date.now(),
                    },
                  ]);
                }
                break;

              case 'spoken_response_early':
                // Compute Time-to-First-Audio / Spoken response latency
                if (turnStartTimeRef.current) {
                  const elapsed = Math.round(performance.now() - turnStartTimeRef.current);
                  setLatencyMs(elapsed);
                }
                break;

              case 'tts_chunk':
                if (data.audio_base64) {
                  const binary = atob(data.audio_base64);
                  const bytes = new Uint8Array(binary.length);
                  for (let i = 0; i < binary.length; i++) {
                    bytes[i] = binary.charCodeAt(i);
                  }
                  audioQueueRef.current.push(bytes.buffer);

                  if (!isPlayingAudioRef.current) {
                    playNextChunk();
                  }
                }
                break;

              case 'dialogue_update':
                if (data.fsm_state) setFsmState(data.fsm_state);
                if (data.active_sop_id !== undefined) setActiveSopId(data.active_sop_id);
                if (data.current_step_id !== undefined) setCurrentStepId(data.current_step_id);
                if (data.completed_steps) setCompletedSteps(data.completed_steps);
                if (data.slots) setSlots(data.slots);

                if (data.structured) {
                  const structured = data.structured as StructuredResponse;
                  setMessages((prev) => [
                    ...prev,
                    {
                      id: `bot-${Date.now()}`,
                      speaker: 'assistant',
                      text: structured.spoken_response,
                      timestamp: Date.now(),
                      structured,
                      sop_id: data.active_sop_id || undefined,
                      step_id: data.current_step_id || undefined,
                      breakdown_type: structured.breakdown_type,
                    },
                  ]);
                }
                break;

              case 'barge_in_confirmed':
                stopAudioPlayback();
                setFsmState('LISTENING');
                break;

              case 'session_reset':
                stopAudioPlayback();
                setFsmState('IDLE');
                setActiveSopId(null);
                setCurrentStepId(null);
                setCompletedSteps([]);
                setSlots({});
                setMessages([]);
                setLatencyMs(null);
                break;
            }
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };
      } catch (err) {
        console.error('WebSocket initialization error:', err);
        reconnectTimer = window.setTimeout(connect, 2500);
      }
    };

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      stopAudioPlayback();
      if (socketRef.current) socketRef.current.close();
    };
  }, [sessionId, playNextChunk, stopAudioPlayback]);

  // Send User Text message
  const sendText = useCallback((text: string) => {
    if (!text.trim() || !socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      return;
    }
    turnStartTimeRef.current = performance.now();
    // Add optimistic user message to transcript
    setMessages((prev) => [
      ...prev,
      {
        id: `user-${Date.now()}`,
        speaker: 'user',
        text: text.trim(),
        timestamp: Date.now(),
      },
    ]);

    socketRef.current.send(
      JSON.stringify({
        type: 'user_text',
        text: text.trim(),
      })
    );
  }, []);

  // Send User Speech audio blob
  const sendSpeech = useCallback(async (blob: Blob) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      return;
    }
    turnStartTimeRef.current = performance.now();

    const reader = new FileReader();
    reader.onloadend = () => {
      const base64Data = (reader.result as string).split(',')[1];
      socketRef.current?.send(
        JSON.stringify({
          type: 'user_speech',
          audio_base64: base64Data,
        })
      );
    };
    reader.readAsDataURL(blob);
  }, []);

  // Trigger Barge-In when user speaks during bot speech
  const triggerBargeIn = useCallback(() => {
    stopAudioPlayback();
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'barge_in' }));
    }
  }, [stopAudioPlayback]);

  // Reset Session
  const resetSession = useCallback(() => {
    stopAudioPlayback();
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'reset' }));
    }
  }, [stopAudioPlayback]);

  return {
    isConnected,
    fsmState,
    messages,
    activeSopId,
    currentStepId,
    completedSteps,
    slots,
    isBotSpeaking,
    latencyMs,
    sendText,
    sendSpeech,
    triggerBargeIn,
    resetSession,
    stopAudioPlayback,
  };
}
