import React, { useState } from 'react';
import PageHeader from '../components/common/PageHeader';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  FileCheck,
  RefreshCw,
  Cpu,
  Layers,
  Sparkles,
  ShieldCheck,
  Tag,
  ListChecks,
  Table
} from 'lucide-react';
import PrototypeDisclaimer from '../components/common/PrototypeDisclaimer';
import { extractDocumentText, extractRequirements, analyzeGaps } from '../services/api';
import GapAnalysisPanel from '../components/search/GapAnalysisPanel';

export default function TenderAnalyzerPage({ onSearchWithExtractedText }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isProcessingFile, setIsProcessingFile] = useState(false);
  const [extractionResult, setExtractionResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [activePageTab, setActivePageTab] = useState('all');

  // Requirement Extraction & Gap Analysis State
  const [isExtractingReqs, setIsExtractingReqs] = useState(false);
  const [structuredReqs, setStructuredReqs] = useState(null);
  const [reqsError, setReqsError] = useState(null);

  const [gapAnalysisResult, setGapAnalysisResult] = useState(null);
  const [isAnalyzingGaps, setIsAnalyzingGaps] = useState(false);
  const [gapError, setGapError] = useState(null);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setErrorMsg("Invalid file format. Only PDF tender documents (.pdf) are supported.");
      return;
    }

    setErrorMsg(null);
    setSelectedFile(file);
    setIsProcessingFile(true);
    setExtractionResult(null);
    setStructuredReqs(null);
    setReqsError(null);
    setGapAnalysisResult(null);
    setGapError(null);

    try {
      const result = await extractDocumentText(file);
      setExtractionResult(result);
    } catch (err) {
      console.error('PDF extraction error:', err);
      const msg = err.response?.data?.detail || err.message || 'Failed to extract text from PDF document.';
      setErrorMsg(msg);
    } finally {
      setIsProcessingFile(false);
    }
  };

  const handleExtractRequirements = async () => {
    if (!extractionResult || !extractionResult.text) return;

    setIsExtractingReqs(true);
    setReqsError(null);

    try {
      const reqsData = await extractRequirements(
        extractionResult.text,
        extractionResult.filename
      );
      setStructuredReqs(reqsData);
      
      // Auto-run gap analysis
      try {
        setIsAnalyzingGaps(true);
        const q = reqsData.product?.name || extractionResult.text.slice(0, 180);
        const gapData = await analyzeGaps(q, 5, reqsData);
        setGapAnalysisResult(gapData);
      } catch (gErr) {
        console.error('Auto gap analysis error:', gErr);
      } finally {
        setIsAnalyzingGaps(false);
      }
    } catch (err) {
      console.error('Requirement extraction error:', err);
      const msg = err.response?.data?.detail || err.message || 'Failed to extract structured requirements from text.';
      setReqsError(msg);
    } finally {
      setIsExtractingReqs(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setIsProcessingFile(false);
    setExtractionResult(null);
    setStructuredReqs(null);
    setGapAnalysisResult(null);
    setErrorMsg(null);
    setReqsError(null);
    setGapError(null);
    setActivePageTab('all');
  };

  const getSuggestedSearchQuery = () => {
    if (structuredReqs) {
      const parts = [];
      if (structuredReqs.product?.name) parts.push(structuredReqs.product.name);
      if (structuredReqs.technical_requirements?.length) {
        parts.push(structuredReqs.technical_requirements.map(t => t.source_text).slice(0, 3).join(' '));
      }
      if (structuredReqs.standards_mentions?.length) {
        parts.push(structuredReqs.standards_mentions.join(' '));
      }
      return parts.join(' ').trim() || extractionResult.text.slice(0, 180);
    }
    
    if (extractionResult && extractionResult.text) {
      const snippet = extractionResult.text.replace(/--- Page \d+ ---/g, '').replace(/\n+/g, ' ').trim();
      return snippet.slice(0, 180);
    }
    return '';
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      
      <PageHeader
        title="Tender Document Processing & Requirement Extraction"
        subtitle="Upload tender PDFs to parse document text using PyMuPDF and automatically extract structured technical parameters, voltage, power, IS mentions, and safety clauses."
        badgeText="Deterministic Pattern Extraction"
      />

      <PrototypeDisclaimer />

      {/* PDF Upload Area */}
      {!selectedFile && (
        <div className="bg-white border-2 border-dashed border-slate-300 hover:border-govnavy-800 rounded-lg p-10 text-center transition-all shadow-sm">
          <div className="max-w-md mx-auto space-y-4">
            <div className="w-12 h-12 rounded-full bg-govnavy-50 text-govnavy-900 mx-auto flex items-center justify-center border border-govnavy-200">
              <UploadCloud className="w-6 h-6" />
            </div>

            <div>
              <h3 className="text-sm font-bold text-slate-900">Upload Tender / Technical Specification PDF</h3>
              <p className="text-xs text-slate-500 mt-1">Supported file format: <span className="font-semibold text-slate-700">PDF (.pdf)</span> up to 25 MB</p>
            </div>

            <div>
              <label
                htmlFor="tender-pdf-input"
                className="inline-flex items-center space-x-2 px-4 py-2 bg-govnavy-900 hover:bg-govnavy-800 text-white text-xs font-semibold rounded cursor-pointer transition-colors shadow-xs"
              >
                <FileText className="w-4 h-4 text-saffron-500" />
                <span>Select PDF Document</span>
              </label>
              <input
                id="tender-pdf-input"
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileChange}
                className="sr-only"
              />
            </div>
          </div>
        </div>
      )}

      {/* Upload Error */}
      {errorMsg && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-xs text-red-900 flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={handleReset} className="font-semibold text-red-950 underline shrink-0 ml-4">Try again</button>
        </div>
      )}

      {/* File Processing Spinner */}
      {selectedFile && isProcessingFile && (
        <div className="bg-white border border-slate-200 rounded-lg p-8 text-center space-y-4 shadow-sm max-w-lg mx-auto">
          <RefreshCw className="w-10 h-10 text-govnavy-800 mx-auto animate-spin" />
          <div>
            <h4 className="text-sm font-bold text-slate-900">Extracting Text from PDF with PyMuPDF</h4>
            <p className="text-xs text-slate-600 font-mono mt-1">{selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)</p>
          </div>
          <div className="text-[11px] text-slate-500">Parsing PDF pages & normalizing technical units...</div>
        </div>
      )}

      {/* PDF Extraction Results & Requirement Trigger */}
      {extractionResult && !isProcessingFile && (
        <div className="bg-white border border-slate-200 rounded-lg p-6 space-y-6 shadow-sm">
          
          {/* File Header */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4">
            <div className="flex items-center space-x-3">
              <FileCheck className="w-7 h-7 text-emerald-600 shrink-0" />
              <div>
                <h3 className="text-sm font-bold text-slate-900">{extractionResult.filename}</h3>
                <div className="flex flex-wrap items-center gap-2 mt-1 text-xs">
                  <span className="font-mono bg-govnavy-50 text-govnavy-900 border border-govnavy-200 px-2 py-0.5 rounded font-semibold text-[11px]">
                    Pages: {extractionResult.page_count}
                  </span>
                  <span className="font-mono bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded font-semibold text-[11px] flex items-center space-x-1">
                    <Cpu className="w-3 h-3 text-emerald-600" />
                    <span>Engine: {extractionResult.extraction_method}</span>
                  </span>
                  <span className="text-slate-500 text-[11px]">
                    Total Extracted Chars: {extractionResult.text.length}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={handleExtractRequirements}
                disabled={isExtractingReqs}
                className="px-4 py-2 bg-saffron-600 hover:bg-saffron-500 disabled:opacity-50 text-white font-bold text-xs rounded transition-colors flex items-center space-x-1.5 shadow-xs"
              >
                <Sparkles className="w-4 h-4" />
                <span>{isExtractingReqs ? 'Extracting...' : 'Extract Requirements'}</span>
              </button>

              <button
                onClick={handleReset}
                className="text-xs font-semibold text-slate-700 hover:text-slate-900 px-3 py-2 bg-slate-100 rounded border border-slate-300 transition-colors"
              >
                Upload Different PDF
              </button>
            </div>
          </div>

          {/* Warning Banner if present */}
          {extractionResult.warning && (
            <div className="bg-amber-50 border border-amber-200 p-3.5 rounded text-xs text-amber-900 flex items-start space-x-2.5">
              <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
              <div>
                <strong className="font-bold block mb-0.5">Extraction Notice:</strong>
                {extractionResult.warning}
              </div>
            </div>
          )}

          {/* Structured Requirements View if Extracted */}
          {structuredReqs && (
            <div className="bg-govnavy-50/60 border border-govnavy-200 rounded-lg p-5 space-y-5 animate-in fade-in duration-150">
              
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-govnavy-200 pb-3">
                <div className="flex items-center space-x-2">
                  <ListChecks className="w-5 h-5 text-govnavy-900" />
                  <h3 className="text-sm font-bold text-govnavy-950">Structured Technical Procurement Requirements</h3>
                </div>
                <span className="text-[11px] font-semibold bg-white border border-govnavy-200 text-govnavy-900 px-2.5 py-1 rounded">
                  Detected from Document
                </span>
              </div>

              {/* Product Info Badges */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-white p-3.5 rounded border border-govnavy-200">
                <div>
                  <span className="text-slate-500 text-[11px] block">Identified Product Name</span>
                  <span className="text-slate-900 font-bold">{structuredReqs.product?.name || 'Unspecified'}</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[11px] block">Product Domain Category</span>
                  <span className="text-govnavy-900 font-bold">{structuredReqs.product?.category || 'General Procurement'}</span>
                </div>
              </div>

              {/* Technical Requirements Table */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-govnavy-900 mb-2 flex items-center space-x-1.5">
                  <Table className="w-4 h-4 text-govnavy-800" />
                  <span>Technical Attributes Table ({structuredReqs.technical_requirements?.length || 0})</span>
                </h4>

                {structuredReqs.technical_requirements?.length > 0 ? (
                  <div className="border border-slate-200 rounded bg-white overflow-hidden shadow-xs">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-100 border-b border-slate-200 text-slate-700 uppercase tracking-wider text-[10px] font-bold">
                        <tr>
                          <th className="p-2.5">Attribute</th>
                          <th className="p-2.5">Value</th>
                          <th className="p-2.5">Unit</th>
                          <th className="p-2.5">Source Text Snippet</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200 font-sans text-slate-800">
                        {structuredReqs.technical_requirements.map((req, idx) => (
                          <tr key={idx} className="hover:bg-slate-50">
                            <td className="p-2.5 font-bold capitalize text-govnavy-900">{req.attribute}</td>
                            <td className="p-2.5 font-mono font-bold">{req.value}</td>
                            <td className="p-2.5 font-mono text-slate-600">{req.unit || '—'}</td>
                            <td className="p-2.5 font-mono text-slate-600 bg-slate-50/50">{req.source_text}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="bg-white border border-slate-200 p-4 rounded text-center text-xs text-slate-500">
                    No specific numeric technical parameters detected.
                  </div>
                )}
              </div>

              {/* IS Mentions */}
              {structuredReqs.standards_mentions?.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-govnavy-900 mb-2">
                    Detected Indian Standard Mentions:
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {structuredReqs.standards_mentions.map((isCode, idx) => (
                      <span key={idx} className="font-mono text-xs font-bold px-2.5 py-1 rounded bg-govnavy-900 text-white shadow-xs">
                        {isCode}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Safety Requirements */}
              {structuredReqs.safety_requirements?.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-govnavy-900 mb-2">
                    Safety & Protection Requirements:
                  </h4>
                  <div className="space-y-1">
                    {structuredReqs.safety_requirements.map((clause, idx) => (
                      <div key={idx} className="text-xs text-slate-800 bg-white p-2 rounded border border-slate-200 flex items-start space-x-2">
                        <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{clause}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Extracted Keywords */}
              {structuredReqs.keywords?.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-govnavy-900 mb-1.5">
                    Extracted Technical Keywords:
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {structuredReqs.keywords.map((kw, idx) => (
                      <span key={idx} className="text-xs px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200 font-mono">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Gap Analysis Panel */}
              <GapAnalysisPanel
                gapAnalysis={gapAnalysisResult}
                loading={isAnalyzingGaps}
                error={gapError}
              />

              {/* Quality Notice */}
              <div className="text-[11px] text-slate-500 italic pt-1 border-t border-govnavy-200">
                {structuredReqs.disclaimer}
              </div>

            </div>
          )}

          {/* Page Selector Tabs */}
          {extractionResult.pages && extractionResult.pages.length > 0 && (
            <div className="flex items-center space-x-2 border-b border-slate-200 pb-2 overflow-x-auto text-xs">
              <button
                onClick={() => setActivePageTab('all')}
                className={`px-3 py-1 rounded font-semibold transition-colors ${
                  activePageTab === 'all'
                    ? 'bg-govnavy-900 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                All Pages ({extractionResult.pages.length})
              </button>

              {extractionResult.pages.map((p) => (
                <button
                  key={p.page_number}
                  onClick={() => setActivePageTab(p.page_number)}
                  className={`px-3 py-1 rounded font-semibold transition-colors ${
                    activePageTab === p.page_number
                      ? 'bg-govnavy-900 text-white'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  Page {p.page_number} ({p.char_count} chars)
                </button>
              ))}
            </div>
          )}

          {/* Extracted Text Box */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-2 flex items-center space-x-1.5">
              <Layers className="w-4 h-4 text-govnavy-800" />
              <span>Extracted Raw Text Content</span>
            </h4>
            <pre className="text-xs font-mono text-slate-800 bg-slate-50 p-4 rounded border border-slate-200 max-h-80 overflow-y-auto whitespace-pre-wrap leading-relaxed">
              {activePageTab === 'all'
                ? extractionResult.text || 'No text extracted.'
                : extractionResult.pages.find((p) => p.page_number === activePageTab)?.text || 'Empty page.'}
            </pre>
          </div>

          {/* Action Trigger Button */}
          {extractionResult.text && (
            <div className="bg-govnavy-50 border border-govnavy-200 p-4 rounded flex flex-wrap items-center justify-between gap-3">
              <div>
                <span className="text-xs font-bold text-govnavy-950 block">Search Query derived from Extracted Requirements:</span>
                <p className="text-xs font-mono text-govnavy-900 italic line-clamp-1 mt-0.5">
                  "{getSuggestedSearchQuery()}"
                </p>
              </div>

              <button
                onClick={() => onSearchWithExtractedText(getSuggestedSearchQuery(), structuredReqs)}
                className="px-4 py-2 bg-saffron-600 hover:bg-saffron-500 text-white font-bold text-xs rounded transition-colors flex items-center space-x-1.5 shadow-xs shrink-0"
              >
                <span>Run Standards Recommendation Search</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

        </div>
      )}

    </div>
  );
}
