import React from 'react';
import { X, ExternalLink, ShieldCheck } from 'lucide-react';

export default function SourceViewerModal({ citation, onClose }) {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="glass-panel w-full max-w-2xl p-6 rounded-3xl border border-gold-500/40 shadow-2xl relative animate-scaleUp">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-full bg-slate-900 border border-slate-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center space-x-2 text-xs font-bold text-gold-400 uppercase tracking-wider mb-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Statutory Authority & Grounding Verification</span>
        </div>

        <h3 className="text-xl font-extrabold text-white mb-1">{citation.title}</h3>
        <p className="text-xs text-slate-400 mb-4">
          {citation.statute || citation.treaty} {citation.section ? `• ${citation.section}` : citation.article ? `• ${citation.article}` : ''}
        </p>

        <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 mb-6 space-y-3">
          <h5 className="text-xs font-bold text-slate-300 uppercase">Statutory Summary</h5>
          <p className="text-sm text-slate-200 leading-relaxed">{citation.summary}</p>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-slate-800 text-xs">
          <span className="text-slate-400">Jurisdiction: <strong className="text-white">{citation.jurisdiction}</strong></span>
          <a
            href={citation.official_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1 px-4 py-2 bg-ayurveda-700 hover:bg-ayurveda-600 text-gold-400 font-bold rounded-xl border border-gold-500/30 transition-colors"
          >
            <span>Open Official Registry Record</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
}
