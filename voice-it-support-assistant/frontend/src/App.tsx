import React, { useMemo } from 'react';
import { Headphones, Activity, Laptop } from 'lucide-react';
import { useDialogueSocket } from './hooks/useDialogueSocket';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { AudioVisualizer } from './components/AudioVisualizer';
import { VoiceControls } from './components/VoiceControls';
import { ChatTranscript } from './components/ChatTranscript';
import { DiagnosticStepper } from './components/DiagnosticStepper';

export const App: React.FC = () => {
  // Generate or maintain persistent session ID
  const sessionId = useMemo(() => {
    let saved = sessionStorage.getItem('it_session_id');
    if (!saved) {
      saved = `session-${Math.random().toString(36).substring(2, 9)}`;
      sessionStorage.setItem('it_session_id', saved);
    }
    return saved;
  }, []);

  const {
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
  } = useDialogueSocket({ sessionId });

  // Voice activity recorder hook
  const {
    isRecording,
    isSpeaking,
    analyser,
    startRecording,
    stopRecording,
  } = useAudioRecorder({
    onSpeechStart: () => {
      // BARGE-IN: If bot is currently speaking and user starts talking, halt bot immediately!
      if (isBotSpeaking) {
        console.log('User speech detected during bot speech! Emitting Barge-in.');
        triggerBargeIn();
      }
    },
    onSpeechEnd: (audioBlob: Blob) => {
      console.log('VAD detected speech end, sending audio chunk...');
      sendSpeech(audioBlob);
    },
    vadThreshold: 0.025,
    silenceTimeoutMs: 850,
  });

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Top Application Header */}
      <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-teal-400 flex items-center justify-center shadow-md shadow-cyan-500/20">
            <Headphones className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-slate-100 tracking-tight">
                Trợ Lý Ảo Hỗ Trợ IT Bằng Giọng Nói
              </h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 uppercase tracking-wider">
                Grounded Dialogue
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Voice-Based IT Support Assistant & Zero-Hallucination SOP Grounding
            </p>
          </div>
        </div>

        {/* Status Indicators in Header */}
        <div className="flex items-center gap-4 text-xs font-medium">
          {/* Active Device Slot */}
          {slots.device_type && (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
              <Laptop className="w-3.5 h-3.5 text-cyan-400" />
              <span>Thiết bị: <strong className="text-cyan-300">{slots.device_type}</strong></span>
            </div>
          )}

          {/* Connection Status Indicator */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700">
            <span
              className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
              }`}
            />
            <span className={isConnected ? 'text-emerald-400' : 'text-rose-400'}>
              {isConnected ? 'Máy Chủ Trực Tuyến' : 'Mất Kết Nối'}
            </span>
          </div>
        </div>
      </header>

      {/* Main 3-Column Workspace */}
      <main className="flex-1 p-5 grid grid-cols-12 gap-5 overflow-hidden">
        {/* Column 1: Voice Controller & Visualizer (3 cols) */}
        <div className="col-span-3 flex flex-col gap-4 overflow-y-auto">
          {/* Live Mic Audio Visualizer */}
          <AudioVisualizer
            analyser={analyser}
            isRecording={isRecording}
            isSpeaking={isSpeaking}
            isBotSpeaking={isBotSpeaking}
          />

          {/* Voice Controls (PTT, VAD Toggle, Barge-in) */}
          <VoiceControls
            isRecording={isRecording}
            isSpeaking={isSpeaking}
            isBotSpeaking={isBotSpeaking}
            latencyMs={latencyMs}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
            onBargeIn={triggerBargeIn}
            onResetSession={resetSession}
          />

          {/* Session Metadata / Slots Card */}
          <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 text-xs space-y-2.5">
            <h4 className="font-semibold text-slate-300 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              Thông Số Phiên Làm Việc (Telemetry)
            </h4>
            <div className="space-y-1.5 font-mono text-[11px] text-slate-400">
              <div className="flex justify-between">
                <span>Session ID:</span>
                <span className="text-slate-200">{sessionId}</span>
              </div>
              <div className="flex justify-between">
                <span>Trạng thái FSM:</span>
                <span className="text-cyan-400 font-bold">{fsmState}</span>
              </div>
              <div className="flex justify-between">
                <span>Active SOP:</span>
                <span className="text-amber-400">{activeSopId || 'Chưa liên kết'}</span>
              </div>
              <div className="flex justify-between">
                <span>Bước hiện tại:</span>
                <span className="text-emerald-400">
                  {currentStepId ? `Bước ${currentStepId}` : '---'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Đã lưu Slots:</span>
                <span className="text-slate-200">
                  {Object.keys(slots).length > 0 ? JSON.stringify(slots) : '{}'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Column 2: Turn-by-Turn Chat Transcript (5 cols) */}
        <div className="col-span-5 flex flex-col h-full overflow-hidden">
          <ChatTranscript
            messages={messages}
            onSendMessage={sendText}
            isBotSpeaking={isBotSpeaking}
          />
        </div>

        {/* Column 3: Diagnostic SOP Stepper (4 cols) */}
        <div className="col-span-4 flex flex-col h-full overflow-hidden">
          <DiagnosticStepper
            activeSopId={activeSopId}
            currentStepId={currentStepId}
            completedSteps={completedSteps}
            fsmState={fsmState}
            missingSlots={[]}
          />
        </div>
      </main>
    </div>
  );
};

export default App;
