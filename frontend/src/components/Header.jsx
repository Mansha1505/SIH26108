import React from 'react';
import { ShieldCheck, Cpu, Database, FileText } from 'lucide-react';

export default function Header({ healthInfo }) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
        
        {/* Title and Hackathon Badge */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-brand-500/20 ring-1 ring-white/20">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold text-white tracking-tight">SIH26108 Standards AI</h1>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300 border border-brand-500/30">
                SIH 2026 MVP
              </span>
            </div>
            <p className="text-xs text-slate-400">
              AI-Powered Indian Standards (IS/BIS) Recommendation Engine for Procurement Specifications
            </p>
          </div>
        </div>

        {/* System Status Indicators */}
        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300">
            <Database className="w-3.5 h-3.5 text-brand-400" />
            <span>
              Corpus: <strong className="text-slate-100">{healthInfo ? `${healthInfo.total_standards_indexed} Standards` : 'Demo JSON'}</strong>
            </span>
          </div>

          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-medium">BM25 + Dense Semantic Fusion</span>
          </div>

          <a 
            href="/docs" 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700/50"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>API Docs</span>
          </a>
        </div>

      </div>
    </header>
  );
}
