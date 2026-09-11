import React, { useState, useEffect } from 'react';
import AppShell from './components/layout/AppShell';
import DashboardPage from './pages/DashboardPage';
import SearchPage from './pages/SearchPage';
import TenderAnalyzerPage from './pages/TenderAnalyzerPage';
import NetworkPage from './pages/NetworkPage';
import AmendmentsPage from './pages/AmendmentsPage';
import CertificationPage from './pages/CertificationPage';
import ReportsPage from './pages/ReportsPage';
import LoginPage from './pages/LoginPage';
import { DEMO_AUTH_CONFIG } from './config/authConfig';
import { recommendStandards, recommendFromRequirements, checkHealth } from './services/api';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return Boolean(sessionStorage.getItem(DEMO_AUTH_CONFIG.sessionKey));
  });

  const [activeTab, setActiveTab] = useState('dashboard');
  const [healthInfo, setHealthInfo] = useState(null);

  // Recommendation search state
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [responseData, setResponseData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedDetailItem, setSelectedDetailItem] = useState(null);

  useEffect(() => {
    // Fetch backend health status & indexed standards count on app mount
    checkHealth()
      .then((data) => setHealthInfo(data))
      .catch((err) => console.warn('Could not reach backend health check endpoint:', err));
  }, []);

  const handleLogout = () => {
    sessionStorage.removeItem(DEMO_AUTH_CONFIG.sessionKey);
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  const handleSearch = async (searchQuery, kVal = topK) => {
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

  const handleNavigate = (tabId) => {
    setActiveTab(tabId);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectPrompt = (promptQuery) => {
    setQuery(promptQuery);
    setActiveTab('search');
    handleSearch(promptQuery, topK);
  };

  const handleSearchWithExtractedText = async (extractedQuery, structuredReqs = null) => {
    setQuery(extractedQuery);
    setActiveTab('search');
    setIsLoading(true);
    setError(null);

    try {
      let data;
      if (structuredReqs) {
        data = await recommendFromRequirements(structuredReqs, topK);
      } else {
        data = await recommendStandards(extractedQuery, topK);
      }
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
    <AppShell activeTab={activeTab} setActiveTab={setActiveTab} healthInfo={healthInfo} onLogout={handleLogout}>
      {activeTab === 'dashboard' && (
        <DashboardPage
          onNavigate={handleNavigate}
          onSelectPrompt={handleSelectPrompt}
          healthInfo={healthInfo}
        />
      )}

      {(activeTab === 'search' || activeTab === 'recommendations') && (
        <SearchPage
          query={query}
          setQuery={setQuery}
          topK={topK}
          setTopK={setTopK}
          onSearch={handleSearch}
          isLoading={isLoading}
          error={error}
          responseData={responseData}
          selectedDetailItem={selectedDetailItem}
          setSelectedDetailItem={setSelectedDetailItem}
        />
      )}

      {activeTab === 'tender-analyzer' && (
        <TenderAnalyzerPage
          onSearchWithExtractedText={handleSearchWithExtractedText}
        />
      )}

      {activeTab === 'network' && <NetworkPage />}
      {activeTab === 'amendments' && <AmendmentsPage />}
      {activeTab === 'certification' && <CertificationPage />}
      {activeTab === 'reports' && (
        <ReportsPage
          initialQuery={query}
          responseData={responseData}
        />
      )}
    </AppShell>
  );
}
