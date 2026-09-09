import React from 'react';
import { X, BookOpen, Calendar, Tag, ShieldAlert, CheckCircle2, Globe } from 'lucide-react';

export default function DetailModal({ item, onClose }) {
  if (!item) return null;

  const scorePercent = Math.round(item.relevance_score * 100);

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl space-y-5 animate-scale-up">
        
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="font-mono text-sm font-bold px-3 py-1 rounded-md bg-brand-500/20 text-brand-300 border border-brand-500/30">
                {item.is_number}
              </span>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
                {item.status}
              </span>
            </div>
            <h2 className="text-lg font-bold text-slate-100 leading-snug">{item.title}</h2>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Relevance Score & Data Disclaimer */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-brand-500/20 flex items-center justify-center font-bold text-brand-300 text-base">
              {scorePercent}%
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">AI Hybrid Score</span>
              <span className="text-slate-200 font-medium">Statistical Match Score</span>
            </div>
          </div>

          <div className="bg-amber-500/10 p-3 rounded-xl border border-amber-500/30 flex items-center space-x-2 text-amber-200 text-[11px]">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
            <span>Sample record for hackathon MVP evaluation. Not authoritative BIS source.</span>
          </div>
        </div>

        {/* Full Scope */}
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center space-x-1.5">
            <BookOpen className="w-4 h-4 text-brand-400" />
            <span>Full Technical Scope</span>
          </h3>
          <p className="text-xs text-slate-200 bg-slate-950 p-4 rounded-xl border border-slate-800 leading-relaxed font-sans">
            {item.scope}
          </p>
        </div>

        {/* Metadata Details */}
        <div className="grid grid-cols-2 gap-4 text-xs bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
          <div>
            <span className="text-slate-500 text-[11px] block">Product Category</span>
            <span className="text-slate-200 font-medium">{item.product_category}</span>
          </div>
          <div>
            <span className="text-slate-500 text-[11px] block">Engineering Sector</span>
            <span className="text-slate-200 font-medium">{item.sector}</span>
          </div>
          <div>
            <span className="text-slate-500 text-[11px] block">Revision Year</span>
            <span className="text-slate-200 font-medium">{item.revision_year || 'N/A'}</span>
          </div>
          <div>
            <span className="text-slate-500 text-[11px] block">Source URL</span>
            <span className="text-slate-400 italic">None (Demo Dataset)</span>
          </div>
        </div>

        {/* Keywords */}
        {item.keywords && item.keywords.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center space-x-1.5">
              <Tag className="w-4 h-4 text-brand-400" />
              <span>Indexed Technical Keywords</span>
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {item.keywords.map((kw, idx) => (
                <span key={idx} className="text-xs px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-slate-700/60">
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Close Button */}
        <div className="pt-3 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition-colors"
          >
            Close Specification
          </button>
        </div>

      </div>
    </div>
  );
}
