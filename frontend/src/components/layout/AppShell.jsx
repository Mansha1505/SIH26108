import React from 'react';
import Header from './Header';
import Navbar from './Navbar';
import Footer from './Footer';

export default function AppShell({ activeTab, setActiveTab, healthInfo, children }) {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900">
      <Header healthInfo={healthInfo} />
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </main>
      <Footer />
    </div>
  );
}
