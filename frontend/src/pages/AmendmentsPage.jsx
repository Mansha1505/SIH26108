import React, { useState, useEffect } from 'react';
import PageHeader from '../components/common/PageHeader';
import { History, Calendar, AlertCircle, Search, ShieldCheck, FileText, CheckCircle2, RefreshCw } from 'lucide-react';
import PrototypeDisclaimer from '../components/common/PrototypeDisclaimer';
import { getStandardsAmendments } from '../services/api';

export default function AmendmentsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchAmendments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getStandardsAmendments();
      setData(res);
    } catch (err) {
      console.error('Failed to load standards amendment intelligence:', err);
      setError(err.message || 'Failed to connect to backend service');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAmendments();
  }, []);

  const filteredItems = (data?.items || []).filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.is_number.toLowerCase().includes(q) ||
      item.summary.toLowerCase().includes(q) ||
      item.version_status.toLowerCase().includes(q) ||
      (item.amendment_history || []).some(
        (amd) =>
          amd.title.toLowerCase().includes(q) ||
          String(amd.year).includes(q) ||
          String(amd.amendment_number).includes(q)
      )
    );
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <PageHeader
        title="Version & Amendments Intelligence"
        subtitle="Track historical revisions, active amendments, and standard designations to ensure procurement specifications cite active technical standards."
        badgeText="Deterministic Metadata Module"
      />

      <PrototypeDisclaimer />

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex items-center space-x-3">
          <div className="p-3 bg-govnavy-50 rounded-lg text-govnavy-800">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Indexed Demo Standards
            </span>
            <span className="text-xl font-bold font-mono text-slate-900">
              {loading ? '...' : data?.total_standards || 0}
            </span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex items-center space-x-3">
          <div className="p-3 bg-amber-50 rounded-lg text-amber-700">
            <History className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Standards With Recorded Amds
            </span>
            <span className="text-xl font-bold font-mono text-amber-900">
              {loading ? '...' : data?.standards_with_amendments || 0}
            </span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex items-center space-x-3">
          <div className="p-3 bg-emerald-50 rounded-lg text-emerald-700">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Corpus Verification Status
            </span>
            <span className="text-xs font-bold text-emerald-800 flex items-center space-x-1 mt-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Authoritative Verification Req.</span>
            </span>
          </div>
        </div>
      </div>

      {/* Main Content Box */}
      <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-3 text-govnavy-900">
            <History className="w-6 h-6 text-govnavy-800 shrink-0" />
            <div>
              <h2 className="text-base font-bold">Standard Revision & Amendment Registry</h2>
              <p className="text-xs text-slate-500">
                Deterministic version metadata derived from the curated sample standards corpus.
              </p>
            </div>
          </div>

          {/* Search Filter */}
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search designation or amd..."
              className="w-full text-xs pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded focus:bg-white focus:outline-none focus:ring-1 focus:ring-govnavy-800"
            />
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-500 text-xs flex flex-col items-center space-y-2">
            <RefreshCw className="w-6 h-6 animate-spin text-govnavy-800" />
            <span>Analyzing standard revision & amendment intelligence...</span>
          </div>
        ) : error ? (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded text-xs text-rose-800 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{error}</span>
            </div>
            <button
              onClick={fetchAmendments}
              className="px-3 py-1 bg-rose-100 hover:bg-rose-200 text-rose-900 rounded font-semibold transition-colors"
            >
              Retry
            </button>
          </div>
        ) : (
          <div className="border border-slate-200 rounded overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 border-b border-slate-200 text-slate-700 uppercase tracking-wider text-[10px] font-bold">
                <tr>
                  <th className="p-3">IS Designation</th>
                  <th className="p-3">Revision Year</th>
                  <th className="p-3">Recorded Amendments</th>
                  <th className="p-3">Corpus Version Status</th>
                  <th className="p-3">Verification Notice</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 font-sans text-slate-800">
                {filteredItems.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="p-6 text-center text-slate-500 text-xs">
                      No matching standards found for "{searchQuery}".
                    </td>
                  </tr>
                ) : (
                  filteredItems.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition-colors">
                      <td className="p-3">
                        <span className="font-mono font-bold text-govnavy-900 block">
                          {item.is_number}
                        </span>
                        <span className="text-[11px] text-slate-500 line-clamp-1">
                          {item.summary}
                        </span>
                      </td>

                      <td className="p-3 font-mono font-semibold text-slate-700">
                        {item.revision_year ? (
                          <span className="flex items-center space-x-1">
                            <Calendar className="w-3.5 h-3.5 text-slate-400" />
                            <span>{item.revision_year}</span>
                          </span>
                        ) : (
                          <span className="text-slate-400">N/A</span>
                        )}
                      </td>

                      <td className="p-3">
                        {item.has_amendments ? (
                          <div className="space-y-1">
                            {item.amendment_history.map((amd, aIdx) => (
                              <div
                                key={aIdx}
                                className="bg-amber-50 border border-amber-200 p-1.5 rounded text-[11px] text-amber-950 font-sans"
                              >
                                <span className="font-mono font-bold text-amber-900 mr-1.5">
                                  Amd. #{amd.amendment_number || 'N/A'} ({amd.year || 'N/A'}):
                                </span>
                                <span>{amd.title}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="text-slate-400 text-[11px] font-sans">
                            No recorded amendments in corpus
                          </span>
                        )}
                      </td>

                      <td className="p-3 font-semibold">
                        {item.version_status.includes('Superseded') ? (
                          <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200 text-[11px]">
                            {item.version_status}
                          </span>
                        ) : item.has_amendments ? (
                          <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-200 text-[11px]">
                            {item.version_status}
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-900 border border-emerald-200 text-[11px]">
                            {item.version_status}
                          </span>
                        )}
                      </td>

                      <td className="p-3 text-[11px] text-slate-500">
                        <span className="inline-flex items-center space-x-1 text-slate-600 font-medium">
                          <AlertCircle className="w-3 h-3 text-amber-600 shrink-0" />
                          <span>BIS Portal Check Req.</span>
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
