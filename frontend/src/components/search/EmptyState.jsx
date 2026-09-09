import React from 'react';
import { SearchX, ArrowRight } from 'lucide-react';

export default function EmptyState({ onSelectExample }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-10 text-center max-w-2xl mx-auto space-y-4 shadow-sm my-6">
      <div className="w-12 h-12 rounded-full bg-govnavy-50 text-govnavy-800 mx-auto flex items-center justify-center border border-govnavy-200">
        <SearchX className="w-6 h-6" />
      </div>
      <div className="space-y-1">
        <h3 className="text-base font-bold text-slate-900">Ready to Analyze Procurement Requirements</h3>
        <p className="text-xs text-slate-600 max-w-md mx-auto leading-relaxed">
          Enter a product description or tender requirement query in the search bar above to run hybrid BM25 and dense sentence-transformer retrieval against the demo Indian Standards corpus.
        </p>
      </div>
      
      {onSelectExample && (
        <div className="pt-2">
          <button
            onClick={() => onSelectExample("50W LED street light for outdoor municipal roads")}
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-govnavy-900 hover:bg-govnavy-800 text-white font-semibold text-xs rounded transition-colors shadow-xs"
          >
            <span>Try sample query: "50W LED street light"</span>
            <ArrowRight className="w-3.5 h-3.5 text-saffron-500" />
          </button>
        </div>
      )}
    </div>
  );
}
