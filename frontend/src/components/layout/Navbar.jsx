import React from 'react';
import {
  LayoutDashboard,
  Search,
  FileText,
  BookmarkCheck,
  GitFork,
  History,
  Award,
  BarChart3
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'search', label: 'Standards Search', icon: Search, badge: 'Active' },
  { id: 'tender-analyzer', label: 'Tender Analyzer', icon: FileText, badge: 'PDF' },
  { id: 'recommendations', label: 'Recommendations', icon: BookmarkCheck },
  { id: 'network', label: 'Standards Network', icon: GitFork },
  { id: 'amendments', label: 'Version & Amendments', icon: History },
  { id: 'certification', label: 'Certification', icon: Award },
  { id: 'reports', label: 'Reports', icon: BarChart3 },
];

export default function Navbar({ activeTab, setActiveTab }) {
  return (
    <nav className="bg-govnavy-950 border-b border-govnavy-800 text-slate-300 text-xs font-medium sticky top-[61px] z-30 shadow-inner overflow-x-auto scrollbar-none">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center space-x-2 py-3 px-3.5 border-b-2 transition-all whitespace-nowrap ${
                isActive
                  ? 'border-saffron-500 text-white font-semibold bg-govnavy-900/90'
                  : 'border-transparent text-slate-300 hover:text-white hover:bg-govnavy-900/50'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-saffron-500' : 'text-slate-400'}`} />
              <span>{item.label}</span>
              {item.badge && (
                <span
                  className={`text-[10px] font-bold px-1.5 py-0.2 rounded font-mono ${
                    item.badge === 'Active'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-slate-800 text-slate-300 border border-slate-700'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
