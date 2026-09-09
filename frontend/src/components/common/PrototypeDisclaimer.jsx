import React from 'react';
import { ShieldAlert } from 'lucide-react';

export default function PrototypeDisclaimer({ className = '' }) {
  return (
    <div className={`bg-amber-50/90 border border-amber-200 rounded-lg p-3.5 shadow-sm text-xs text-amber-900 ${className}`}>
      <div className="flex items-start space-x-3">
        <ShieldAlert className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <span className="font-semibold text-amber-900 uppercase tracking-wide mr-1.5">
            Prototype Notice:
          </span>
          Current standards records are demonstration/sample data. Recommendations should be reviewed against authoritative BIS sources before procurement decisions. This AI-assisted prototype does not guarantee statutory compliance.
        </div>
      </div>
    </div>
  );
}
