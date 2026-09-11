import React from 'react';
import RecommendationCard from './RecommendationCard';
import { Layers } from 'lucide-react';

export default function RecommendationList({ responseData, onViewDetails }) {
  if (!responseData || !responseData.recommendations) {
    return null;
  }

  const { query, recommendations, total_candidates } = responseData;

  return (
    <div className="space-y-4">
      
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white border border-slate-200 px-4 py-3 rounded-lg shadow-sm">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-govnavy-800" />
          <h2 className="text-sm font-bold text-slate-900">
            Recommendations for: <span className="text-govnavy-900 italic font-medium">"{query}"</span>
          </h2>
        </div>
        <div className="text-xs text-slate-600">
          Showing top <span className="font-bold text-slate-900">{recommendations.length}</span> candidates (evaluated {total_candidates} demo standards)
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
