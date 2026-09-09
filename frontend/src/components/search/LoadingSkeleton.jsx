import React from 'react';

export default function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-9 bg-slate-200 rounded-md w-72"></div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1, 2, 3, 4].map((n) => (
          <div key={n} className="bg-white border border-slate-200 rounded-lg p-5 space-y-4 shadow-sm">
            <div className="flex justify-between items-center">
              <div className="h-5 bg-slate-200 rounded w-32"></div>
              <div className="h-5 bg-slate-200 rounded-full w-28"></div>
            </div>
            <div className="h-6 bg-slate-200 rounded w-3/4"></div>
            <div className="h-16 bg-slate-100 rounded"></div>
            <div className="space-y-2">
              <div className="h-4 bg-slate-200 rounded w-1/2"></div>
              <div className="h-4 bg-slate-200 rounded w-2/3"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
