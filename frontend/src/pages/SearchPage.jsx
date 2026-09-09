import React from 'react';
import PageHeader from '../components/common/PageHeader';
import SearchBar from '../components/search/SearchBar';
import RecommendationList from '../components/search/RecommendationList';
import LoadingSkeleton from '../components/search/LoadingSkeleton';
import ErrorState from '../components/search/ErrorState';
import EmptyState from '../components/search/EmptyState';
import DetailModal from '../components/search/DetailModal';
import PrototypeDisclaimer from '../components/common/PrototypeDisclaimer';

export default function SearchPage({
  query,
  setQuery,
  topK,
  setTopK,
  onSearch,
  isLoading,
  error,
  responseData,
  selectedDetailItem,
  setSelectedDetailItem
}) {
  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      
      <PageHeader
        title="Indian Standards Search & Recommendation"
        subtitle="Analyze technical product specifications against the Indian Standards corpus using BM25 lexical keyword matching and dense semantic vector similarities."
        badgeText="Working IR Engine"
      />

      <PrototypeDisclaimer />

      <SearchBar
        query={query}
        setQuery={setQuery}
        topK={topK}
        setTopK={setTopK}
        onSearch={onSearch}
        isLoading={isLoading}
      />

      {/* Error state */}
      {error && <ErrorState error={error} onRetry={() => onSearch(query, topK)} />}

      {/* Loading state */}
      {isLoading && <LoadingSkeleton />}

      {/* Results state */}
      {!isLoading && responseData && (
        <RecommendationList
          responseData={responseData}
          onViewDetails={(item) => setSelectedDetailItem(item)}
        />
      )}

      {/* Empty state when no search executed yet */}
      {!isLoading && !responseData && !error && (
        <EmptyState
          onSelectExample={(sampleQuery) => {
            setQuery(sampleQuery);
            onSearch(sampleQuery, topK);
          }}
        />
      )}

      {/* Detail modal popup */}
      {selectedDetailItem && (
        <DetailModal
          item={selectedDetailItem}
          onClose={() => setSelectedDetailItem(null)}
        />
      )}

    </div>
  );
}
