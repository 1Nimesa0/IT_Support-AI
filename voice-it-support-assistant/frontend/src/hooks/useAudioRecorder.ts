import { useState, useRef, useCallback } from 'react';

interface UseAudioRecorderOptions {
  onSpeechStart?: () => void;
  onSpeechEnd?: (audioBlob: Blob) => void;
  vadThreshold?: number; // RMS threshold for voice detection (default ~0.025)
  silenceTimeoutMs?: number; // Silence duration before trigger (default 900ms)
}

export function useAudioRecorder({
  onSpeechStart,
  onSpeechEnd,
  vadThreshold = 0.025,
  silenceTimeoutMs = 900,
}: UseAudioRecorderOptions = {}) {
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [micVolume, setMicVolume] = useState(0);

  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);

  const audioChunksRef = useRef<Float32Array[]>([]);
  const silenceTimerRef = useRef<number | null>(null);
  const speakingStateRef = useRef(false);
  const isRecordingRef = useRef(false);

  const encodeWAV = (samples: Float32Array, sampleRate: number): Blob => {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    const writeString = (offset: number, str: string) => {
      for (let i = 0; i < str.length; i++) {
        view.setUint8(offset + i, str.charCodeAt(i));
      }
    };

    // RIFF identifier
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(8, 'WAVE');
    // fmt sub-chunk
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM format
    view.setUint16(22, 1, true); // mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true); // block align
    view.setUint16(34, 16, true); // 16-bit
    // data sub-chunk
    writeString(36, 'data');
    view.setUint32(40, samples.length * 2, true);

    // Write PCM samples
    let offset = 44;
    for (let i = 0; i < samples.length; i++, offset += 2) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }

    return new Blob([buffer], { type: 'audio/wav' });
  };

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      mediaStreamRef.current = stream;
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 16000,
      });
      audioContextRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 512;
      analyserRef.current = analyser;

      // Script processor for 16kHz PCM audio collection and real-time VAD
      const processor = audioCtx.createScriptProcessor(2048, 1, 1);
      processorRef.current = processor;
      audioChunksRef.current = [];

      source.connect(analyser);
      analyser.connect(processor);
      processor.connect(audioCtx.destination);

      isRecordingRef.current = true;
      setIsRecording(true);

      processor.onaudioprocess = (e) => {
        if (!isRecordingRef.current) return;

        const inputData = e.inputBuffer.getChannelData(0);
        // Clone and store chunk
        audioChunksRef.current.push(new Float32Array(inputData));

        // Compute RMS energy for VAD
        let sum = 0;
        for (let i = 0; i < inputData.length; i++) {
          sum += inputData[i] * inputData[i];
        }
        const rms = Math.sqrt(sum / inputData.length);
        setMicVolume(Math.min(1, rms * 8));

        // VAD Speech Detection
        if (rms > vadThreshold) {
          if (!speakingStateRef.current) {
            speakingStateRef.current = true;
            setIsSpeaking(true);
            onSpeechStart?.();
          }

          // Clear any pending silence timer
          if (silenceTimerRef.current) {
            window.clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
        } else if (speakingStateRef.current) {
          // Detected silence while in speaking state
          if (!silenceTimerRef.current) {
            silenceTimerRef.current = window.setTimeout(() => {
              speakingStateRef.current = false;
              setIsSpeaking(false);
              silenceTimerRef.current = null;

              // Consolidate samples into WAV blob
              const totalLength = audioChunksRef.current.reduce((acc, c) => acc + c.length, 0);
              if (totalLength > 16000 * 0.4) { // Only send if at least 400ms of audio
                const fullSamples = new Float32Array(totalLength);
                let offset = 0;
                for (const chunk of audioChunksRef.current) {
                  fullSamples.set(chunk, offset);
                  offset += chunk.length;
                }
                const wavBlob = encodeWAV(fullSamples, 16000);
                onSpeechEnd?.(wavBlob);
              }
              audioChunksRef.current = [];
            }, silenceTimeoutMs);
          }
        }
      };
    } catch (err) {
      console.error('Failed to access microphone:', err);
    }
  }, [onSpeechStart, onSpeechEnd, vadThreshold, silenceTimeoutMs]);

  const stopRecording = useCallback(() => {
    isRecordingRef.current = false;
    speakingStateRef.current = false;
    setIsRecording(false);
    setIsSpeaking(false);
    setMicVolume(0);

    if (silenceTimerRef.current) {
      window.clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }

    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }

    if (analyserRef.current) {
      analyserRef.current.disconnect();
      analyserRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }
  }, []);

  return {
    isRecording,
    isSpeaking,
    micVolume,
    analyser: analyserRef.current,
    startRecording,
    stopRecording,
  };
}
