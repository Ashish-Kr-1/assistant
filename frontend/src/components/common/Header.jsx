import React from 'react';
import { ShieldCheck, Scale, Globe, BookOpen } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, selectedLang, setSelectedLang }) {
  const languages = [
    { code: 'en', label: 'English' },
    { code: 'hi', label: 'हिंदी (Hindi)' },
    { code: 'ta', label: 'தமிழ் (Tamil)' },
    { code: 'te', label: 'తెలుగు (Telugu)' },
    { code: 'gu', label: 'ગુજરાતી (Gujarati)' },
    { code: 'mr', label: 'मराठी (Marathi)' }
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-gold-500/20 px-4 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand Logo & Name */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-ayurveda-900 via-ayurveda-700 to-gold-500 flex items-center justify-center shadow-lg border border-gold-500/40">
            <ShieldCheck className="w-6 h-6 text-gold-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-extrabold tracking-tight text-white font-sans">
                IP-SAKTI <span className="text-gold-500">Sahayak</span>
              </h1>
              <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-ayurveda-900/80 text-gold-400 border border-gold-500/30">
                PS045 RAG-AI
              </span>
            </div>
            <p className="text-xs text-slate-400">Ayurveda IPR & Regulatory Intelligence Engine</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('search')}
            className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === 'search'
                ? 'bg-ayurveda-700 text-white shadow-md border border-gold-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            IPR RAG Search
          </button>
          <button
            onClick={() => setActiveTab('classifier')}
            className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === 'classifier'
                ? 'bg-ayurveda-700 text-white shadow-md border border-gold-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Formulation Classifier
          </button>
          <button
            onClick={() => setActiveTab('abs')}
            className={`px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === 'abs'
                ? 'bg-ayurveda-700 text-white shadow-md border border-gold-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            ABS Duty Helper
          </button>
        </nav>

        {/* Bhashini Language Selector */}
        <div className="flex items-center space-x-2">
          <Globe className="w-4 h-4 text-gold-400" />
          <select
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
            className="bg-slate-900 text-slate-200 border border-slate-700 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-gold-500 transition-colors"
          >
            {languages.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </header>
  );
}
