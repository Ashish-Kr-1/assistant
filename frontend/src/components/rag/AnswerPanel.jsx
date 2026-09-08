import React from 'react';
import { ShieldCheck, ExternalLink, Award, UserCheck, AlertTriangle } from 'lucide-react';

export default function AnswerPanel({ data, onOpenModal, onOpenEscalation }) {
  if (!data) return null;

  const isNational = data.jurisdiction === 'national';

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
      <div className={`glass-panel p-6 rounded-3xl border ${isNational ? 'border-emerald-500/40' : 'border-indigo-500/40'}`}>
        {/* Header & Badges */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
          <div className="flex items-center space-x-2">
            <span
              className={`px-3 py-1 text-xs font-bold rounded-lg uppercase tracking-wider ${
                isNational
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40'
                  : 'bg-indigo-950 text-indigo-300 border border-indigo-500/40'
              }`}
            >
              {data.jurisdiction.toUpperCase()} REGIME ANSWER
            </span>
            <span className="flex items-center space-x-1 px-2.5 py-1 bg-slate-900 text-gold-400 text-xs font-semibold rounded-lg border border-gold-500/20">
              <Award className="w-3.5 h-3.5" />
              <span>Grounding Confidence: {(data.confidence_score * 100).toFixed(0)}%</span>
            </span>
          </div>

          <button
            onClick={onOpenEscalation}
            className="flex items-center space-x-1 px-3 py-1.5 bg-ayurveda-900 hover:bg-ayurveda-800 text-gold-400 text-xs font-bold rounded-lg border border-gold-500/30 transition-colors"
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>Escalate to Human Facilitator</span>
          </button>
        </div>

        {/* Answer Content */}
        <div className="prose prose-invert max-w-none text-sm text-slate-200 leading-relaxed whitespace-pre-line mb-6">
          {data.answer}
        </div>

        {/* Statutory Citations Grid */}
        <div className="space-y-3 border-t border-slate-800 pt-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Mandatory Statutory & Legal Citations ({data.citations.length})
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {data.citations.map((cit, idx) => (
              <div key={idx} className="glass-card p-4 rounded-xl border border-slate-800 hover:border-gold-500/40 transition-all">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-gold-400">
                    {cit.statute || cit.treaty} {cit.section ? `• ${cit.section}` : cit.article ? `• ${cit.article}` : ''}
                  </span>
                  <button
                    onClick={() => onOpenModal(cit)}
                    className="p-1 text-slate-400 hover:text-white transition-colors"
                    title="View Statute Source Detail"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </button>
                </div>
                <h5 className="text-xs font-semibold text-white mb-1">{cit.title}</h5>
                <p className="text-xs text-slate-400 line-clamp-2">{cit.summary}</p>
              </div>
            ))}
          </div>
        </div>

        {/* DPDP Anonymization Footer */}
        <div className="mt-6 pt-4 border-t border-slate-900 flex items-center justify-between text-xs text-slate-500">
          <span className="flex items-center space-x-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
            <span>DPDP Audit Hash: <code className="text-slate-400 font-mono">{data.anonymized_audit_ref}</code></span>
          </span>
          <span>Zero PII Retained</span>
        </div>
      </div>
    </div>
  );
}
