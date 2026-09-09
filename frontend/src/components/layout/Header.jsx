import React from 'react';
import { Shield, Database, Cpu, ExternalLink } from 'lucide-react';

export default function Header({ healthInfo }) {
  return (
    <header className="bg-govnavy-900 text-white shadow-md sticky top-0 z-40">
      {/* Tricolor Subtle Accent Line */}
      <div className="h-1 w-full bg-gradient-to-r from-saffron-600 via-white to-emerald-600"></div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-4">
        
        {/* Government Emblem Placeholder & System Title */}
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-lg bg-govnavy-800 border border-govnavy-700 flex items-center justify-center shadow-inner text-saffron-500 shrink-0">
            <Shield className="w-6 h-6 stroke-[2]" />
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <span className="text-xs font-bold uppercase tracking-wider text-saffron-500 font-mono">
                Government Procurement Intelligence
              </span>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-saffron-500/20 text-saffron-300 border border-saffron-500/40">
                SIH 2026 Prototype
              </span>
            </div>
            <h1 className="text-base font-bold text-white tracking-tight">
              AI-Assisted Indian Standards Recommendation Engine
            </h1>
          </div>
        </div>

        {/* Status Indicators & Metadata */}
        <div className="flex items-center space-x-3 text-xs">
          
          {/* Index count badge */}
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-govnavy-800 border border-govnavy-700 text-slate-200">
            <Database className="w-3.5 h-3.5 text-saffron-500" />
            <span>
              Corpus: <strong className="text-white">{healthInfo ? `${healthInfo.total_standards_indexed} Standards` : '14 Demo Standards'}</strong>
            </span>
          </div>

          {/* Engine type badge */}
          <div className="hidden md:flex items-center space-x-1.5 px-3 py-1.5 rounded bg-emerald-950/60 border border-emerald-700/60 text-emerald-300">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-medium text-[11px]">BM25 + Dense Hybrid</span>
          </div>

          {/* API Docs Link */}
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1 px-3 py-1.5 rounded bg-govnavy-800 hover:bg-govnavy-700 text-slate-200 border border-govnavy-700 transition-colors text-[11px]"
          >
            <span>API Docs</span>
            <ExternalLink className="w-3 h-3 text-slate-400" />
          </a>

        </div>

      </div>
    </header>
  );
}
