import React from 'react';
import RecommendationCard from './RecommendationCard';
import { Layers } from 'lucide-react';

export default function RecommendationList({ responseData, onViewDetails }) {
  if (!responseData || !responseData.recommendations) {
    return null;
  }

  const { query, recommendations, total_candidates } = responseData;

  return (
    <div className="space-y-4 animate-fade-in">
      
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/50 border border-slate-800/80 px-4 py-3 rounded-xl">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-brand-400" />
          <h2 className="text-sm font-semibold text-slate-200">
            Top Recommendations for: <span className="text-brand-300 italic">"{query}"</span>
          </h2>
        </div>
        <div className="text-xs text-slate-400">
          Showing <span className="font-semibold text-slate-200">{recommendations.length}</span> of <span className="font-semibold text-slate-200">{total_candidates}</span> demo corpus standards
        </div>
      </div>

      {/* Grid of cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {recommendations.map((item, idx) => (
          <RecommendationCard
            key={idx}
            rank={idx + 1}
            item={item}
            onViewDetails={onViewDetails}
          />
        ))}
      </div>

    </div>
  );
}
