import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export default function ErrorState({ error, onRetry }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start space-x-3 text-xs text-red-900 shadow-sm">
      <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
      <div className="flex-1">
        <span className="font-bold text-red-950 block mb-1">Backend Communication Error</span>
        <p className="leading-relaxed">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2.5 inline-flex items-center space-x-1.5 font-semibold px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded text-xs transition-colors shadow-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Search</span>
          </button>
        )}
      </div>
    </div>
  );
}
