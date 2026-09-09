import React from 'react';
import { Search, Sparkles, X, SlidersHorizontal } from 'lucide-react';

const SAMPLE_PROMPTS = [
  "50W LED street light for outdoor municipal roads",
  "Portland Slag Cement for structural foundation work",
  "Submersible pump set for agricultural water supply",
  "Crosslinked polyethylene XLPE insulated power cables 1100V",
  "High Density Polyethylene (HDPE) pipes for water supply",
  "Crystalline Silicon PV Modules for solar power plant",
];

export default function SearchBar({ query, setQuery, topK, setTopK, onSearch, isLoading }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query, topK);
    }
  };

  const handleChipClick = (prompt) => {
    setQuery(prompt);
    onSearch(prompt, topK);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl mb-8">
      <form onSubmit={handleSubmit} className="space-y-4">
        
        {/* Search Input Box */}
        <div className="relative flex items-center">
          <Search className="absolute left-4 w-5 h-5 text-slate-400 pointer-events-none" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Describe your product requirement or tender specification (e.g., '50W LED street light for outdoor municipal roads')..."
            className="w-full pl-12 pr-28 py-3.5 bg-slate-950 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-all shadow-inner"
            disabled={isLoading}
          />
          
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="absolute right-28 p-1 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="absolute right-2.5 px-4 py-2 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-semibold rounded-lg transition-all duration-200 flex items-center space-x-1.5 shadow-md shadow-brand-600/30"
          >
            <Sparkles className="w-4 h-4" />
            <span>{isLoading ? 'Searching...' : 'Recommend'}</span>
          </button>
        </div>

        {/* Controls & Sample Chips */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs pt-1">
          
          {/* Sample Prompts */}
          <div className="flex items-center space-x-2 overflow-x-auto py-1 max-w-full">
            <span className="text-slate-400 whitespace-nowrap font-medium text-[11px] uppercase tracking-wider">
              Try examples:
            </span>
            <div className="flex space-x-2">
              {SAMPLE_PROMPTS.map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleChipClick(prompt)}
                  className="whitespace-nowrap px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 hover:text-brand-300 text-slate-300 border border-slate-700/60 transition-colors text-[11px]"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          {/* Top-K Selector */}
          <div className="flex items-center space-x-2 shrink-0 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
            <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
            <label className="text-slate-400 text-xs">Top Results:</label>
            <select
              value={topK}
              onChange={(e) => setTopK(e.target.value)}
              className="bg-transparent text-slate-200 font-semibold focus:outline-none cursor-pointer text-xs"
            >
              <option value="3" className="bg-slate-900">Top 3</option>
              <option value="5" className="bg-slate-900">Top 5</option>
              <option value="10" className="bg-slate-900">Top 10</option>
            </select>
          </div>

        </div>

      </form>
    </div>
  );
}
