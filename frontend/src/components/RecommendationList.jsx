import React from 'react';
import RecommendationCard from './RecommendationCard';
import { Layers, AlertTriangle, Sparkles } from 'lucide-react';

export default function RecommendationList({ responseData, onViewDetails }) {
  if (!responseData || !responseData.recommendations) {
    return null;
  }

  const { query, recommendations, total_candidates, semantic_status } = responseData;
  const isFallback = semantic_status === 'fallback_bm25';

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
        <div className="flex items-center space-x-3 text-xs text-slate-400">
          {isFallback ? (
            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20" title="Semantic Inference Offline - Using BM25 Hybrid Keyword Engine">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              <span>BM25 Hybrid Keyword Engine</span>
            </span>
          ) : (
            <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" title="Multilingual E5 Semantic AI Active">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              <span>Multilingual E5 Semantic AI</span>
            </span>
          )}
          <span>
            Showing <span className="font-semibold text-slate-200">{recommendations.length}</span> of <span className="font-semibold text-slate-200">{total_candidates}</span> demo corpus standards
          </span>
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
