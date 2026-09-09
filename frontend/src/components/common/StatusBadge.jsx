import React from 'react';
import { Tag } from 'lucide-react';

export default function StatusBadge({ status, className = '' }) {
  const isDemo = status?.includes('DEMO') || status?.includes('SAMPLE');
  
  return (
    <span
      className={`inline-flex items-center space-x-1 font-mono text-[11px] font-semibold px-2 py-0.5 rounded border ${
        isDemo
          ? 'bg-amber-50 text-amber-800 border-amber-200'
          : 'bg-emerald-50 text-emerald-800 border-emerald-200'
      } ${className}`}
    >
      <Tag className="w-3 h-3 shrink-0" />
      <span>{status || 'Active (DEMO DATA)'}</span>
    </span>
  );
}
