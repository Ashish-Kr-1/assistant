import React, { useState } from 'react';
import { Calculator, CheckCircle, AlertCircle, ArrowRight } from 'lucide-react';

export default function ABSCalculator() {
  const [entityType, setEntityType] = useState('indian_company');
  const [turnover, setTurnover] = useState(25000000); // 2.5 Cr default
  const [isCultivated, setIsCultivated] = useState(true);
  const [isExport, setIsExport] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCalculate = async () => {
    setLoading(true);
    try {
      const url = `/api/v1/abs/calculate?entity_type=${entityType}&annual_turnover_inr=${turnover}&is_cultivated_species=${isCultivated}&is_export=${isExport}`;
      const res = await fetch(url);
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="glass-panel p-6 rounded-3xl border border-gold-500/30">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 rounded-xl bg-ayurveda-800 text-gold-400">
            <Calculator className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Access & Benefit-Sharing (ABS) Duty Helper</h2>
            <p className="text-xs text-slate-400">
              Biological Diversity Act 2002 (amended 2023) & 2024 Rules compliance calculator.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Entity Type Selection */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300">Entity Category</label>
            <select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 text-white rounded-xl p-3 text-xs focus:outline-none focus:border-gold-500"
            >
              <option value="ayush_practitioner">Registered AYUSH Practitioner / Vaidya</option>
              <option value="indian_individual">Indian Individual / Micro Cultivator</option>
              <option value="indian_company">Indian Commercial Enterprise / MSME</option>
              <option value="foreign_entity">Foreign Entity / NRI / Foreign Collaboration</option>
            </select>
          </div>

          {/* Turnover Input */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-300">Annual Product Turnover (INR ₹)</label>
            <input
              type="number"
              value={turnover}
              onChange={(e) => setTurnover(Number(e.target.value))}
              className="w-full bg-slate-900 border border-slate-700 text-white rounded-xl p-3 text-xs focus:outline-none focus:border-gold-500"
            />
          </div>

          {/* Checkboxes */}
          <div className="flex items-center space-x-3 glass-card p-3 rounded-xl">
            <input
              type="checkbox"
              checked={isCultivated}
              onChange={(e) => setIsCultivated(e.target.checked)}
              className="w-4 h-4 accent-emerald-500 rounded cursor-pointer"
            />
            <span className="text-xs text-slate-200">Cultivated Biological Resource (Exempt if domestic)</span>
          </div>

          <div className="flex items-center space-x-3 glass-card p-3 rounded-xl">
            <input
              type="checkbox"
              checked={isExport}
              onChange={(e) => setIsExport(e.target.checked)}
              className="w-4 h-4 accent-emerald-500 rounded cursor-pointer"
            />
            <span className="text-xs text-slate-200">Export of Biological Resource / Foreign IPR</span>
          </div>
        </div>

        <button
          onClick={handleCalculate}
          disabled={loading}
          className="w-full py-3 bg-gradient-to-r from-ayurveda-700 to-ayurveda-900 hover:from-ayurveda-600 hover:to-ayurveda-800 text-gold-400 font-bold text-sm rounded-xl border border-gold-500/40 shadow-lg flex items-center justify-center space-x-2 transition-all"
        >
          <span>{loading ? 'Calculating ABS Duties...' : 'Calculate Benefit-Sharing Slab & Required NBA Forms'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>

        {result && (
          <div className="mt-6 p-6 rounded-2xl glass-card border border-gold-500/40 space-y-4 animate-fadeIn">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                {result.abs_required ? (
                  <AlertCircle className="w-5 h-5 text-amber-400" />
                ) : (
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                )}
                <h4 className="text-sm font-bold text-white">
                  {result.abs_required ? 'ABS Compliance Mandatory' : 'Monetary ABS Exempt'}
                </h4>
              </div>
              <span className="px-3 py-1 bg-slate-900 text-gold-400 text-xs font-mono font-bold rounded-lg border border-gold-500/30">
                Fee Slab: {result.benefit_sharing_fee_percentage}%
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">{result.summary}</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1 font-semibold">Required Regulatory Form:</span>
                <strong className="text-gold-400">{result.nba_form_required}</strong>
              </div>

              <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                <span className="text-slate-400 block mb-1 font-semibold">Compliance Action:</span>
                <strong className="text-emerald-300">{result.compliance_action}</strong>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
