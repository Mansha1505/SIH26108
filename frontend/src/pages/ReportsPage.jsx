import React, { useState } from 'react';
import PageHeader from '../components/common/PageHeader';
import PrototypeDisclaimer from '../components/common/PrototypeDisclaimer';
import { generateReport, downloadReportJson, downloadReportPdf } from '../services/api';
import {
  BarChart3,
  Download,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Sparkles,
  FileJson,
  FileText,
  Award,
  ShieldAlert,
  Search,
  Info,
  RefreshCw,
  ListChecks
} from 'lucide-react';

export default function ReportsPage({ initialQuery = '', responseData = null }) {
  const [query, setQuery] = useState(initialQuery || '50W LED street light outdoor municipal roads');
  const [topK, setTopK] = useState(5);
  const [reportData, setReportData] = useState(null);

  // UI state
  const [loading, setLoading] = useState(false);
  const [exportingJson, setExportingJson] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [error, setError] = useState(null);

  const isBusy = loading || exportingJson || exportingPdf;

  const handleGenerateReport = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a procurement specification query.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Extract requirements from responseData if available
      const reqs = responseData?.extracted_requirements || null;
      const docName = responseData?.extracted_requirements?.source_filename || null;
      const data = await generateReport(query.trim(), topK, reqs, docName);
      setReportData(data);
    } catch (err) {
      console.error('Report generation error:', err);
      const msg =
        err.response?.data?.detail ||
        err.message ||
        'Failed to generate procurement report from backend.';
      setError(msg);
    } fontally: {
      setLoading(false);
    }
  };

  const handleExportJson = async () => {
    if (!query.trim()) {
      setError('Please enter a procurement specification query.');
      return;
    }

    setExportingJson(true);
    setError(null);

    try {
      const reqs = responseData?.extracted_requirements || null;
      const docName = responseData?.extracted_requirements?.source_filename || null;
      await downloadReportJson(query.trim(), topK, reqs, docName);
    } catch (err) {
      console.error('JSON export error:', err);
      const msg =
        err.response?.data?.detail ||
        err.message ||
        'Failed to export JSON report from backend.';
      setError(msg);
    } finally {
      setExportingJson(false);
    }
  };

  const handleExportPdf = async () => {
    if (!query.trim()) {
      setError('Please enter a procurement specification query.');
      return;
    }

    setExportingPdf(true);
    setError(null);

    try {
      const reqs = responseData?.extracted_requirements || null;
      const docName = responseData?.extracted_requirements?.source_filename || null;
      await downloadReportPdf(query.trim(), topK, reqs, docName);
    } catch (err) {
      console.error('PDF export error:', err);
      const msg =
        err.response?.data?.detail ||
        err.message ||
        'Failed to export PDF report from backend.';
      setError(msg);
    } finally {
      setExportingPdf(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <PageHeader
        title="Procurement Compliance & Gap Analysis Reports"
        subtitle="Generate executive summary reports, standards compliance audit checklists, and tender specification gap analysis documentation."
        badgeText="Phase 10D / 11A Implemented Module"
      />

      <PrototypeDisclaimer />

      {/* Query & Control Bar */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-3 text-govnavy-900">
            <BarChart3 className="w-6 h-6 text-govnavy-800" />
            <div>
              <h2 className="text-base font-bold">Procurement Report Generator</h2>
              <p className="text-xs text-slate-500">
                Connected to backend Phase 10D report engine endpoints (/api/reports)
              </p>
            </div>
          </div>
          {initialQuery && (
            <span className="text-[11px] font-mono font-semibold px-2.5 py-1 rounded bg-amber-50 text-amber-900 border border-amber-200">
              Pre-filled from Active Search
            </span>
          )}
        </div>

        <form onSubmit={handleGenerateReport} className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Procurement Query / Requirement Specification
            </label>
            <div className="relative">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter tender specifications or procurement query..."
                className="w-full text-xs px-3 py-2.5 bg-slate-50 border border-slate-200 rounded focus:outline-none focus:border-govnavy-800 text-slate-800 font-mono"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
            <div className="flex items-center space-x-2">
              <label className="text-xs font-semibold text-slate-600">Top Standards (k):</label>
              <select
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value, 10))}
                className="py-1 px-2 text-xs bg-slate-50 border border-slate-200 rounded focus:outline-none focus:border-govnavy-800 text-slate-700"
              >
                <option value={3}>3 Standards</option>
                <option value={5}>5 Standards</option>
                <option value={10}>10 Standards</option>
              </select>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                type="submit"
                disabled={isBusy || !query.trim()}
                className="px-4 py-2 bg-govnavy-900 hover:bg-govnavy-950 text-white text-xs font-bold rounded transition-colors disabled:opacity-50 inline-flex items-center space-x-1.5 shadow-sm"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Generating Report...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5 text-saffron-400" />
                    <span>Generate Report</span>
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleExportJson}
                disabled={isBusy || !query.trim()}
                className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded border border-slate-300 transition-colors disabled:opacity-50 inline-flex items-center space-x-1.5"
              >
                {exportingJson ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Downloading JSON...</span>
                  </>
                ) : (
                  <>
                    <FileJson className="w-3.5 h-3.5 text-govnavy-800" />
                    <span>Export JSON</span>
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={handleExportPdf}
                disabled={isBusy || !query.trim()}
                className="px-3.5 py-2 bg-saffron-500 hover:bg-saffron-600 text-govnavy-950 text-xs font-bold rounded transition-colors disabled:opacity-50 inline-flex items-center space-x-1.5 shadow-sm"
              >
                {exportingPdf ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Downloading PDF...</span>
                  </>
                ) : (
                  <>
                    <Download className="w-3.5 h-3.5" />
                    <span>Export PDF</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Loading Indicator */}
      {loading && (
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-8 text-center text-slate-600 text-xs space-y-3 animate-in fade-in duration-150">
          <Loader2 className="w-6 h-6 animate-spin text-govnavy-800 mx-auto" />
          <p className="font-semibold text-slate-800">
            Assembling procurement recommendations, version intelligence, certification rules, and gap analysis...
          </p>
          <p className="text-slate-500 text-[11px]">
            Calling POST /api/reports/generate backend endpoint...
          </p>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800 text-xs flex items-start space-x-2 animate-in fade-in duration-150">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold block">Report Processing Notice</span>
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Functional Module Feature Cards (shown when no reportData generated yet) */}
      {!reportData && !loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-3 shadow-sm hover:border-govnavy-300 transition-colors">
            <h3 className="text-xs font-bold text-slate-900 flex items-center space-x-2 border-b border-slate-100 pb-2">
              <FileSpreadsheet className="w-4 h-4 text-govnavy-800" />
              <span>Standards Compliance Matrix Report</span>
            </h3>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              Export detailed structured JSON / PDF mapping tender requirements to primary Indian Standards (IS), version statuses, secondary test methods, and mandatory Quality Control Orders (QCOs).
            </p>
            <div className="pt-2 flex items-center space-x-2">
              <button
                onClick={handleGenerateReport}
                disabled={isBusy}
                className="px-3 py-1.5 bg-govnavy-900 hover:bg-govnavy-950 text-white text-xs font-semibold rounded transition-colors disabled:opacity-50 inline-flex items-center space-x-1"
              >
                <Sparkles className="w-3.5 h-3.5 text-saffron-400" />
                <span>Generate Report</span>
              </button>
              <button
                onClick={handleExportJson}
                disabled={isBusy}
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded border border-slate-300 transition-colors disabled:opacity-50 inline-flex items-center space-x-1"
              >
                <FileJson className="w-3.5 h-3.5 text-govnavy-800" />
                <span>Export JSON</span>
              </button>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-3 shadow-sm hover:border-govnavy-300 transition-colors">
            <h3 className="text-xs font-bold text-slate-900 flex items-center space-x-2 border-b border-slate-100 pb-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Tender Specification Gap Summary</span>
            </h3>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              Automated audit report highlighting outdated IS references (e.g. citing IS 10322:1982 instead of IS 10322:2012), missing surge protection clauses, and mandatory certification gaps.
            </p>
            <div className="pt-2 flex items-center space-x-2">
              <button
                onClick={handleExportPdf}
                disabled={isBusy}
                className="px-3 py-1.5 bg-saffron-500 hover:bg-saffron-600 text-govnavy-950 text-xs font-bold rounded transition-colors disabled:opacity-50 inline-flex items-center space-x-1"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export PDF</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Generated Report Preview Card */}
      {reportData && !loading && (
        <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm space-y-6 animate-in fade-in duration-200">
          {/* Report Metadata Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <span className="font-mono text-xs font-bold px-2.5 py-0.5 rounded bg-govnavy-900 text-white">
                  {reportData.metadata.report_id}
                </span>
                <span className="text-xs font-semibold text-slate-500">
                  {reportData.metadata.generated_at}
                </span>
              </div>
              <h3 className="text-base font-bold text-govnavy-950">
                {reportData.metadata.application_name}
              </h3>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={handleExportJson}
                disabled={isBusy}
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold rounded border border-slate-300 transition-colors inline-flex items-center space-x-1"
              >
                <FileJson className="w-3.5 h-3.5 text-govnavy-800" />
                <span>Export JSON</span>
              </button>

              <button
                onClick={handleExportPdf}
                disabled={isBusy}
                className="px-3 py-1.5 bg-saffron-500 hover:bg-saffron-600 text-govnavy-950 text-xs font-bold rounded transition-colors inline-flex items-center space-x-1"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export PDF</span>
              </button>
            </div>
          </div>

          {/* Input Requirement Summary */}
          <div className="bg-slate-50 border border-slate-200 rounded p-4 space-y-2 text-xs">
            <span className="font-bold text-govnavy-900 uppercase tracking-wider text-[11px] block">
              Evaluated Procurement Requirement
            </span>
            <p className="text-slate-800 font-mono bg-white p-2.5 rounded border border-slate-200">
              "{reportData.input_requirement.query || 'Tender specification document'}"
            </p>
            {reportData.input_requirement.uploaded_document_name && (
              <p className="text-[11px] text-slate-600">
                Source File: <span className="font-semibold">{reportData.input_requirement.uploaded_document_name}</span>
              </p>
            )}
          </div>

          {/* Recommended Standards Compliance Matrix */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-govnavy-950 flex items-center space-x-1.5 uppercase tracking-wider">
              <FileText className="w-4 h-4 text-govnavy-800" />
              <span>Recommended Indian Standards Matrix ({reportData.recommendations.length})</span>
            </h4>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-govnavy-900 text-white font-semibold text-[11px]">
                    <th className="p-2.5 rounded-l">IS Number</th>
                    <th className="p-2.5">Title</th>
                    <th className="p-2.5">Sector / Category</th>
                    <th className="p-2.5">Relevance</th>
                    <th className="p-2.5 rounded-r">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {reportData.recommendations.map((rec, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 text-slate-800">
                      <td className="p-2.5 font-mono font-bold text-govnavy-900">{rec.is_number}</td>
                      <td className="p-2.5 font-medium max-w-xs">{rec.title}</td>
                      <td className="p-2.5 text-slate-600">{rec.sector} / {rec.product_category}</td>
                      <td className="p-2.5 font-mono font-bold text-emerald-700">
                        {(rec.relevance_score * 100).toFixed(1)}%
                      </td>
                      <td className="p-2.5">
                        <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-100 text-emerald-900 border border-emerald-200">
                          {rec.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Certification Assessment Summary */}
          {reportData.certification_assessment && (
            <div className="bg-slate-50 border border-slate-200 rounded p-4 space-y-3 text-xs">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <span className="font-bold text-govnavy-900 flex items-center space-x-1.5">
                  <Award className="w-4 h-4 text-saffron-600" />
                  <span>Compulsory BIS Certification Assessment</span>
                </span>
                <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-govnavy-100 text-govnavy-900">
                  {reportData.certification_assessment.total_rules_matched} Rules Matched
                </span>
              </div>

              {reportData.certification_assessment.rules_matched &&
              reportData.certification_assessment.rules_matched.length > 0 ? (
                <div className="space-y-2">
                  {reportData.certification_assessment.rules_matched.map((rule, idx) => (
                    <div key={idx} className="bg-white p-2.5 rounded border border-slate-200 space-y-1">
                      <div className="flex justify-between font-semibold text-[11px]">
                        <span className="font-mono text-govnavy-900">{rule.rule_id}</span>
                        <span className="text-emerald-800">{rule.indication}</span>
                      </div>
                      <p className="text-[11px] text-slate-600">{rule.applicability_basis}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-slate-600">
                  No compulsory BIS certification rules triggered for the retrieved standards in prototype dataset.
                </p>
              )}
            </div>
          )}

          {/* Gap Analysis Summary */}
          {reportData.gap_analysis && (
            <div className="bg-slate-50 border border-slate-200 rounded p-4 space-y-3 text-xs">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <span className="font-bold text-govnavy-900 flex items-center space-x-1.5">
                  <ListChecks className="w-4 h-4 text-govnavy-800" />
                  <span>Specification Gap Analysis Overview</span>
                </span>
                <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-900">
                  {reportData.gap_analysis.covered_count} Covered / {reportData.gap_analysis.total_requirements} Total
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-[11px]">
                <div className="bg-emerald-50 border border-emerald-200 p-2 rounded">
                  <span className="block font-bold text-emerald-800 text-sm">
                    {reportData.gap_analysis.covered_count}
                  </span>
                  <span className="text-emerald-700">Covered</span>
                </div>
                <div className="bg-amber-50 border border-amber-200 p-2 rounded">
                  <span className="block font-bold text-amber-800 text-sm">
                    {reportData.gap_analysis.partially_covered_count}
                  </span>
                  <span className="text-amber-700">Partially Covered</span>
                </div>
                <div className="bg-rose-50 border border-rose-200 p-2 rounded">
                  <span className="block font-bold text-rose-800 text-sm">
                    {reportData.gap_analysis.not_evidenced_count}
                  </span>
                  <span className="text-rose-700">Not Evidenced</span>
                </div>
                <div className="bg-slate-100 border border-slate-200 p-2 rounded">
                  <span className="block font-bold text-slate-800 text-sm">
                    {reportData.gap_analysis.requires_verification_count}
                  </span>
                  <span className="text-slate-600">Needs Verification</span>
                </div>
              </div>

              <p className="text-[11px] text-slate-600 bg-white p-2.5 rounded border border-slate-200 leading-relaxed">
                {reportData.gap_analysis.coverage_summary}
              </p>
            </div>
          )}

          {/* Prototype Legal Disclaimer Notice */}
          <div className="bg-amber-50 border border-amber-200 rounded p-4 text-[11px] text-amber-900 space-y-1">
            <div className="flex items-center space-x-1.5 font-bold">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              <span>Prototype Disclaimer & Statutory Verification Notice</span>
            </div>
            <p className="leading-relaxed text-amber-800">{reportData.disclaimer}</p>
          </div>
        </div>
      )}
    </div>
  );
}
