import React, { useState } from 'react';
import { HelpCircle, CheckCircle2, ShieldAlert, FileText, ArrowRight, RotateCcw } from 'lucide-react';

export default function ClassificationWizard() {
  const [formData, setFormData] = useState({
    is_in_first_schedule: false,
    uses_modified_ratio_or_novel_combo: false,
    is_standardized_extract: false,
    intended_for_food: false,
    intended_for_cosmetic: false,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleToggle = (key) => {
    setFormData((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleClassify = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/classify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      is_in_first_schedule: false,
      uses_modified_ratio_or_novel_combo: false,
      is_standardized_extract: false,
      intended_for_food: false,
      intended_for_cosmetic: false,
    });
    setResult(null);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="glass-panel p-6 rounded-3xl border border-gold-500/30">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 rounded-xl bg-ayurveda-800 text-gold-400">
            <HelpCircle className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Ayurvedic Formulation Classifier Wizard</h2>
            <p className="text-xs text-slate-400">
              Answer the clarifying questions below to determine regulatory category, IP bar posture (Section 3(p)), and ABS duties.
            </p>
          </div>
        </div>

        {!result ? (
          <div className="space-y-4">
            {/* Question 1 */}
            <div className="glass-card p-4 rounded-xl flex items-center justify-between">
              <div>
                <h4 className="text-sm font-semibold text-white">1. Authoritative Text Reference</h4>
                <p className="text-xs text-slate-400">Is formulation drawn directly from First Schedule authoritative texts (e.g. Charaka, Sharangadhara)?</p>
              </div>
              <input
                type="checkbox"
                checked={formData.is_in_first_schedule}
                onChange={() => handleToggle('is_in_first_schedule')}
                className="w-5 h-5 accent-emerald-500 rounded cursor-pointer"
              />
            </div>

            {/* Question 2 */}
            <div className="glass-card p-4 rounded-xl flex items-center justify-between">
              <div>
                <h4 className="text-sm font-semibold text-white">2. Novel Ratios / Ingredients</h4>
                <p className="text-xs text-slate-400">Does it use modified ingredient ratios, new combinations, or modern processing?</p>
              </div>
              <input
                type="checkbox"
                checked={formData.uses_modified_ratio_or_novel_combo}
                onChange={() => handleToggle('uses_modified_ratio_or_novel_combo')}
                className="w-5 h-5 accent-emerald-500 rounded cursor-pointer"
              />
            </div>

            {/* Question 3 */}
            <div className="glass-card p-4 rounded-xl flex items-center justify-between">
              <div>
                <h4 className="text-sm font-semibold text-white">3. Standardized Extract / Fraction</h4>
                <p className="text-xs text-slate-400">Is it a standardized active fraction extract with defined chemical marker compounds?</p>
              </div>
              <input
                type="checkbox"
                checked={formData.is_standardized_extract}
                onChange={() => handleToggle('is_standardized_extract')}
                className="w-5 h-5 accent-emerald-500 rounded cursor-pointer"
              />
            </div>

            {/* Question 4 */}
            <div className="glass-card p-4 rounded-xl flex items-center justify-between">
              <div>
                <h4 className="text-sm font-semibold text-white">4. Intended as Food / Supplement</h4>
                <p className="text-xs text-slate-400">Is the product intended as a dietary supplement or food product (Ayurveda-Aahar)?</p>
              </div>
              <input
                type="checkbox"
                checked={formData.intended_for_food}
                onChange={() => handleToggle('intended_for_food')}
                className="w-5 h-5 accent-emerald-500 rounded cursor-pointer"
              />
            </div>

            {/* Question 5 */}
            <div className="glass-card p-4 rounded-xl flex items-center justify-between">
              <div>
                <h4 className="text-sm font-semibold text-white">5. Intended as Cosmetic</h4>
                <p className="text-xs text-slate-400">Is it intended for beautification, skincare, or cosmetic use?</p>
              </div>
              <input
                type="checkbox"
                checked={formData.intended_for_cosmetic}
                onChange={() => handleToggle('intended_for_cosmetic')}
                className="w-5 h-5 accent-emerald-500 rounded cursor-pointer"
              />
            </div>

            <button
              onClick={handleClassify}
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-ayurveda-700 to-ayurveda-900 hover:from-ayurveda-600 hover:to-ayurveda-800 text-gold-400 font-bold text-sm rounded-xl border border-gold-500/40 shadow-lg glow-emerald flex items-center justify-center space-x-2 transition-all"
            >
              <span>{loading ? 'Evaluating Regulatory Framework...' : 'Evaluate Formulation Category & IP Posture'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Results Display Card */}
            <div className="glass-card p-6 rounded-2xl border border-gold-500/40 bg-slate-900/90">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
                <div>
                  <span className="text-xs text-gold-400 font-semibold uppercase tracking-wider">Classification Result</span>
                  <h3 className="text-xl font-bold text-white">{result.category_name}</h3>
                </div>
                <span className="px-3 py-1 bg-ayurveda-900 text-emerald-300 text-xs font-mono font-bold rounded-lg border border-emerald-500/30">
                  {result.category_code}
                </span>
              </div>

              <p className="text-sm text-slate-300 mb-6">{result.description}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
                  <div className="flex items-center space-x-2 text-gold-400 mb-2">
                    <FileText className="w-4 h-4" />
                    <h5 className="text-xs font-bold uppercase">Regulatory Regime</h5>
                  </div>
                  <p className="text-xs text-slate-300">{result.regulatory_framework}</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
                  <div className="flex items-center space-x-2 text-rose-400 mb-2">
                    <ShieldAlert className="w-4 h-4" />
                    <h5 className="text-xs font-bold uppercase">IP Posture & Sec 3(p) Bar</h5>
                  </div>
                  <p className="text-xs text-slate-300">{result.ip_posture}</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
                  <div className="flex items-center space-x-2 text-emerald-400 mb-2">
                    <CheckCircle2 className="w-4 h-4" />
                    <h5 className="text-xs font-bold uppercase">ABS Posture (BDA 2023)</h5>
                  </div>
                  <p className="text-xs text-slate-300">{result.abs_posture}</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
                  <div className="flex items-center space-x-2 text-indigo-400 mb-2">
                    <FileText className="w-4 h-4" />
                    <h5 className="text-xs font-bold uppercase">Required Dossier / Evidence</h5>
                  </div>
                  <p className="text-xs text-slate-300">{result.required_evidence}</p>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-800">
                <h5 className="text-xs font-bold text-white uppercase mb-2">Recommended Action Plan</h5>
                <ul className="list-disc list-inside text-xs text-slate-400 space-y-1">
                  {result.next_steps.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ul>
              </div>
            </div>

            <button
              onClick={resetForm}
              className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-xl flex items-center justify-center space-x-2 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Evaluate Another Formulation</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
