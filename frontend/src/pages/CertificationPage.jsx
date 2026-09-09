import React, { useState, useEffect } from 'react';
import PageHeader from '../components/common/PageHeader';
import PrototypeDisclaimer from '../components/common/PrototypeDisclaimer';
import { getCertificationRules, assessCertification } from '../services/api';
import {
  Award,
  CheckCircle2,
  ShieldCheck,
  Search,
  AlertTriangle,
  Info,
  RefreshCw,
  FileCheck,
  SlidersHorizontal,
  HelpCircle,
  ShieldAlert
} from 'lucide-react';

export default function CertificationPage() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [schemeFilter, setSchemeFilter] = useState('ALL');

  // Assessment tool state
  const [testStandardId, setTestStandardId] = useState('');
  const [testCategory, setTestCategory] = useState('');
  const [assessmentResult, setAssessmentResult] = useState(null);
  const [assessing, setAssessing] = useState(false);

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getCertificationRules();
      setRules(data.rules || []);
    } catch (err) {
      console.error('Failed to load certification rules:', err);
      setError('Unable to load certification rules dataset from backend server.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunAssessment = async (e) => {
    e.preventDefault();
    if (!testStandardId.trim() && !testCategory.trim()) return;

    setAssessing(true);
    try {
      const stdIds = testStandardId.trim() ? [testStandardId.trim()] : [];
      const cat = testCategory.trim() ? testCategory.trim() : null;
      const res = await assessCertification(stdIds, cat);
      setAssessmentResult(res);
    } catch (err) {
      console.error('Certification assessment failed:', err);
    } finally {
      setAssessing(false);
    }
  };

  // Filter rules
  const filteredRules = rules.filter((rule) => {
    const matchesSearch =
      searchTerm === '' ||
      rule.rule_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rule.product_category.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rule.certification_scheme.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rule.standard_ids.some((id) => id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      rule.notes.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesScheme =
      schemeFilter === 'ALL' || rule.certification_scheme === schemeFilter;

    return matchesSearch && matchesScheme;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <PageHeader
        title="Certification Rule Engine — SIH 2026 Prototype"
        subtitle="Deterministic rule-based mapping of Indian Standards and product categories to compulsory BIS certification schemes & Quality Control Orders (QCOs)."
        badgeText="Auditable Certification Layer"
      />

      <PrototypeDisclaimer />

      {/* Main Info Card */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-3 text-govnavy-900">
            <Award className="w-6 h-6 text-saffron-600" />
            <div>
              <h2 className="text-base font-bold">Compulsory BIS Certification Schemes</h2>
              <p className="text-xs text-slate-500">Deterministic rule dataset provenance & verification guidelines</p>
            </div>
          </div>
          <span className="text-[11px] font-mono font-bold px-2.5 py-1 rounded bg-govnavy-50 text-govnavy-900 border border-govnavy-200">
            {rules.length} Rules Loaded
          </span>
        </div>

        <p className="text-xs text-slate-700 leading-relaxed">
          Certain Indian Standards are subject to mandatory Quality Control Orders (QCOs) issued by Central Ministries. The Certification Rule Engine evaluates procurement requirements deterministically without AI/LLM hallucinations.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          <div className="bg-slate-50 border border-slate-200 rounded p-4 space-y-1.5">
            <h3 className="text-xs font-bold text-govnavy-950 flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Scheme-I: Mandatory Product Certification (ISI Mark)</span>
            </h3>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              Requires factory quality management evaluation, batch sample testing, and licensing before ISI Mark application (e.g. XLPE Cables IS 7098, HDPE Pipes IS 4984, Transformers IS 1180).
            </p>
          </div>

          <div className="bg-slate-50 border border-slate-200 rounded p-4 space-y-1.5">
            <h3 className="text-xs font-bold text-govnavy-950 flex items-center space-x-1.5">
              <CheckCircle2 className="w-4 h-4 text-govnavy-800" />
              <span>Scheme-II: Compulsory Registration Scheme (CRS)</span>
            </h3>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              Mandatory self-declaration of conformity based on testing in BIS-recognized labs prior to market placement (e.g. LED Lamps IS 16102, Solar Modules IS 14286).
            </p>
          </div>
        </div>
      </div>

      {/* Interactive Certification Assessment Tool */}
      <div className="bg-govnavy-900 text-white rounded-lg p-5 shadow-sm space-y-4">
        <div className="flex items-center space-x-2 border-b border-govnavy-700 pb-3">
          <FileCheck className="w-5 h-5 text-saffron-400" />
          <h3 className="text-sm font-bold">Interactive Certification Rule Matcher</h3>
        </div>

        <form onSubmit={handleRunAssessment} className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">
              Standard ID (e.g. IS 1180 Part 1 or IS-7098-P1)
            </label>
            <input
              type="text"
              value={testStandardId}
              onChange={(e) => setTestStandardId(e.target.value)}
              placeholder="e.g. IS-1180-P1"
              className="w-full text-xs px-3 py-2 bg-govnavy-950 border border-govnavy-700 rounded text-white focus:outline-none focus:border-saffron-400"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-300 mb-1">
              Product Category (e.g. Transformers, Cables)
            </label>
            <input
              type="text"
              value={testCategory}
              onChange={(e) => setTestCategory(e.target.value)}
              placeholder="e.g. Transformers"
              className="w-full text-xs px-3 py-2 bg-govnavy-950 border border-govnavy-700 rounded text-white focus:outline-none focus:border-saffron-400"
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={assessing || (!testStandardId.trim() && !testCategory.trim())}
              className="w-full py-2 px-4 bg-saffron-500 hover:bg-saffron-600 text-govnavy-950 font-bold text-xs rounded transition-colors disabled:opacity-50 flex items-center justify-center space-x-1.5"
            >
              {assessing ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Assessing...</span>
                </>
              ) : (
                <>
                  <Search className="w-3.5 h-3.5" />
                  <span>Assess Certification</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Assessment Result Output */}
        {assessmentResult && (
          <div className="bg-white text-slate-900 rounded p-4 text-xs space-y-3 animate-in fade-in duration-150">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2">
              <span className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                Deterministic Rule Assessment Output
              </span>
              <span className="text-[10px] text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-semibold">
                {assessmentResult.disclaimer}
              </span>
            </div>

            {assessmentResult.assessments && assessmentResult.assessments.length > 0 ? (
              <div className="space-y-3">
                {assessmentResult.assessments.map((item, idx) => (
                  <div key={idx} className="bg-slate-50 border border-slate-200 rounded p-3 space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-govnavy-900 text-white">
                          {item.rule_id}
                        </span>
                        <span className="font-semibold text-govnavy-900">{item.certification_scheme}</span>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-100 text-emerald-900 border border-emerald-200">
                        {item.indication}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px]">
                      <div>
                        <span className="text-slate-500">Applicability Basis: </span>
                        <span className="font-medium text-slate-800">{item.applicability_basis}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Source: </span>
                        <span className="font-medium text-slate-800">{item.source_reference} ({item.source_type})</span>
                      </div>
                    </div>

                    {item.notes && (
                      <p className="text-[11px] text-slate-600 bg-white p-2 rounded border border-slate-200">
                        {item.notes}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded text-slate-700 text-xs">
                No matching certification rules found for the requested criteria in prototype rule dataset.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Rules Dataset Explorer */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <h3 className="text-sm font-bold text-govnavy-900 flex items-center space-x-2">
            <SlidersHorizontal className="w-4 h-4 text-govnavy-800" />
            <span>Prototype Certification Rules Dataset</span>
          </h3>

          {/* Controls */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search rules..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded focus:outline-none focus:border-govnavy-800 w-44"
              />
            </div>

            <select
              value={schemeFilter}
              onChange={(e) => setSchemeFilter(e.target.value)}
              className="py-1.5 px-2.5 text-xs bg-slate-50 border border-slate-200 rounded focus:outline-none focus:border-govnavy-800 text-slate-700"
            >
              <option value="ALL">All Schemes</option>
              <option value="Scheme-I (ISI Mark)">Scheme-I (ISI Mark)</option>
              <option value="Scheme-II (CRS)">Scheme-II (CRS)</option>
            </select>

            <button
              onClick={fetchRules}
              className="p-1.5 bg-slate-100 hover:bg-slate-200 rounded border border-slate-300 transition-colors"
              title="Refresh Rules"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-slate-600 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Loading / Error / Content */}
        {loading ? (
          <div className="p-8 text-center text-slate-500 text-xs flex flex-col items-center space-y-2">
            <RefreshCw className="w-5 h-5 animate-spin text-govnavy-800" />
            <span>Loading prototype certification rules dataset...</span>
          </div>
        ) : error ? (
          <div className="p-4 bg-red-50 border border-red-200 rounded text-red-800 text-xs flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : filteredRules.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">
            No certification rules match the selected filter or search query.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredRules.map((rule) => (
              <div key={rule.rule_id} className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-3 hover:border-govnavy-300 transition-colors">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold px-2.5 py-0.5 rounded bg-govnavy-900 text-white">
                      {rule.rule_id}
                    </span>
                    <span className="text-xs font-bold text-slate-900">{rule.product_category}</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    {rule.scheme_status === 'requires_authoritative_verification' && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                        Transitioning
                      </span>
                    )}
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-200 font-mono">
                      {rule.certification_scheme}
                    </span>
                  </div>
                </div>

                {rule.applicable_order && (
                  <div className="bg-white p-2.5 rounded border border-slate-200 text-xs space-y-1">
                    <span className="text-[10px] font-bold text-slate-500 block uppercase tracking-wider">Applicable Order:</span>
                    <span className="font-semibold text-slate-900 block leading-tight">{rule.applicable_order}</span>
                    {(rule.order_date || rule.effective_date) && (
                      <div className="flex space-x-3 text-[10px] text-slate-600 font-mono pt-0.5">
                        {rule.order_date && <span>Notified: {rule.order_date}</span>}
                        {rule.effective_date && <span>Effective: {rule.effective_date}</span>}
                      </div>
                    )}
                    {rule.superseded_by && (
                      <div className="text-[10px] text-amber-900 font-semibold bg-amber-50 p-1.5 rounded border border-amber-200 mt-1">
                        ⚠️ Framework Transition: {rule.superseded_by}
                      </div>
                    )}
                  </div>
                )}

                <div className="space-y-1.5 text-xs text-slate-700">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-[11px] text-slate-500 shrink-0">Indication:</span>
                    <span className="font-semibold text-emerald-800 text-[11px] text-right">{rule.indication}</span>
                  </div>

                  <div className="flex items-start justify-between gap-2">
                    <span className="text-[11px] text-slate-500 shrink-0">Target Standards:</span>
                    <div className="flex flex-wrap justify-end gap-1">
                      {(rule.target_standard_ids || rule.standard_ids || []).map((id) => (
                        <span key={id} className="font-mono text-[10px] font-semibold px-1.5 py-0.5 rounded bg-white border border-slate-200 text-slate-800">
                          {id}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-start justify-between gap-2">
                    <span className="text-[11px] text-slate-500 shrink-0">Applicability Basis:</span>
                    <span className="text-[11px] text-slate-800 text-right">{rule.applicability_basis}</span>
                  </div>

                  <div className="flex items-start justify-between gap-2">
                    <span className="text-[11px] text-slate-500 shrink-0">Provenance / Source:</span>
                    <span className="text-[11px] text-slate-700 font-mono text-right">{rule.source_reference}</span>
                  </div>
                </div>

                {rule.notes && (
                  <p className="text-[11px] text-slate-600 bg-white p-2.5 rounded border border-slate-200 leading-relaxed">
                    <strong>Notes & Subtype Scope:</strong> {rule.notes}
                  </p>
                )}

                <div className="pt-2 border-t border-slate-200 flex items-center justify-between text-[10px] text-slate-500">
                  <span className="flex items-center space-x-1">
                    <ShieldAlert className="w-3 h-3 text-amber-600" />
                    <span>Verification Required: {rule.verification_required ? 'Yes' : 'No'}</span>
                  </span>
                  <span className="font-mono">Source Type: {rule.source_type}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

