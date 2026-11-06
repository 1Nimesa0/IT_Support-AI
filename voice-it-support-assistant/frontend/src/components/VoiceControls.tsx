import React, { useState, useEffect } from 'react';
import { Mic, MicOff, Radio, RotateCcw, Zap, PhoneOff } from 'lucide-react';

interface VoiceControlsProps {
  isRecording: boolean;
  isSpeaking: boolean;
  isBotSpeaking: boolean;
  latencyMs: number | null;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onBargeIn: () => void;
  onResetSession: () => void;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  isRecording,
  isSpeaking,
  isBotSpeaking,
  latencyMs,
  onStartRecording,
  onStopRecording,
  onBargeIn,
  onResetSession,
}) => {
  const [isAutoVAD, setIsAutoVAD] = useState(true);

  // If auto VAD is enabled, start recording mic on mount
  useEffect(() => {
    if (isAutoVAD && !isRecording) {
      onStartRecording();
    }
  }, [isAutoVAD, isRecording, onStartRecording]);

  const toggleRecording = () => {
    if (isRecording) {
      onStopRecording();
      setIsAutoVAD(false);
    } else {
      onStartRecording();
    }
  };

  return (
    <div className="flex flex-col gap-4 p-4 rounded-2xl bg-slate-900/90 border border-slate-800 backdrop-blur-md">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
          <Radio className="w-4 h-4 text-cyan-400 animate-pulse" />
          Điều Khiển Giọng Nói & VAD
        </h3>
        
        {/* Latency Metric Badge */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-xs font-mono">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-slate-400">TTFA:</span>
          <span className={latencyMs && latencyMs <= 1500 ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
            {latencyMs !== null ? `${latencyMs}ms` : '< 1.5s'}
          </span>
        </div>
      </div>

      {/* Main Microphone Button */}
      <div className="flex items-center justify-center py-3">
        <div className="relative flex items-center justify-center">
          {/* Pulsing Ripple rings when active */}
          {isRecording && (
            <div
              className={`absolute w-24 h-24 rounded-full opacity-30 animate-ping ${
                isSpeaking ? 'bg-emerald-500' : isBotSpeaking ? 'bg-purple-500' : 'bg-cyan-500'
              }`}
            />
          )}

          <button
            onClick={toggleRecording}
            className={`relative z-10 w-20 h-20 rounded-full flex flex-col items-center justify-center shadow-lg transition-all duration-300 active:scale-95 ${
              isRecording
                ? isSpeaking
                  ? 'bg-gradient-to-tr from-emerald-600 to-teal-400 text-white shadow-emerald-500/30'
                  : 'bg-gradient-to-tr from-cyan-600 to-sky-400 text-white shadow-cyan-500/30'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700'
            }`}
            title={isRecording ? 'Bấm để tắt micro' : 'Bấm để bật micro'}
          >
            {isRecording ? <Mic className="w-8 h-8" /> : <MicOff className="w-8 h-8" />}
            <span className="text-[10px] font-semibold mt-1">
              {isRecording ? 'Đang Bật' : 'Tắt Mic'}
            </span>
          </button>
        </div>
      </div>

      {/* Control Buttons row */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {/* Barge-in Stop Button */}
        <button
          onClick={onBargeIn}
          disabled={!isBotSpeaking}
          className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl border transition-all ${
            isBotSpeaking
              ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 hover:bg-rose-500/30 cursor-pointer animate-pulse'
              : 'bg-slate-800/50 text-slate-500 border-slate-800 cursor-not-allowed'
          }`}
          title="Ngắt lời phát thanh của bot ngay lập tức"
        >
          <PhoneOff className="w-3.5 h-3.5" />
          <span>Ngắt Lời (Barge-in)</span>
        </button>

        {/* Reset Session Button */}
        <button
          onClick={onResetSession}
          className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700 transition-colors"
          title="Xóa phiên làm việc và bắt đầu lại từ đầu"
        >
          <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
          <span>Làm Mới Phiên</span>
        </button>
      </div>

      {/* VAD Settings Toggle */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-xs text-slate-400">
        <span>Tự động phát hiện giọng nói (VAD):</span>
        <button
          onClick={() => {
            const nextVal = !isAutoVAD;
            setIsAutoVAD(nextVal);
            if (nextVal && !isRecording) onStartRecording();
          }}
          className={`w-10 h-5 flex items-center rounded-full p-1 transition-colors ${
            isAutoVAD ? 'bg-cyan-500 justify-end' : 'bg-slate-700 justify-start'
          }`}
        >
          <div className="w-3.5 h-3.5 rounded-full bg-white shadow-md" />
        </button>
      </div>
    </div>
  );
};
