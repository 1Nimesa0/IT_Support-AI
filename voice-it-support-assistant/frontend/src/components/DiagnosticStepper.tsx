import React, { useEffect, useState } from 'react';
import {
  CheckCircle2,
  HelpCircle,
  Terminal,
  Layers,
  Sparkles,
} from 'lucide-react';
import { SOPDocument } from '../types/dialogue';
import { fetchAllSOPs, fetchSOPById } from '../services/api';

interface DiagnosticStepperProps {
  activeSopId: string | null;
  currentStepId: number | null;
  completedSteps: number[];
  fsmState: string;
  missingSlots?: string[];
}

export const DiagnosticStepper: React.FC<DiagnosticStepperProps> = ({
  activeSopId,
  currentStepId,
  completedSteps,
  fsmState,
}) => {
  const [activeSop, setActiveSop] = useState<SOPDocument | null>(null);
  const [allSops, setAllSops] = useState<SOPDocument[]>([]);

  // Load all SOPs for quick reference
  useEffect(() => {
    fetchAllSOPs()
      .then((data) => setAllSops(data))
      .catch((err) => console.error('Failed to load SOPs catalog:', err));
  }, []);

  // Fetch active SOP whenever activeSopId changes
  useEffect(() => {
    if (activeSopId) {
      fetchSOPById(activeSopId)
        .then((doc) => setActiveSop(doc))
        .catch((err) => console.error(`Error loading SOP ${activeSopId}:`, err));
    } else {
      setActiveSop(null);
    }
  }, [activeSopId]);

  return (
    <div className="flex flex-col h-full rounded-2xl bg-slate-900/90 border border-slate-800 backdrop-blur-md overflow-hidden">
      {/* Stepper Header */}
      <div className="px-5 py-3.5 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-cyan-400" />
          <h2 className="text-sm font-semibold text-slate-200">
            Tiến Trình Chẩn Đoán Kỹ Thuật (SOP Stepper)
          </h2>
        </div>

        {/* FSM Status Pill */}
        <span
          className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border ${
            fsmState === 'RESOLVED'
              ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
              : fsmState === 'BREAKDOWN_RECOVERY'
              ? 'bg-amber-500/20 text-amber-400 border-amber-500/30 animate-pulse'
              : fsmState === 'SLOT_FILLING'
              ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
              : fsmState === 'GROUNDED_EXECUTING'
              ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'
              : 'bg-slate-800 text-slate-400 border-slate-700'
          }`}
        >
          {fsmState}
        </span>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-5 overflow-y-auto space-y-6">
        {activeSop ? (
          <div>
            {/* Active SOP Title Card */}
            <div className="p-4 rounded-xl bg-slate-800/80 border border-slate-700/80 shadow-sm mb-6">
              <div className="flex items-center justify-between mb-1.5">
                <span className="px-2 py-0.5 rounded bg-cyan-900/60 border border-cyan-500/30 text-cyan-300 font-mono text-xs font-bold">
                  {activeSop.sop_id}
                </span>
                <span className="text-xs text-slate-400 font-medium">
                  {activeSop.category}
                </span>
              </div>
              <h3 className="text-base font-bold text-slate-100">
                {activeSop.title}
              </h3>
              <div className="flex flex-wrap gap-1.5 mt-2.5">
                {activeSop.symptoms.slice(0, 3).map((sym, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded-md bg-slate-700/60 text-slate-300 text-[11px]"
                  >
                    #{sym}
                  </span>
                ))}
              </div>
            </div>

            {/* Stepper Progression */}
            <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
              {activeSop.steps.map((step) => {
                const isCompleted = completedSteps.includes(step.step_id);
                const isActive = currentStepId === step.step_id;

                return (
                  <div key={step.step_id} className="relative group">
                    {/* Step Icon Indicator */}
                    <div
                      className={`absolute -left-6 top-1 w-5 h-5 rounded-full flex items-center justify-center transition-all duration-300 ${
                        isCompleted
                          ? 'bg-emerald-500 text-white shadow-emerald-500/40 shadow-sm'
                          : isActive
                          ? 'bg-cyan-500 text-white ring-4 ring-cyan-500/20 animate-pulse'
                          : 'bg-slate-800 text-slate-500 border border-slate-700'
                      }`}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="w-4 h-4" />
                      ) : (
                        <span className="text-[11px] font-bold font-mono">
                          {step.step_id}
                        </span>
                      )}
                    </div>

                    {/* Step Content Box */}
                    <div
                      className={`ml-3 p-4 rounded-xl border transition-all ${
                        isActive
                          ? 'bg-slate-800/90 border-cyan-500/50 shadow-md ring-1 ring-cyan-500/20'
                          : isCompleted
                          ? 'bg-slate-900/60 border-emerald-500/30 text-slate-400'
                          : 'bg-slate-900/40 border-slate-800/80 text-slate-500'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span
                          className={`text-xs font-semibold uppercase tracking-wider ${
                            isActive ? 'text-cyan-400' : isCompleted ? 'text-emerald-400' : 'text-slate-500'
                          }`}
                        >
                          Bước {step.step_id}: {isCompleted ? 'Đã hoàn thành' : isActive ? 'Đang thực hiện' : 'Chờ tới lượt'}
                        </span>
                        {step.shortcut && (
                          <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-cyan-300">
                            <Terminal className="w-3 h-3 text-cyan-400" />
                            <span>{step.shortcut}</span>
                          </div>
                        )}
                      </div>

                      <h4
                        className={`text-sm font-semibold mb-2 ${
                          isActive ? 'text-slate-100' : isCompleted ? 'text-slate-300' : 'text-slate-400'
                        }`}
                      >
                        {step.action}
                      </h4>

                      {/* Spoken Instruction preview */}
                      <p className="text-xs text-slate-400 italic bg-slate-950/60 p-2 rounded-lg border border-slate-800/80 mb-2">
                        "{step.instruction_spoken}"
                      </p>

                      {/* Expected confirmations */}
                      {step.expected_confirmation.length > 0 && (
                        <div className="flex items-center gap-1.5 flex-wrap text-[11px] text-slate-400 mt-2">
                          <span className="font-medium text-slate-500">Phản hồi mẫu:</span>
                          {step.expected_confirmation.map((c, i) => (
                            <span
                              key={i}
                              className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]"
                            >
                              "{c}"
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Fallback instruction callout */}
                      {isActive && step.fallback_instruction && (
                        <div className="mt-3 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300/90 flex items-start gap-2">
                          <HelpCircle className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
                          <div>
                            <span className="font-semibold block text-amber-300">
                              Nếu gặp lỗi / không bấm được:
                            </span>
                            {step.fallback_instruction}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          /* Empty State: SOP Knowledge Base Catalog */
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800 text-center">
              <Sparkles className="w-8 h-8 text-cyan-400 mx-auto mb-2 animate-pulse" />
              <h3 className="text-sm font-semibold text-slate-200">
                Sẵn Sàng Tiếp Nhận Sự Cố IT
              </h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Hệ thống tự động liên kết với 10+ quy trình kỹ thuật chuẩn (SOP).
                Mô tả sự cố bằng giọng nói để kích hoạt quy trình phù hợp.
              </p>
            </div>

            {/* List of Loaded SOPs in Knowledge Base */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Kho Quy Trình SOP Đã Nạp ({allSops.length}):
              </h4>
              <div className="space-y-2">
                {allSops.map((sop) => (
                  <div
                    key={sop.sop_id}
                    className="p-3 rounded-xl bg-slate-900 border border-slate-800/80 hover:border-cyan-500/40 transition-colors flex items-center justify-between cursor-default"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[11px] font-bold text-cyan-400">
                          {sop.sop_id}
                        </span>
                        <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">
                          {sop.category}
                        </span>
                      </div>
                      <p className="text-xs font-medium text-slate-300 mt-1">
                        {sop.title}
                      </p>
                    </div>
                    <span className="text-xs font-mono text-slate-500">
                      {sop.steps?.length || 0} bước
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
