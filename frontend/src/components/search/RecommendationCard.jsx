import React from 'react';
import { BookOpen, CheckCircle2, Tag, Calendar, ChevronRight, GitFork, FileCheck, History, Network, Award } from 'lucide-react';


import StatusBadge from '../common/StatusBadge';
import RelevanceScore from '../common/RelevanceScore';

export default function RecommendationCard({ item, rank, onViewDetails }) {
  return (
    <div className="bg-white border border-slate-200 hover:border-govnavy-300 rounded-lg p-5 shadow-sm hover:shadow transition-all duration-200 flex flex-col justify-between group">
      
      <div>
        {/* Top Badges: Rank, IS Number, Status, Relevance Score */}
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div className="flex items-center space-x-2">
            <span className="w-6 h-6 rounded bg-govnavy-900 text-white font-bold text-xs flex items-center justify-center font-mono">
              #{rank}
            </span>
            <span className="font-mono text-xs font-bold px-2.5 py-1 rounded bg-govnavy-50 text-govnavy-900 border border-govnavy-200">
              {item.is_number}
            </span>
            {item.revision_year && (
              <span className="text-[11px] text-slate-500 flex items-center space-x-1">
                <Calendar className="w-3 h-3 text-slate-400" />
                <span>Rev. {item.revision_year}</span>
              </span>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <StatusBadge status={item.status} />
            <RelevanceScore score={item.relevance_score} />
          </div>
        </div>

        {/* Title */}
        <h3 className="text-base font-bold text-slate-900 group-hover:text-govnavy-900 transition-colors mb-2 leading-snug">
          {item.title}
        </h3>

        {/* Scope snippet */}
        <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3 rounded border border-slate-200 mb-4 line-clamp-3">
          {item.scope}
        </p>

        {/* Rationale Reasons List with Evidence Signals */}
        <div className="space-y-1.5 mb-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
              Evidence-Grounded Rationale:
            </span>
            <span className="text-[9px] font-mono text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
              Prototype Corpus Evidence
            </span>
          </div>
          {item.reasons.map((reason, idx) => (
            <div key={idx} className="flex items-start space-x-2 text-xs text-slate-800">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
              <span>{reason}</span>
            </div>
          ))}
        </div>

        {/* Certification Assessment Badge */}
        {item.certification_assessment && (
          <div className="mb-2 p-2 bg-emerald-50/70 border border-emerald-200 rounded text-[11px] flex items-center justify-between gap-2">
            <span className="font-semibold text-emerald-950 flex items-center space-x-1.5 truncate">
              <Award className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
              <span className="truncate">{item.certification_assessment.certification_scheme}</span>
            </span>
            <span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-900 font-semibold text-[10px] shrink-0 border border-emerald-200">
              {item.certification_assessment.indication}
            </span>
          </div>
        )}

        {/* Version & Amendment Intelligence Badge */}
        {item.version_intelligence && (
          <div className="mb-3 p-2 bg-slate-50 border border-slate-200 rounded text-[11px] flex items-center justify-between gap-2">
            <span className="font-semibold text-slate-700 flex items-center space-x-1.5 truncate">
              <History className="w-3.5 h-3.5 text-govnavy-800 shrink-0" />
              <span className="truncate">{item.version_intelligence.version_status}</span>
            </span>
            {item.version_intelligence.has_amendments && (
              <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 font-mono font-bold text-[10px] shrink-0 border border-amber-200">
                Amd #{item.version_intelligence.latest_known_amendment_number} ({item.version_intelligence.latest_known_amendment_year})
              </span>
            )}
          </div>
        )}

        {/* Related Standards preview if available */}
        {item.related_standards && item.related_standards.length > 0 && (
          <div className="mb-3 pt-2 border-t border-slate-100 flex items-center space-x-2 text-[11px] text-slate-600">
            <GitFork className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="font-semibold text-slate-700">Related Standards:</span>
            <div className="flex flex-wrap gap-1">
              {item.related_standards.map((rel, idx) => (
                <span key={idx} className="font-mono px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700 text-[10px]">
                  {rel}
                </span>
              ))}
            </div>
          </div>
        )}

      </div>

      {/* Footer Category & Details Trigger */}
      <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
        <div className="flex items-center space-x-2 text-[11px] text-slate-600 truncate">
          <Tag className="w-3 h-3 text-slate-400 shrink-0" />
          <span className="font-medium text-slate-800 truncate">{item.product_category}</span>
          <span>•</span>
          <span className="truncate">{item.sector}</span>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <a
            href={`/network?standard_id=${encodeURIComponent(item.id || item.is_number)}`}
            className="px-2.5 py-1.5 bg-govnavy-50 hover:bg-govnavy-100 text-govnavy-900 text-xs font-semibold rounded border border-govnavy-200 transition-colors flex items-center space-x-1"
            title="Explore in Standards Knowledge Graph"
          >
            <Network className="w-3.5 h-3.5 text-govnavy-800" />
            <span className="hidden sm:inline">Network</span>
          </a>

          <button
            type="button"
            onClick={() => onViewDetails(item)}
            className="px-3 py-1.5 bg-slate-100 hover:bg-govnavy-900 hover:text-white text-slate-800 text-xs font-semibold rounded border border-slate-300 transition-colors flex items-center space-x-1"
          >
            <span>View Spec</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

      </div>

    </div>
  );
}
