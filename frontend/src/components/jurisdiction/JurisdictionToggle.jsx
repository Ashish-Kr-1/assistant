import React from 'react';
import { Flag, Globe2 } from 'lucide-react';

export default function JurisdictionToggle({ jurisdiction, setJurisdiction }) {
  return (
    <div className="flex items-center justify-between glass-card p-3 rounded-2xl border border-slate-800">
      <div className="flex items-center space-x-2">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Explicit Regime Switch:
        </span>
      </div>

      <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
        <button
          type="button"
          onClick={() => setJurisdiction('national')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            jurisdiction === 'national'
              ? 'bg-ayurveda-800 text-gold-400 border border-gold-500/50 shadow-lg glow-emerald'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Flag className="w-4 h-4 text-emerald-400" />
          <span>NATIONAL (INDIA)</span>
        </button>

        <button
          type="button"
          onClick={() => setJurisdiction('international')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            jurisdiction === 'international'
              ? 'bg-indigo-950 text-indigo-300 border border-indigo-500/50 shadow-lg'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Globe2 className="w-4 h-4 text-indigo-400" />
          <span>INTERNATIONAL (WIPO / CBD)</span>
        </button>
      </div>

      <div className="hidden md:flex items-center space-x-2 text-xs text-slate-400">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span>
          Active Corpus:{' '}
          <strong className="text-white">
            {jurisdiction === 'national'
              ? 'Patents Act 2024 Rules, BDA 2023, D&C Act, FSSAI'
              : 'WIPO GRATK 2024, TRIPS, Nagoya Protocol, PCT'}
          </strong>
        </span>
      </div>
    </div>
  );
}
