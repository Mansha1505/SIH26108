import React, { useState } from 'react';
import { ShieldCheck, Lock, User, KeyRound, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react';
import { DEMO_AUTH_CONFIG } from '../config/authConfig';

export default function LoginPage({ onLoginSuccess }) {
  const [officerId, setOfficerId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    setTimeout(() => {
      const cleanId = officerId.trim();
      const cleanPass = password.trim();

      if (
        (cleanId.toLowerCase() === DEMO_AUTH_CONFIG.officerId.toLowerCase() || cleanId.toLowerCase() === 'admin' || cleanId.toLowerCase() === 'officer') &&
        (cleanPass === DEMO_AUTH_CONFIG.password || cleanPass === 'demo' || cleanPass === 'password')
      ) {
        sessionStorage.setItem(
          DEMO_AUTH_CONFIG.sessionKey,
          JSON.stringify({
            officerId: cleanId,
            loggedAt: new Date().toISOString(),
            role: 'Procurement Officer'
          })
        );
        onLoginSuccess();
      } else {
        setError(`Invalid Officer ID or Password. Demo Credentials — ID: ${DEMO_AUTH_CONFIG.officerId} | Pass: ${DEMO_AUTH_CONFIG.password}`);
      }
      setIsSubmitting(false);
    }, 300);
  };

  const handleFillDemo = () => {
    setOfficerId(DEMO_AUTH_CONFIG.officerId);
    setPassword(DEMO_AUTH_CONFIG.password);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-between font-sans text-slate-100 relative overflow-hidden">
      
      {/* Top Bar */}
      <header className="border-b border-slate-800 bg-slate-950/80 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded bg-govnavy-800 border border-saffron-500/40 flex items-center justify-center font-bold text-saffron-400 text-xs">
            BIS
          </div>
          <div>
            <h1 className="text-xs font-bold text-slate-100 uppercase tracking-wide">
              Government Procurement Standards Intelligence Engine
            </h1>
            <p className="text-[10px] text-slate-400 font-mono">
              SIH26108 Prototype Portal • Bureau of Indian Standards
            </p>
          </div>
        </div>
        <div className="hidden sm:flex items-center space-x-2 text-xs text-amber-400 bg-amber-500/10 px-3 py-1 rounded border border-amber-500/20">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Restricted Prototype Access</span>
        </div>
      </header>

      {/* Main Login Card Container */}
      <main className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-slate-950 border border-slate-800 rounded-xl p-8 shadow-2xl space-y-6 relative z-10">
          
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="w-12 h-12 bg-govnavy-900 border border-govnavy-700 rounded-full flex items-center justify-center mx-auto text-saffron-400 shadow-inner">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Procurement Officer Portal
            </h2>
            <p className="text-xs text-slate-400">
              Sign in with authorized officer credentials to access technical standards recommendations and tender intelligence.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-400 flex items-start space-x-2 animate-in fade-in">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {/* Officer ID Field */}
            <div className="space-y-1.5">
              <label htmlFor="officer-id-input" className="block text-xs font-semibold text-slate-300">
                Officer ID / Username
              </label>
              <div className="relative flex items-center">
                <User className="w-4 h-4 text-slate-500 absolute left-3 pointer-events-none" />
                <input
                  id="officer-id-input"
                  type="text"
                  required
                  value={officerId}
                  onChange={(e) => setOfficerId(e.target.value)}
                  placeholder="e.g. OFFICER-2026"
                  className="w-full pl-9 pr-3 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-saffron-500 focus:ring-1 focus:ring-saffron-500 transition-all font-mono"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1.5">
              <label htmlFor="officer-password-input" className="block text-xs font-semibold text-slate-300">
                Password
              </label>
              <div className="relative flex items-center">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 pointer-events-none" />
                <input
                  id="officer-password-input"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-3 py-2.5 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-saffron-500 focus:ring-1 focus:ring-saffron-500 transition-all"
                />
              </div>
            </div>

            {/* Sign In Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2.5 px-4 bg-saffron-600 hover:bg-saffron-500 text-slate-950 font-bold text-sm rounded-lg shadow-md hover:shadow-saffron-500/20 transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <span>{isSubmitting ? 'Authenticating...' : 'Sign In to Portal'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>

          </form>

          {/* Quick Demo Fill Helper */}
          <div className="pt-4 border-t border-slate-800 text-center space-y-2">
            <p className="text-[11px] text-slate-400">
              Evaluating prototype? Click below to auto-fill demo credentials:
            </p>
            <button
              type="button"
              onClick={handleFillDemo}
              className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-semibold rounded border border-slate-700 transition-colors inline-flex items-center space-x-1.5"
            >
              <KeyRound className="w-3.5 h-3.5 text-saffron-400" />
              <span>Fill Demo Credentials ({DEMO_AUTH_CONFIG.officerId})</span>
            </button>
          </div>

          <div className="text-[10px] text-slate-500 text-center font-mono">
            Notice: Demo frontend authentication gate for SIH26108 evaluation.
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950/80 px-6 py-3 text-center text-xs text-slate-400">
        SIH 2026 Problem Statement 108 • Automated Indian Standards Recommendation System
      </footer>

    </div>
  );
}
