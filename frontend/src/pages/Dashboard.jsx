import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import DisclaimerBanner from '../components/DisclaimerBanner';
import SearchBar from '../components/SearchBar';
import RecommendationList from '../components/RecommendationList';
import LoadingSkeleton from '../components/LoadingSkeleton';
import DetailModal from '../components/DetailModal';
import { recommendStandards, checkHealth } from '../services/api';
import { AlertCircle, SearchX, RefreshCw } from 'lucide-react';

export default function Dashboard() {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [responseData, setResponseData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedDetailItem, setSelectedDetailItem] = useState(null);
  const [healthInfo, setHealthInfo] = useState(null);

  useEffect(() => {
    // Fetch backend health & indexed standard count on initial load
    checkHealth()
      .then((data) => setHealthInfo(data))
      .catch((err) => console.warn('Could not reach backend health check endpoint:', err));
  }, []);

  const handleSearch = async (searchQuery, kVal) => {
    if (!searchQuery.trim()) return;
    setIsLoading(true);
    setError(null);

    try {
      const data = await recommendStandards(searchQuery, kVal);
      setResponseData(data);
    } catch (err) {
      console.error('Search error:', err);
      const msg = err.response?.data?.detail || err.message || 'Failed to fetch recommendations from backend server.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      <Header healthInfo={healthInfo} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <DisclaimerBanner />

        <SearchBar
          query={query}
          setQuery={setQuery}
          topK={topK}
          setTopK={setTopK}
          onSearch={handleSearch}
          isLoading={isLoading}
        />

        {/* Error State */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6 flex items-start space-x-3 text-xs text-red-200">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="font-semibold text-red-300 block mb-1">Backend Connection Error</span>
              <p>{error}</p>
              <button
                onClick={() => handleSearch(query, topK)}
                className="mt-2 inline-flex items-center space-x-1 font-semibold text-red-300 hover:text-red-100 underline"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry Search</span>
              </button>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && <LoadingSkeleton />}

        {/* Results State */}
        {!isLoading && responseData && (
          <RecommendationList
            responseData={responseData}
            onViewDetails={(item) => setSelectedDetailItem(item)}
          />
        )}

        {/* Empty State when no query executed yet */}
        {!isLoading && !responseData && !error && (
          <div className="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-12 text-center max-w-xl mx-auto space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-800/80 mx-auto flex items-center justify-center text-brand-400">
              <SearchX className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-slate-200">Ready to Analyze Procurement Requirements</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Enter a product or tender requirement query above (or click one of the example chips) to run hybrid BM25 and semantic vector retrieval against the local demo Indian Standards corpus.
            </p>
          </div>
        )}
      </main>

      {/* Specification Detail Modal */}
      {selectedDetailItem && (
        <DetailModal
          item={selectedDetailItem}
          onClose={() => setSelectedDetailItem(null)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-4 text-center text-xs text-slate-400">
        SIH26108 — Smart India Hackathon 2026 Problem Statement Solution MVP • AI-Assisted Recommendation Engine
      </footer>
    </div>
  );
}
