import React from 'react';

export default function PageHeader({ title, subtitle, badgeText, actions }) {
  return (
    <div className="border-b border-slate-200 bg-white px-4 sm:px-6 lg:px-8 py-5 shadow-sm mb-6">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">{title}</h1>
            {badgeText && (
              <span className="text-[11px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-govnavy-50 text-govnavy-800 border border-govnavy-200">
                {badgeText}
              </span>
            )}
          </div>
          {subtitle && <p className="text-xs text-slate-600 mt-1 max-w-3xl leading-relaxed">{subtitle}</p>}
        </div>
        {actions && <div className="flex items-center space-x-3">{actions}</div>}
      </div>
    </div>
  );
}
