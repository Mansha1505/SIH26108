import React from 'react';
import { BookOpen, CheckCircle2, Tag, Calendar, ChevronRight, ShieldAlert } from 'lucide-react';

export default function RecommendationCard({ item, rank, onViewDetails }) {
  // Score formatting
  const relVal = item?.relative_match_score;
  const scorePercent = relVal !== undefined && relVal !== null 
    ? Math.round(relVal) 
    : Math.round((item.relevance_score || 0) * 100);

  let scoreBadgeClass = 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
  if (scorePercent < 50) {
    scoreBadgeClass = 'bg-amber-500/20 text-amber-300 border-amber-500/30';
  } else if (scorePercent < 75) {
    scoreBadgeClass = 'bg-sky-500/20 text-sky-300 border-sky-500/30';
  }

  return (
    <div className="bg-slate-900/90 border border-slate-800 hover:border-slate-700/80 rounded-xl p-5 shadow-lg transition-all duration-200 hover:shadow-brand-900/20 group relative flex flex-col justify-between">
      
      <div>
        {/* Header Badges: Rank, IS Number, Relative Match Score */}
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div className="flex items-center space-x-2">
            <span className="w-6 h-6 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-300">
              #{rank}
            </span>
            <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-md bg-brand-500/10 text-brand-300 border border-brand-500/20">
              {item.is_number}
            </span>
            {item.revision_year && (
              <span className="text-[11px] text-slate-400 flex items-center space-x-1">
                <Calendar className="w-3 h-3" />
                <span>{item.revision_year}</span>
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <span 
              className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${scoreBadgeClass}`}
              title="Relative match score indicates how strongly this result matches the current query compared with other returned candidates. It is not a legal compliance or accuracy guarantee."
            >
              Relative Match Score: {scorePercent}%
            </span>
          </div>
        </div>

        {/* Title */}
        <h3 className="text-base font-semibold text-slate-100 group-hover:text-brand-300 transition-colors mb-2 leading-snug">
          {item.title}
        </h3>

        {/* Scope Snippet */}
        <p className="text-xs text-slate-300 line-clamp-3 mb-4 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
          {item.scope}
        </p>

        {/* Deterministic Reasons */}
        <div className="space-y-1.5 mb-4">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
            Recommendation Rationale:
          </span>
          {item.reasons.map((reason, idx) => (
            <div key={idx} className="flex items-start space-x-2 text-xs text-slate-300">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
              <span>{reason}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Metadata & Details Button */}
      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
        <div className="flex items-center space-x-2 text-[11px] text-slate-400 overflow-hidden">
          <Tag className="w-3 h-3 shrink-0 text-slate-500" />
          <span className="truncate">{item.product_category}</span>
          <span>•</span>
          <span className="truncate">{item.sector}</span>
        </div>

        <button
          type="button"
          onClick={() => onViewDetails(item)}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700/80 transition-colors flex items-center space-x-1 shrink-0"
        >
          <span>Full Spec</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

    </div>
  );
}
