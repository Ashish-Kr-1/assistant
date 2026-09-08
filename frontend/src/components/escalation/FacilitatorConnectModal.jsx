import React, { useState } from 'react';
import { X, UserCheck, Send, CheckCircle2 } from 'lucide-react';

export default function FacilitatorConnectModal({ onClose }) {
  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    user_name: '',
    user_email: '',
    user_phone: '',
    query_summary: 'Complex Ayurvedic Patent Application under Section 3(p) & NBA Approval',
    formulation_category: 'Proprietary Ayurvedic Medicine'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await fetch('/api/v1/escalation/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      setSubmitted(true);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="glass-panel w-full max-w-lg p-6 rounded-3xl border border-gold-500/40 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white rounded-full bg-slate-900 border border-slate-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center space-x-2 text-gold-400 mb-2">
          <UserCheck className="w-5 h-5 text-emerald-400" />
          <h3 className="text-lg font-bold text-white">Escalate to Registered IP Facilitator</h3>
        </div>
        <p className="text-xs text-slate-400 mb-4">
          Connect with certified Patent Agents and AYUSH regulatory attorneys for formal legal representation.
        </p>

        {!submitted ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Full Name</label>
              <input
                type="text"
                required
                value={formData.user_name}
                onChange={(e) => setFormData({ ...formData, user_name: e.target.value })}
                placeholder="Dr. Rajesh Vaidya"
                className="w-full bg-slate-900 border border-slate-700 text-white rounded-xl p-3 text-xs focus:outline-none focus:border-gold-500"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Email Address</label>
              <input
                type="email"
                required
                value={formData.user_email}
                onChange={(e) => setFormData({ ...formData, user_email: e.target.value })}
                placeholder="rajesh@ayushstartup.in"
                className="w-full bg-slate-900 border border-slate-700 text-white rounded-xl p-3 text-xs focus:outline-none focus:border-gold-500"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Phone Number</label>
              <input
                type="tel"
                required
                value={formData.user_phone}
                onChange={(e) => setFormData({ ...formData, user_phone: e.target.value })}
                placeholder="+91 98765 43210"
                className="w-full bg-slate-900 border border-slate-700 text-white rounded-xl p-3 text-xs focus:outline-none focus:border-gold-500"
              />
            </div>

            <button
              type="submit"
              className="w-full py-3 bg-gradient-to-r from-ayurveda-700 to-ayurveda-900 hover:from-ayurveda-600 hover:to-ayurveda-800 text-gold-400 font-bold text-xs rounded-xl border border-gold-500/40 shadow-lg flex items-center justify-center space-x-2 transition-all"
            >
              <span>Submit Facilitator Match Request</span>
              <Send className="w-4 h-4" />
            </button>
          </form>
        ) : (
          <div className="text-center py-8 space-y-4">
            <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
            <h4 className="text-lg font-bold text-white">Escalation Request Received!</h4>
            <p className="text-xs text-slate-300">
              Reference Ticket ID: <code className="text-gold-400 font-mono font-bold">IP-SAKTI-2026-8942</code>
            </p>
            <p className="text-xs text-slate-400">
              A certified Patent Agent specializing in Ayurvedic traditional knowledge defense will contact you within 24 hours.
            </p>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-slate-800 text-xs font-bold text-white rounded-xl"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
