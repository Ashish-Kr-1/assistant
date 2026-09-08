import React, { useState } from 'react';
import Header from './components/common/Header';
import JurisdictionToggle from './components/jurisdiction/JurisdictionToggle';
import SearchConsole from './components/rag/SearchConsole';
import AnswerPanel from './components/rag/AnswerPanel';
import ClassificationWizard from './components/classifier/ClassificationWizard';
import ABSCalculator from './components/abs/ABSCalculator';
import SourceViewerModal from './components/rag/SourceViewerModal';
import FacilitatorConnectModal from './components/escalation/FacilitatorConnectModal';
import LegalDisclaimer from './components/compliance/LegalDisclaimer';

export default function App() {
  const [activeTab, setActiveTab] = useState('search');
  const [jurisdiction, setJurisdiction] = useState('national'); // 'national' | 'international'
  const [selectedLang, setSelectedLang] = useState('en');
  const [queryResult, setQueryResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [showEscalation, setShowEscalation] = useState(false);

  const handleExecuteQuery = async (queryText) => {
    setLoading(true);
    setQueryResult(null);
    try {
      const res = await fetch('/api/v1/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: queryText,
          jurisdiction: jurisdiction,
          language: selectedLang,
          dpdp_consent: true
        })
      });
      const data = await res.json();
      setQueryResult(data);
    } catch (err) {
      console.error('Search query error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-between">
      <div>
        <Header
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          selectedLang={selectedLang}
          setSelectedLang={setSelectedLang}
        />

        <main className="max-w-7xl mx-auto px-4 lg:px-8 py-6 space-y-6">
          {/* Main Top Jurisdiction Switcher */}
          <JurisdictionToggle
            jurisdiction={jurisdiction}
            setJurisdiction={setJurisdiction}
          />

          {/* Main View Switching */}
          {activeTab === 'search' && (
            <div className="space-y-6">
              <SearchConsole
                onExecuteQuery={handleExecuteQuery}
                loading={loading}
                jurisdiction={jurisdiction}
              />
              <AnswerPanel
                data={queryResult}
                onOpenModal={(cit) => setSelectedCitation(cit)}
                onOpenEscalation={() => setShowEscalation(true)}
              />
            </div>
          )}

          {activeTab === 'classifier' && <ClassificationWizard />}

          {activeTab === 'abs' && <ABSCalculator />}
        </main>
      </div>

      {/* Modals */}
      {selectedCitation && (
        <SourceViewerModal
          citation={selectedCitation}
          onClose={() => setSelectedCitation(null)}
        />
      )}

      {showEscalation && (
        <FacilitatorConnectModal
          onClose={() => setShowEscalation(false)}
        />
      )}

      <LegalDisclaimer />
    </div>
  );
}
