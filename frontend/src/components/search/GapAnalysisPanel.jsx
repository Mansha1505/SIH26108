import React from 'react';

const GapAnalysisPanel = ({ gapAnalysis, loading = false, error = null }) => {
  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-400">
        <div className="animate-spin inline-block w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full mb-2"></div>
        <p className="text-sm font-medium">Evaluating procurement requirements against prototype corpus evidence...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-950/40 border border-rose-900/50 rounded-xl p-4 text-rose-300 text-sm">
        <strong>Gap Analysis Notice:</strong> {error}
      </div>
    );
  }

  if (!gapAnalysis || !gapAnalysis.requirements || gapAnalysis.requirements.length === 0) {
    return null;
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'covered':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            ✓ Covered
          </span>
        );
      case 'partially_covered':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            ◐ Partially Covered
          </span>
        );
      case 'not_evidenced':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
            ? Not Evidenced in Corpus
          </span>
        );
      case 'requires_verification':
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/30">
            ! Requires Verification
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4 my-4">
      {/* Header Summary */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">📊</span>
            <h3 className="text-lg font-bold text-white tracking-wide">
              Procurement Requirement Gap Analysis
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Evidence-grounded coverage assessment against 14 prototype Indian Standards.
          </p>
        </div>

        {/* Count Stat Cards */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-1 text-center min-w-[70px]">
            <span className="text-xs text-slate-400 block uppercase font-medium">Total</span>
            <span className="text-sm font-bold text-white">{gapAnalysis.total_requirements}</span>
          </div>
          <div className="bg-emerald-950/40 border border-emerald-900/50 rounded-lg px-3 py-1 text-center min-w-[70px]">
            <span className="text-xs text-emerald-400 block uppercase font-medium">Covered</span>
            <span className="text-sm font-bold text-emerald-300">{gapAnalysis.covered_count}</span>
          </div>
          <div className="bg-amber-950/40 border border-amber-900/50 rounded-lg px-3 py-1 text-center min-w-[70px]">
            <span className="text-xs text-amber-400 block uppercase font-medium">Partial</span>
            <span className="text-sm font-bold text-amber-300">{gapAnalysis.partially_covered_count}</span>
          </div>
          <div className="bg-indigo-950/40 border border-indigo-900/50 rounded-lg px-3 py-1 text-center min-w-[75px]">
            <span className="text-xs text-indigo-400 block uppercase font-medium">Not Evidenced</span>
            <span className="text-sm font-bold text-indigo-300">{gapAnalysis.not_evidenced_count}</span>
          </div>
        </div>
      </div>

      {/* Coverage Summary Text */}
      {gapAnalysis.coverage_summary && (
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3 text-xs text-slate-300 leading-relaxed">
          <strong>Summary:</strong> {gapAnalysis.coverage_summary}
        </div>
      )}

      {/* Granular Requirement Breakdown List */}
      <div className="space-y-3">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Granular Requirement Coverage Breakdown
        </h4>
        <div className="grid grid-cols-1 gap-3">
          {gapAnalysis.requirements.map((req) => (
            <div
              key={req.requirement_id}
              className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3.5 space-y-2 hover:border-slate-700 transition-colors"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
                    {req.requirement_id}
                  </span>
                  <span className="text-sm font-medium text-slate-200">
                    {req.requirement_text}
                  </span>
                </div>
                {getStatusBadge(req.status)}
              </div>

              {/* Supporting Standards */}
              {req.supporting_standard_ids && req.supporting_standard_ids.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-xs text-slate-400">Supporting Standards:</span>
                  {req.supporting_standard_ids.map((stdId, idx) => (
                    <span
                      key={idx}
                      className="text-xs font-medium px-2 py-0.5 rounded bg-slate-800/80 text-emerald-300 border border-slate-700"
                    >
                      {stdId}
                    </span>
                  ))}
                </div>
              )}

              {/* Evidence details */}
              {req.evidence && req.evidence.length > 0 && (
                <ul className="text-xs text-slate-300 space-y-1 pl-4 list-disc marker:text-emerald-400">
                  {req.evidence.map((ev, idx) => (
                    <li key={idx}>{ev}</li>
                  ))}
                </ul>
              )}

              {/* Missing aspects / Unevidenced note */}
              {req.missing_aspects && req.missing_aspects.length > 0 && (
                <div className="bg-indigo-950/20 border border-indigo-900/30 rounded p-2 text-xs text-indigo-300 space-y-1">
                  {req.missing_aspects.map((m, idx) => (
                    <div key={idx} className="flex items-start gap-1">
                      <span>📌</span>
                      <span>{m}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Legal & Data Honesty Disclaimer */}
      <div className="bg-slate-950/80 border border-amber-900/40 rounded-lg p-3 text-[11px] text-amber-300/90 leading-relaxed flex items-start gap-2">
        <span className="text-amber-400 text-sm">⚠️</span>
        <div>
          <strong>Corpus Boundary Notice:</strong> {gapAnalysis.disclaimer || "Gap analysis compares extracted requirements against available prototype corpus evidence. 'Not evidenced' means no evidence was found in this demo corpus; it does NOT imply that no applicable Indian Standard exists in official BIS records."}
        </div>
      </div>
    </div>
  );
};

export default GapAnalysisPanel;
