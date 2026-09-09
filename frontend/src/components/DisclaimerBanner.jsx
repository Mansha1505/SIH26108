import React from 'react';
import { AlertTriangle, Info } from 'lucide-react';

export default function DisclaimerBanner() {
  return (
    <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 mb-6 shadow-sm">
      <div className="flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-200/90 leading-relaxed">
          <span className="font-semibold text-amber-300 uppercase tracking-wide mr-1">
            Important System Positioning & Disclaimer:
          </span>
          This is an <strong>AI-assisted recommendation engine</strong> designed to assist procurement officers in discovering potentially applicable Indian Standards (IS/BIS).
          The relevance scores are statistical match indicators and do <strong>NOT</strong> constitute legal advice, statutory compliance guarantees, or official BIS certification validation.
          All loaded standards represent <strong>DEMO / SAMPLE DATA</strong>.
        </div>
      </div>
    </div>
  );
}
