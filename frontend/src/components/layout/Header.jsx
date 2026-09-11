import React from 'react';
import { Shield, Database, ExternalLink, LogOut, UserCheck } from 'lucide-react';

export default function Header({ healthInfo, onLogout }) {
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

          {/* Officer & Logout control */}
          {onLogout && (
            <div className="flex items-center space-x-2 border-l border-govnavy-700 pl-3">
              <span className="hidden xl:flex items-center space-x-1 text-[11px] text-slate-300 bg-govnavy-950 px-2 py-1 rounded border border-govnavy-800">
                <UserCheck className="w-3 h-3 text-saffron-400" />
                <span className="font-mono">Officer Portal</span>
              </span>
              <button
                type="button"
                onClick={onLogout}
                className="px-2.5 py-1.5 rounded bg-red-950/80 hover:bg-red-900 text-red-200 border border-red-800 transition-colors text-[11px] font-semibold flex items-center space-x-1 cursor-pointer"
                title="Sign out of Procurement Officer Portal"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Logout</span>
              </button>
            </div>
          )}

        </div>

      </div>
    </header>
  );
}
