import React from 'react';
import { Search, Sparkles, X, SlidersHorizontal } from 'lucide-react';

const SAMPLE_PROMPTS = [
  "50W LED street light for outdoor municipal roads",
  "कृषि के लिए सबमर्सिबल पानी का पंप",
  "Portland Slag Cement for structural foundation work",
  "kheti ke liye submersible water pump",
  "Submersible pump set for agricultural water supply",
  "Crosslinked polyethylene XLPE insulated power cables 1100V",
];

export default function SearchBar({ query, setQuery, topK, setTopK, onSearch, isLoading }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query, parseInt(topK, 10));
    }
  };

  const handleChipClick = (prompt) => {
    setQuery(prompt);
    onSearch(prompt, parseInt(topK, 10));
  };

  const handleTopKChange = (e) => {
    const val = parseInt(e.target.value, 10);
    setTopK(val);
    if (query.trim() && !isLoading) {
      onSearch(query, val);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm mb-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        
        {/* Search Input Box */}
        <div className="relative flex items-center">
          <label htmlFor="standards-search-input" className="sr-only">Search Procurement Requirements</label>
          <Search className="absolute left-4 w-5 h-5 text-slate-400 pointer-events-none" />
          <input
            id="standards-search-input"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter product description in English, Hindi (हिंदी) or Hinglish (e.g. 'कृषि के लिए सबमर्सिबल पानी का पंप')..."
            className="w-full pl-12 pr-32 py-3 bg-slate-50 border border-slate-300 rounded-md text-slate-900 placeholder-slate-500 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-govnavy-800 focus:border-govnavy-800 transition-all"
            disabled={isLoading}
          />
          
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="absolute right-32 p-1 text-slate-400 hover:text-slate-700 transition-colors"
              title="Clear input"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="absolute right-2 px-4 py-2 bg-govnavy-900 hover:bg-govnavy-800 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-semibold rounded transition-all flex items-center space-x-1.5 shadow-sm"
          >
            <Sparkles className="w-4 h-4 text-saffron-500" />
            <span>{isLoading ? 'Searching...' : 'Recommend'}</span>
          </button>
        </div>

        {/* Controls & Sample Prompt Chips */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs pt-1 border-t border-slate-100">
          
          {/* Example Chips */}
          <div className="flex items-center space-x-2 overflow-x-auto py-1 max-w-full">
            <span className="text-slate-500 font-semibold text-[11px] uppercase tracking-wider whitespace-nowrap">
              Example Queries:
            </span>
            <div className="flex space-x-2">
              {SAMPLE_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleChipClick(prompt)}
                  className="whitespace-nowrap px-2.5 py-1 rounded bg-slate-100 hover:bg-govnavy-50 hover:text-govnavy-900 hover:border-govnavy-300 text-slate-700 border border-slate-200 transition-colors text-[11px]"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          {/* Top-K Selector */}
          <div className="flex items-center space-x-2 shrink-0 bg-slate-50 px-3 py-1 rounded border border-slate-200">
            <SlidersHorizontal className="w-3.5 h-3.5 text-slate-500" />
            <label htmlFor="top-k-select" className="text-slate-600 text-xs">Results Count:</label>
            <select
              id="top-k-select"
              value={topK}
              onChange={handleTopKChange}
              className="bg-transparent text-slate-900 font-semibold focus:outline-none cursor-pointer text-xs"
            >
              <option value={3}>Top 3</option>
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
            </select>
          </div>

        </div>

      </form>
    </div>
  );
}
