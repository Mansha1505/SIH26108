import React from 'react';
import { Search, FileText, Shield, Sparkles, Layers, ArrowRight, Database, Cpu, CheckCircle2 } from 'lucide-react';
import PrototypeDisclaimer from '../components/common/PrototypeDisclaimer';

export default function DashboardPage({ onNavigate, onSelectPrompt, healthInfo }) {
  const QUICK_PROMPTS = [
    { title: "Outdoor LED Street Lighting", query: "50W LED street light for outdoor municipal roads", cat: "Lighting & Luminaires" },
    { title: "Structural Foundation Cement", query: "Portland Slag Cement for structural foundation work", cat: "Cement & Construction" },
    { title: "Agricultural Borewell Pumping", query: "Submersible pump set for agricultural water supply", cat: "Pumps & Hydraulics" },
    { title: "Solar Power Generation", query: "Crystalline Silicon PV Modules for solar power plant", cat: "Renewable Energy" },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      
      {/* Prototype Disclaimer Banner */}
      <PrototypeDisclaimer />

      {/* Hero Section */}
      <div className="bg-gradient-to-r from-govnavy-950 via-govnavy-900 to-govnavy-950 text-white rounded-xl p-8 sm:p-10 shadow-lg border border-govnavy-800 relative overflow-hidden">
        
        {/* Background Subtle Accent Pattern */}
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-saffron-500/5 blur-3xl pointer-events-none"></div>

        <div className="max-w-3xl space-y-4 relative z-10">
          
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded bg-saffron-500/20 text-saffron-300 border border-saffron-500/30 text-xs font-semibold uppercase tracking-wider font-mono">
            <Sparkles className="w-3.5 h-3.5 text-saffron-400" />
            <span>AI-Assisted Procurement Intelligence System</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight leading-tight text-white">
            Identify the Indian Standards relevant to your procurement specification.
          </h1>

          <p className="text-sm text-slate-300 leading-relaxed">
            Analyze natural-language product descriptions, technical tender requirements, and specification sheets to get ranked, AI-assisted recommendations of applicable Indian Standards (IS/BIS) backed by BM25 keyword precision and dense semantic vector retrieval.
          </p>

          {/* Primary Actions */}
          <div className="pt-2 flex flex-wrap items-center gap-3">
            <button
              onClick={() => onNavigate('search')}
              className="px-5 py-2.5 bg-saffron-600 hover:bg-saffron-500 text-white font-bold text-xs rounded transition-all shadow-md flex items-center space-x-2"
            >
              <Search className="w-4 h-4" />
              <span>Search Standards</span>
            </button>

            <button
              onClick={() => onNavigate('tender-analyzer')}
              className="px-5 py-2.5 bg-govnavy-800 hover:bg-govnavy-700 text-white font-semibold text-xs rounded border border-govnavy-600 transition-all flex items-center space-x-2"
            >
              <FileText className="w-4 h-4 text-slate-300" />
              <span>Analyze Tender PDF</span>
            </button>
          </div>

        </div>
      </div>

      {/* Core Capability Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-2">
          <div className="w-9 h-9 rounded bg-govnavy-50 text-govnavy-800 flex items-center justify-center border border-govnavy-200 mb-1">
            <Database className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">Curated Standards Dataset</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Indexed standards corpus containing technical scopes, keywords, sectors, and revision histories.
          </p>
          <div className="text-[11px] font-semibold text-govnavy-800 pt-1">
            {healthInfo ? `${healthInfo.total_standards_indexed} Standards Indexed` : '14 Demo Standards'}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-2">
          <div className="w-9 h-9 rounded bg-emerald-50 text-emerald-800 flex items-center justify-center border border-emerald-200 mb-1">
            <Cpu className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">Hybrid Retrieval Engine</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Combines BM25 lexical keyword matching with Sentence-Transformer vector cosine similarities.
          </p>
          <div className="text-[11px] font-semibold text-emerald-800 pt-1">
            Normalized Score Fusion (α = 0.6)
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-2">
          <div className="w-9 h-9 rounded bg-saffron-50 text-saffron-900 flex items-center justify-center border border-saffron-200 mb-1">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">Deterministic Rationale</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Provides metadata-based justification reasons for product categories, keyword overlap, and technical scope.
          </p>
          <div className="text-[11px] font-semibold text-saffron-900 pt-1">
            Human-Auditable Explanations
          </div>
        </div>

      </div>

      {/* Quick Launch Search Prompts */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Common Procurement Requirements</h2>
            <p className="text-xs text-slate-600">Click any category below to immediately execute a standards search.</p>
          </div>
          <button
            onClick={() => onNavigate('search')}
            className="text-xs font-semibold text-govnavy-800 hover:text-govnavy-900 flex items-center space-x-1"
          >
            <span>View All Search Options</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {QUICK_PROMPTS.map((item, idx) => (
            <div
              key={idx}
              onClick={() => onSelectPrompt(item.query)}
              className="bg-slate-50 hover:bg-govnavy-50/80 border border-slate-200 hover:border-govnavy-300 rounded p-4 cursor-pointer transition-all space-y-2 group"
            >
              <span className="text-[10px] font-bold uppercase tracking-wider text-saffron-700 font-mono block">
                {item.cat}
              </span>
              <h4 className="text-xs font-bold text-slate-900 group-hover:text-govnavy-900">
                {item.title}
              </h4>
              <p className="text-[11px] text-slate-600 line-clamp-2 italic">
                "{item.query}"
              </p>
              <div className="text-[11px] font-semibold text-govnavy-800 group-hover:underline flex items-center space-x-1 pt-1">
                <span>Run Search</span>
                <ArrowRight className="w-3 h-3" />
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
