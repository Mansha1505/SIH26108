import React from 'react';
import { ShieldAlert, Info } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-govnavy-950 text-slate-400 border-t border-govnavy-800 text-xs py-8 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        
        {/* Prototype & Legal Disclaimer Box */}
        <div className="bg-govnavy-900/90 border border-govnavy-800 rounded-lg p-4 space-y-2 text-slate-300">
          <div className="flex items-center space-x-2 font-semibold text-saffron-500 uppercase tracking-wider text-[11px]">
            <ShieldAlert className="w-4 h-4 text-saffron-500 shrink-0" />
            <span>Prototype Notice & System Disclaimer</span>
          </div>
          <p className="leading-relaxed text-[11px] text-slate-300">
            <strong>Prototype Notice:</strong> Current standards records are demonstration/sample data. Recommendations should be reviewed against authoritative BIS sources before procurement decisions.
          </p>
          <p className="leading-relaxed text-[11px] text-slate-400">
            This AI-assisted recommendation system generates statistical relevance scores based on natural-language keyword matching and sentence embedding similarities. It is <strong>NOT</strong> a legal compliance engine or official BIS certification service. Recommendations do not constitute legal advice or guarantee statutory compliance.
          </p>
        </div>

        {/* Footer Bottom Links & Copyright */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-govnavy-900 text-[11px] text-slate-500">
          <div>
            <strong>SIH 2026 Prototype</strong> — AI-Assisted Recommendation Engine for Identifying Applicable Indian Standards for Procurement Specifications (Problem Statement SIH26108).
          </div>
          <div className="flex space-x-4">
            <span>Local Demo Corpus</span>
            <span>•</span>
            <span>BM25 + Dense Hybrid IR</span>
            <span>•</span>
            <span>FastAPI + React Architecture</span>
          </div>
        </div>

      </div>
    </footer>
  );
}
