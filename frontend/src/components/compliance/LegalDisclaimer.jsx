import React from 'react';
import { AlertOctagon } from 'lucide-react';

export default function LegalDisclaimer() {
  return (
    <footer className="glass-card border-t border-slate-900 px-4 py-4 mt-12 text-center text-xs text-slate-400">
      <div className="max-w-4xl mx-auto flex items-center justify-center space-x-2">
        <AlertOctagon className="w-4 h-4 text-gold-400 flex-shrink-0" />
        <p>
          <strong className="text-slate-300">Standing Disclaimer:</strong> IP-SAKTI Sahayak provides authoritative statutory information and regulatory guidance for research & educational purposes only. It does not constitute formal legal advice or create an attorney-client relationship.
        </p>
      </div>
    </footer>
  );
}
