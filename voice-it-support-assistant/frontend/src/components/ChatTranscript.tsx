import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, AlertTriangle, HelpCircle, CheckCircle2 } from 'lucide-react';
import { ChatMessage } from '../types/dialogue';

interface ChatTranscriptProps {
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  isBotSpeaking: boolean;
}

export const ChatTranscript: React.FC<ChatTranscriptProps> = ({
  messages,
  onSendMessage,
  isBotSpeaking,
}) => {
  const [inputText, setInputText] = useState('');
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isBotSpeaking]);

  const handleSend = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (inputText.trim()) {
      onSendMessage(inputText.trim());
      setInputText('');
    }
  };

  // Highlights IT keywords in transcript text
  const renderHighlightedText = (text: string) => {
    const itKeywords = [
      'ipconfig',
      'ping 8.8.8.8',
      '8.8.8.8',
      '1.1.1.1',
      'cmd',
      'DHCP',
      'VPN',
      'DNS',
      'SSID',
      'MFA',
      'OTP',
      'Active Directory',
      '/flushdns',
      '/renew',
      '/release',
      'neverssl.com',
      'Win + R',
      'Windows',
      'macOS',
    ];

    const escapedKeywords = itKeywords.map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    const regex = new RegExp(`(${escapedKeywords.join('|')})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) => {
      const match = itKeywords.find((k) => k.toLowerCase() === part.toLowerCase());
      if (match) {
        return (
          <span
            key={index}
            className="inline-block px-1.5 py-0.5 mx-0.5 rounded bg-cyan-950/70 border border-cyan-500/30 text-cyan-300 font-mono text-xs font-semibold"
          >
            {part}
          </span>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  // Quick test prompt chips
  const quickPrompts = [
    'Mạng cơ quan tôi không vào được',
    'Tôi dùng máy tính Windows',
    'Tôi đã thấy IP rồi',
    'Nó báo lệnh không hợp lệ hoặc tôi gõ sai',
    'Lệnh này có làm mất dữ liệu không?',
  ];

  return (
    <div className="flex flex-col h-full rounded-2xl bg-slate-900/90 border border-slate-800 backdrop-blur-md overflow-hidden">
      {/* Transcript Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-cyan-400" />
          <h2 className="text-sm font-semibold text-slate-200">
            Hội Thoại Trực Tiếp (Turn-by-Turn Transcript)
          </h2>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          {messages.length} lượt thoại
        </span>
      </div>

      {/* Message List */}
      <div ref={scrollRef} className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500">
            <Bot className="w-12 h-12 mb-3 text-slate-700 animate-pulse" />
            <p className="text-sm font-medium">Chưa có nội dung trao đổi.</p>
            <p className="text-xs mt-1 text-slate-600">
              Hãy bấm bật Micro và nói sự cố của bạn hoặc gõ vào ô nhập liệu bên dưới.
            </p>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.speaker === 'user';
            const isFailure = msg.breakdown_type === 'execution_failure';
            const isDigression = msg.breakdown_type === 'digression';

            return (
              <div
                key={msg.id}
                className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-full bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4 text-cyan-400" />
                  </div>
                )}

                <div
                  className={`max-w-[82%] rounded-2xl p-3.5 text-sm leading-relaxed shadow-md ${
                    isUser
                      ? 'bg-gradient-to-r from-cyan-600 to-sky-600 text-white rounded-tr-none'
                      : 'bg-slate-800/90 text-slate-200 border border-slate-700/80 rounded-tl-none'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3 mb-1 text-[11px] opacity-75">
                    <span className="font-semibold">
                      {isUser ? 'Người Dùng' : 'Trợ Lý Kỹ Thuật IT'}
                    </span>
                    {msg.confidence && (
                      <span className="font-mono">
                        {(msg.confidence * 100).toFixed(0)}% tin cậy
                      </span>
                    )}
                  </div>

                  {/* Message body with highlighted IT keywords */}
                  <div className="text-[13.5px]">
                    {renderHighlightedText(msg.text)}
                  </div>

                  {/* Breakdown Indicator Badges */}
                  {isFailure && (
                    <div className="mt-2.5 p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
                      <span>Phát hiện người dùng gõ sai lệnh. Kích hoạt hướng dẫn dự phòng!</span>
                    </div>
                  )}

                  {isDigression && (
                    <div className="mt-2.5 p-2 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300 text-xs flex items-center gap-2">
                      <HelpCircle className="w-4 h-4 shrink-0 text-blue-400" />
                      <span>Đã giải đáp câu hỏi phụ và giữ nguyên trạng thái bước trước đó.</span>
                    </div>
                  )}

                  {/* Action Summary Pill */}
                  {msg.structured?.action_summary && (
                    <div className="mt-2 text-[11px] text-slate-400 italic flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                      <span>{msg.structured.action_summary}</span>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0">
                    <User className="w-4 h-4 text-slate-400" />
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Quick Prompts Chips */}
      <div className="px-4 py-2 border-t border-slate-800/80 bg-slate-900/60 flex items-center gap-1.5 overflow-x-auto text-[11px]">
        <span className="text-slate-500 shrink-0 font-medium">Gợi ý mẫu:</span>
        {quickPrompts.map((prompt, i) => (
          <button
            key={i}
            onClick={() => onSendMessage(prompt)}
            className="px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 whitespace-nowrap border border-slate-700/60 transition-colors"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input Form Fallback */}
      <form
        onSubmit={handleSend}
        className="p-3 border-t border-slate-800 bg-slate-950 flex items-center gap-2"
      >
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Nhập phản hồi hoặc kết quả lệnh (ví dụ: 'Đã thấy IP rồi')..."
          className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-500 transition-colors"
        />
        <button
          type="submit"
          disabled={!inputText.trim()}
          className="px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-800 text-white disabled:text-slate-600 text-sm font-medium flex items-center gap-1.5 transition-colors shadow-md"
        >
          <Send className="w-4 h-4" />
          <span>Gửi</span>
        </button>
      </form>
    </div>
  );
};
