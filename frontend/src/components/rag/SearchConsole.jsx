import React, { useState } from 'react';
import { Search, Mic, Sparkles, Send } from 'lucide-react';

export default function SearchConsole({ onExecuteQuery, loading, jurisdiction }) {
  const [query, setQuery] = useState('');

  const sampleQueries = [
    "Is Chyawanprash patentable under Indian law or barred by Section 3(p)?",
    "What are the ABS requirements for exporting standardized Curcumin extract?",
    "How does the 2024 WIPO GRATK Treaty mandate genetic resource disclosures in patents?",
    "What regulatory proof is required for a phytopharmaceutical drug under Rule 122E?"
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    onExecuteQuery(query);
  };

  return (
    <div className="space-y-4 max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="relative glass-panel p-2 rounded-2xl border border-gold-500/40 glow-emerald">
        <div className="flex items-center space-x-3 px-3">
          <Search className="w-5 h-5 text-gold-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Ask IPR, Patentability, Section 3(p), ABS, or Regulatory questions (${jurisdiction.toUpperCase()})...`}
            className="w-full bg-transparent text-slate-100 placeholder-slate-400 text-sm focus:outline-none py-3"
          />
          <button
            type="button"
            className="p-2 text-slate-400 hover:text-gold-400 transition-colors rounded-lg bg-slate-900/60"
            title="Bhashini Voice Input"
          >
            <Mic className="w-4 h-4" />
          </button>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-5 py-2.5 bg-gradient-to-r from-ayurveda-700 to-ayurveda-900 hover:from-ayurveda-600 hover:to-ayurveda-800 text-gold-400 font-bold text-xs rounded-xl border border-gold-500/40 shadow-lg flex items-center space-x-2 transition-all disabled:opacity-50"
          >
            {loading ? (
              <Sparkles className="w-4 h-4 animate-spin text-gold-400" />
            ) : (
              <>
                <span>Search</span>
                <Send className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Preset Queries */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs">
        <span className="text-slate-400 font-semibold whitespace-nowrap">Try asking:</span>
        {sampleQueries.map((q, idx) => (
          <button
            key={idx}
            onClick={() => {
              setQuery(q);
              onExecuteQuery(q);
            }}
            className="whitespace-nowrap px-3 py-1 bg-slate-900/80 hover:bg-slate-800 text-slate-300 rounded-full border border-slate-800 text-xs transition-colors"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
