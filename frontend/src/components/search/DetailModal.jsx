import React from 'react';
import { X, BookOpen, Calendar, Tag, ShieldAlert, CheckCircle2, GitFork, History, Network, Award } from 'lucide-react';

import StatusBadge from '../common/StatusBadge';
import RelevanceScore from '../common/RelevanceScore';

export default function DetailModal({ item, onClose }) {
  if (!item) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white border border-slate-300 rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-xl space-y-5 animate-in fade-in zoom-in-95 duration-150">
        
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 pb-4">
          <div>
            <div className="flex items-center space-x-2.5 mb-1">
              <span className="font-mono text-sm font-bold px-3 py-1 rounded bg-govnavy-900 text-white">
                {item.is_number}
              </span>
              <StatusBadge status={item.status} />
              <RelevanceScore item={item} score={item.relevance_score} />
            </div>
            <h2 className="text-lg font-bold text-slate-900 leading-snug">{item.title}</h2>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors"
            title="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Prototype Notice */}
        <div className="bg-amber-50 border border-amber-200 p-3 rounded text-xs text-amber-900 flex items-start space-x-2.5">
          <ShieldAlert className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
          <div>
            <strong>Prototype Data Notice:</strong> Standard record metadata is from the local demo corpus. Verify all details against official BIS publications prior to finalizing tender specifications.
          </div>
        </div>

        {/* Why this standard? Evidence-Grounded Explanation */}
        <div className="bg-govnavy-900 text-white rounded-lg p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-govnavy-700 pb-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-saffron-400 flex items-center space-x-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Why This Standard? (Evidence-Grounded Explanation)</span>
            </h3>
            <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-govnavy-800 text-slate-300 border border-govnavy-700">
              Evidence-Grounded • Deterministic Engine
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
            <div className="bg-govnavy-950 p-2 rounded border border-govnavy-800 flex items-center space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>Product Match</span>
            </div>
            <div className="bg-govnavy-950 p-2 rounded border border-govnavy-800 flex items-center space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>Technical Spec Match</span>
            </div>
            <div className="bg-govnavy-950 p-2 rounded border border-govnavy-800 flex items-center space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>Scope Alignment</span>
            </div>
            <div className="bg-govnavy-950 p-2 rounded border border-govnavy-800 flex items-center space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>Semantic Relevance</span>
            </div>
          </div>

          <p className="text-xs text-slate-200 leading-relaxed font-sans bg-govnavy-950/80 p-3 rounded border border-govnavy-800">
            Recommended based on high technical scope alignment with product category <strong className="text-saffron-300">{item.product_category}</strong> and vector/keyword similarity signals in the prototype corpus.
          </p>

          <div className="pt-1 flex flex-wrap items-center justify-between text-[10px] text-slate-400 border-t border-govnavy-800">
            <span>Evidence Source: Prototype Corpus Metadata & Rule Engine</span>
            <span className="font-semibold text-amber-300">Authoritative Verification Required</span>
          </div>
        </div>

        {/* Description / Summary if present */}
        {item.description && (
          <div className="bg-govnavy-50/70 border border-govnavy-200 p-3.5 rounded text-xs text-govnavy-950">
            <span className="font-bold block mb-1 uppercase tracking-wider text-[11px] text-govnavy-900">Procurement Overview:</span>
            <p className="leading-relaxed">{item.description}</p>
          </div>
        )}

        {/* Full Scope */}
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2 flex items-center space-x-1.5">
            <BookOpen className="w-4 h-4 text-govnavy-800" />
            <span>Full Technical Scope</span>
          </h3>
          <p className="text-xs text-slate-800 bg-slate-50 p-4 rounded border border-slate-200 leading-relaxed font-sans">
            {item.scope}
          </p>
        </div>

        {/* Certification Assessment Section */}
        {item.certification_assessment && (
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2 flex items-center space-x-1.5">
              <Award className="w-4 h-4 text-saffron-600" />
              <span>Certification Intelligence (Prototype Rule Engine)</span>
            </h3>
            <div className="bg-emerald-50/60 border border-emerald-200 p-4 rounded-lg space-y-2.5 text-xs">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-emerald-200 pb-2">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-govnavy-900 text-white">
                    {item.certification_assessment.rule_id || 'RULE-MAPPED'}
                  </span>
                  <span className="font-bold text-govnavy-950">{item.certification_assessment.certification_scheme}</span>
                </div>
                <div className="flex items-center space-x-2">
                  {item.certification_assessment.scheme_status === 'requires_authoritative_verification' && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                      Transitioning / Verification Required
                    </span>
                  )}
                  <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-900 border border-emerald-300">
                    {item.certification_assessment.indication}
                  </span>
                </div>
              </div>

              {item.certification_assessment.applicable_order && (
                <div className="bg-white p-2.5 rounded border border-emerald-200 space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">Notified Order Reference:</span>
                  <span className="font-semibold text-slate-900 block text-xs">{item.certification_assessment.applicable_order}</span>
                  {(item.certification_assessment.order_date || item.certification_assessment.effective_date) && (
                    <div className="flex space-x-4 text-[10px] text-slate-600 pt-0.5 font-mono">
                      {item.certification_assessment.order_date && <span>Notified: {item.certification_assessment.order_date}</span>}
                      {item.certification_assessment.effective_date && <span>Effective: {item.certification_assessment.effective_date}</span>}
                    </div>
                  )}
                  {item.certification_assessment.superseded_by && (
                    <div className="text-[10px] text-amber-900 font-semibold bg-amber-50 p-1.5 rounded border border-amber-200 mt-1">
                      ⚠️ Framework Update / Transition: {item.certification_assessment.superseded_by}
                    </div>
                  )}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                <div>
                  <span className="text-slate-500 block font-semibold text-[10px]">Applicability Basis</span>
                  <span className="font-medium text-slate-900">{item.certification_assessment.applicability_basis}</span>
                </div>
                <div>
                  <span className="text-slate-500 block font-semibold text-[10px]">Source Reference / Provenance</span>
                  <span className="font-mono text-slate-800">{item.certification_assessment.source_reference} ({item.certification_assessment.source_type})</span>
                </div>
              </div>

              {item.certification_assessment.notes && (
                <p className="text-[11px] text-slate-700 bg-white p-2.5 rounded border border-emerald-200 leading-relaxed">
                  <strong>Notes & Scope Limits:</strong> {item.certification_assessment.notes}
                </p>
              )}

              <div className="pt-1 text-[10px] text-amber-900 font-medium flex items-center space-x-1 bg-amber-50/80 p-2 rounded border border-amber-200">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-700 shrink-0" />
                <span>Verification Requirement: Authoritative confirmation required from official gazette/BIS portal prior to tender specification finalization.</span>
              </div>
            </div>
          </div>
        )}

        {/* Version & Amendments Section */}
        {item.version_intelligence ? (
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2 flex items-center space-x-1.5">
              <History className="w-4 h-4 text-govnavy-800" />
              <span>Version & Amendment Intelligence</span>
            </h3>
            <div className="bg-slate-50 p-3.5 rounded border border-slate-200 text-xs space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-semibold text-slate-900">{item.version_intelligence.version_status}</span>
                <span className="text-[11px] text-amber-800 font-medium bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  Authoritative BIS Verification Required
                </span>
              </div>
              <p className="text-slate-700 text-xs leading-relaxed">{item.version_intelligence.summary}</p>
              
              {item.version_intelligence.has_amendments && (
                <div className="mt-2 space-y-1.5 pt-2 border-t border-slate-200">
                  <span className="text-[11px] font-bold text-slate-600 block">Recorded Amendment History:</span>
                  {item.version_intelligence.amendment_history.map((amd, idx) => (
                    <div key={idx} className="bg-white p-2 rounded border border-slate-200 text-xs text-slate-800 flex items-start space-x-2">
                      <span className="font-mono font-semibold px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 text-[10px] border border-amber-200">
                        Amd. #{amd.amendment_number || 'N/A'} ({amd.year || 'N/A'})
                      </span>
                      <span>{amd.title}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : item.amendments && item.amendments.length > 0 && (
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2 flex items-center space-x-1.5">
              <History className="w-4 h-4 text-govnavy-800" />
              <span>Issued Amendments</span>
            </h3>
            <div className="space-y-1.5">
              {item.amendments.map((amd, idx) => (
                <div key={idx} className="bg-slate-50 p-2.5 rounded border border-slate-200 text-xs text-slate-800 flex items-start space-x-2">
                  <span className="font-mono font-semibold px-1.5 py-0.5 rounded bg-slate-200 text-slate-800 text-[10px]">
                    Amd. #{amd.amendment_number} ({amd.year})
                  </span>
                  <span>{amd.title}</span>
                </div>
              ))}
            </div>
          </div>
        )}


        {/* Related Standards Section */}
        {item.related_standards && item.related_standards.length > 0 && (
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2 flex items-center space-x-1.5">
              <GitFork className="w-4 h-4 text-govnavy-800" />
              <span>Cross-Referenced Standards</span>
            </h3>
            <div className="flex flex-wrap gap-2">
              {item.related_standards.map((rel, idx) => (
                <span key={idx} className="font-mono text-xs font-semibold px-2.5 py-1 rounded bg-slate-100 border border-slate-300 text-slate-800">
                  {rel}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Metadata Table */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs bg-slate-50 p-4 rounded border border-slate-200">
          <div>
            <span className="text-slate-500 text-[11px] block">Product Category</span>
            <span className="text-slate-900 font-semibold">{item.product_category}</span>
          </div>
          <div>
            <span className="text-slate-500 text-[11px] block">Engineering Sector</span>
            <span className="text-slate-900 font-semibold">{item.sector}</span>
          </div>
          <div>
            <span className="text-slate-500 text-[11px] block">Revision Year</span>
            <span className="text-slate-900 font-semibold">{item.revision_year || 'N/A'}</span>
          </div>
        </div>

        {/* Keywords */}
        {item.keywords && item.keywords.length > 0 && (
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1.5">
              Indexed Technical Keywords:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {item.keywords.map((kw, idx) => (
                <span key={idx} className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-mono">
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Modal Footer */}
        <div className="pt-3 border-t border-slate-200 flex items-center justify-between gap-2">
          <a
            href={`/network?standard_id=${encodeURIComponent(item.id || item.is_number)}`}
            className="px-3.5 py-2 bg-govnavy-50 hover:bg-govnavy-100 text-govnavy-900 text-xs font-semibold rounded border border-govnavy-200 transition-colors flex items-center space-x-1.5"
            title="Explore in Standards Knowledge Graph"
          >
            <Network className="w-4 h-4 text-govnavy-800" />
            <span>Explore in Standards Network</span>
          </a>

          <button
            onClick={onClose}
            className="px-4 py-2 bg-govnavy-900 hover:bg-govnavy-800 text-white text-xs font-semibold rounded shadow-xs transition-colors"
          >
            Close Specification
          </button>
        </div>


      </div>
    </div>
  );
}
