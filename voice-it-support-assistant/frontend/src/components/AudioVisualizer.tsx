import React, { useEffect, useRef } from 'react';

interface AudioVisualizerProps {
  analyser: AnalyserNode | null;
  isRecording: boolean;
  isSpeaking: boolean;
  isBotSpeaking: boolean;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
  analyser,
  isRecording,
  isSpeaking,
  isBotSpeaking,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    const dataArray = analyser ? new Uint8Array(analyser.frequencyBinCount) : new Uint8Array(64);

    const render = () => {
      animationFrameId = requestAnimationFrame(render);

      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      if (analyser && isRecording) {
        analyser.getByteFrequencyData(dataArray);
      } else {
        // Subtle resting wave animation
        for (let i = 0; i < dataArray.length; i++) {
          dataArray[i] = Math.sin(Date.now() / 200 + i * 0.2) * 8 + 12;
        }
      }

      // Choose theme color based on status
      let barColor = 'rgba(56, 189, 248, 0.7)'; // Cyan (Listening)
      if (isSpeaking && isBotSpeaking) {
        barColor = 'rgba(239, 68, 68, 0.9)'; // Red (Barge-in happening)
      } else if (isSpeaking) {
        barColor = 'rgba(34, 197, 94, 0.9)'; // Green (User speaking)
      } else if (isBotSpeaking) {
        barColor = 'rgba(168, 85, 247, 0.8)'; // Purple (Bot speaking)
      }

      const numBars = 32;
      const barWidth = (width / numBars) * 0.7;
      const spacing = (width / numBars) * 0.3;

      for (let i = 0; i < numBars; i++) {
        const val = dataArray[i * 2] || 0;
        const barHeight = Math.max(4, (val / 255) * height * 0.9);
        const x = i * (barWidth + spacing) + spacing / 2;
        const y = (height - barHeight) / 2;

        ctx.fillStyle = barColor;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, 4);
        ctx.fill();
      }
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [analyser, isRecording, isSpeaking, isBotSpeaking]);

  return (
    <div className="w-full flex flex-col items-center justify-center p-3 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-inner">
      <canvas
        ref={canvasRef}
        width={320}
        height={60}
        className="w-full max-w-[340px] h-14"
      />
      <div className="flex items-center gap-2 mt-2 text-xs font-medium">
        {isSpeaking && isBotSpeaking ? (
          <span className="flex items-center gap-1.5 text-rose-400 font-semibold animate-pulse">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            Barge-in: Đang ngắt lời trợ lý
          </span>
        ) : isSpeaking ? (
          <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Đang ghi âm giọng nói người dùng
          </span>
        ) : isBotSpeaking ? (
          <span className="flex items-center gap-1.5 text-purple-400 font-semibold">
            <span className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
            Trợ lý đang phát âm thanh hướng dẫn
          </span>
        ) : isRecording ? (
          <span className="flex items-center gap-1.5 text-cyan-400/80">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            VAD đang lắng nghe micro...
          </span>
        ) : (
          <span className="text-slate-500">Micro đang tắt (Sẵn sàng)</span>
        )}
      </div>
    </div>
  );
};
