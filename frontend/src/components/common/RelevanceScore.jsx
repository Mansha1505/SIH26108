import React from 'react';

export default function RelevanceScore({ score, relativeScore, item }) {
  const relVal = item?.relative_match_score ?? relativeScore;
  const percent = relVal !== undefined && relVal !== null 
    ? Math.round(relVal) 
    : Math.round((score || 0) * 100);

  let badgeBg = 'bg-emerald-50 text-emerald-800 border-emerald-300';
  let badgeBar = 'bg-emerald-600';

  if (percent < 50) {
    badgeBg = 'bg-amber-50 text-amber-800 border-amber-300';
    badgeBar = 'bg-amber-600';
  } else if (percent < 75) {
    badgeBg = 'bg-sky-50 text-sky-800 border-sky-300';
    badgeBar = 'bg-sky-600';
  }

  const tooltipText = "Relative match score indicates how strongly this result matches the current query compared with other returned candidates. It is not a legal compliance or accuracy guarantee.";

  return (
    <div 
      className={`inline-flex items-center space-x-2 px-2.5 py-1 rounded-md border text-xs font-medium ${badgeBg}`}
      title={tooltipText}
    >
      <span className="font-semibold text-slate-700">Relative Match Score:</span>
      <span className="font-bold font-mono">{percent}%</span>
      <div className="w-12 h-1.5 bg-slate-200 rounded-full overflow-hidden shrink-0 hidden sm:block">
        <div className={`h-full ${badgeBar}`} style={{ width: `${percent}%` }}></div>
      </div>
    </div>
  );
}
