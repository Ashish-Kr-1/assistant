import { useEffect, useRef, useState, useCallback } from "react"
import { useSearchParams } from "react-router-dom"
import styles from "./Assistant.module.css"
import TopNav from "../../components/TopNav/TopNav"
import SideNav from "../../components/SideNav/SideNav"
import FeatureStrip from "../../components/FeatureStrip/FeatureStrip"
import ContextBar from "../../components/Assistant/ContextBar"
import SearchComposer from "../../components/Assistant/SearchComposer"
import SuggestedQuestions from "../../components/Assistant/SuggestedQuestions"
import Stepper from "../../components/Assistant/Stepper"
import ChatThread from "../../components/Assistant/ChatThread"
import RightPanel from "../../components/Assistant/RightPanel"
import SectionPlaceholder from "../../components/Assistant/SectionPlaceholder"
import EscalateModal from "../../components/Assistant/EscalateModal"
import KnowledgeGraph from "../../components/Assistant/KnowledgeGraph"
import Icon from "../../components/Icons/IconSet"
import api from "../../api/axiosInstance"
import {
  mapCitationsToEvidence,
  mapConfidence,
  mapDeepResearchResponse,
  mapCaseStatusToStep,
} from "../../utils/mapQueryResponse"
import {
  initialConversation,
  recentQueryConversations,
  getDemoAnswer,
} from "../../demo"

// ── Helpers ───────────────────────────────────────────────────────────────────
function nowLabel() {
  const d = new Date()
  const h = d.getHours()
  const m = d.getMinutes().toString().padStart(2, "0")
  const period = h >= 12 ? "PM" : "AM"
  const h12 = h % 12 === 0 ? 12 : h % 12
  return `${h12}:${m} ${period}`
}

function makeId(prefix = "msg") {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 7)}`
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function Assistant({ initialSection }) {
  const [searchParams]                  = useSearchParams()
  const defaultSection                  = initialSection || searchParams.get("section") || "assistant"
  const [section, setSection]           = useState(defaultSection)

  useEffect(() => {
    if (initialSection) setSection(initialSection)
  }, [initialSection])
  const [jurisdiction, setJurisdiction] = useState("india")
  const [category, setCategory]         = useState("ayurvedic-formulation")
  const [language, setLanguage]         = useState("en")
  const [mode, setMode]                 = useState("query")          // "query" | "deep_research"
  const [heroDraft, setHeroDraft]       = useState("")
  const [followUpDraft, setFollowUpDraft] = useState("")
  const [messages, setMessages]         = useState(initialConversation)
  const [isTyping, setIsTyping]         = useState(false)
  const [usingDemoData, setUsingDemoData] = useState(false)
  const [activeRecentId, setActiveRecentId] = useState("rq-1")
  const [showEscalateModal, setShowEscalateModal] = useState(false)

  // Deep Research case tracking
  const [caseId, setCaseId]             = useState(null)
  const [caseStatus, setCaseStatus]     = useState(null)
  const [stepperStep, setStepperStep]   = useState(-1)

  const threadEndRef   = useRef(null)
  const isMountedRef   = useRef(true)
  const conversationIdRef = useRef(
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `conv-${Date.now()}-${Math.random().toString(16).slice(2)}`
  )

  useEffect(() => {
    isMountedRef.current = true
    return () => { isMountedRef.current = false }
  }, [])

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [messages, isTyping])

  // ── Mode switch: clear case context when going back to Query ──────────────
  function handleModeChange(next) {
    setMode(next)
    if (next === "query") {
      setCaseId(null)
      setCaseStatus(null)
      setStepperStep(-1)
    }
  }

  // ── Section routing ───────────────────────────────────────────────────────
  function handleSectionChange(next) {
    if (next?.startsWith("route-")) return
    setSection(next)
  }

  // ── Main send handler ─────────────────────────────────────────────────────
  const handleSend = useCallback(
    async (overrideText) => {
      const text = (overrideText ?? followUpDraft ?? heroDraft ?? "").trim()
      if (!text || isTyping) return

      setSection("assistant")
      setActiveRecentId(null)
      setHeroDraft("")
      setFollowUpDraft("")

      // Append the user message
      setMessages((prev) => [
        ...prev,
        { id: makeId("u"), role: "user", text, timeLabel: nowLabel() },
      ])
      setIsTyping(true)

      try {
        const payload = {
          query: text,
          jurisdiction,
          language,
          dpdp_consent: true,
          conversation_id: conversationIdRef.current,
          mode,
          formulation_category: category,
          // Pass case_id for continuing deep research dialog
          ...(caseId ? { case_id: caseId } : {}),
        }

        const { data } = await api.post("/query", payload)

        if (!isMountedRef.current) return
        setUsingDemoData(false)

        // ── Deep Research branch ──────────────────────────────────────────
        if (mode === "deep_research") {
          // Update case tracking state
          if (data.case_id)     setCaseId(data.case_id)
          if (data.case_status) {
            setCaseStatus(data.case_status)
            setStepperStep(mapCaseStatusToStep(data.case_status))
          }

          const msg = mapDeepResearchResponse(data, jurisdiction)
          setMessages((prev) => [...prev, { ...msg, isStreaming: true }])
          return
        }

        // ── Query branch ─────────────────────────────────────────────────
        setMessages((prev) => [
          ...prev,
          {
            id:               makeId("a"),
            role:             "assistant",
            isStreaming:      true,             // triggers typewriter in MessageBubble
            jurisdictionBadge: jurisdiction === "india" ? "INDIA" : "INTERNATIONAL",
            confidence:       mapConfidence(data.confidence_level),
            text:             data.answer || "I couldn't generate a confident answer for that just now.",
            evidence:         mapCitationsToEvidence(data.citations),
            relatedInsight:
              data.related_insight ||
              "You may also want to check if this is covered under TKDL or has been disclosed in prior art.",
            followUps:
              data.follow_up_questions?.slice(0, 3) || [
                "Can this be trademarked?",
                "What regulations apply here?",
                "Are there ABS obligations for export?",
              ],
          },
        ])
      } catch (_err) {
        // ── Graceful demo fallback ──────────────────────────────────────
        await new Promise((r) => setTimeout(r, 600))
        if (!isMountedRef.current) return
        setUsingDemoData(true)

        const demo = getDemoAnswer(text)
        setMessages((prev) => [
          ...prev,
          {
            id:               makeId("a"),
            role:             "assistant",
            isStreaming:      true,
            jurisdictionBadge: jurisdiction === "india" ? "INDIA" : demo.jurisdictionBadge,
            confidence:       demo.confidence,
            text:             demo.text,
            evidence:         demo.evidence,
            relatedInsight:   demo.relatedInsight,
            followUps:        demo.followUps,
          },
        ])
      } finally {
        if (isMountedRef.current) setIsTyping(false)
      }
    },
    [
      followUpDraft, heroDraft, isTyping,
      jurisdiction, language, mode, category, caseId,
    ]
  )

  function handleSelectRecentQuery(id) {
    setSection("assistant")
    setActiveRecentId(id)
    setMessages(recentQueryConversations[id] || initialConversation)
  }

  function handleResetContext() {
    setJurisdiction("india")
    setCategory("ayurvedic-formulation")
    setLanguage("en")
    setMode("query")
    setCaseId(null)
    setCaseStatus(null)
    setStepperStep(-1)
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className={`${styles.page} ${section === "knowledge-base" ? styles.widePage : ""}`}>
      <TopNav
        section={section}
        onSectionChange={handleSectionChange}
        language={language}
        onLanguageChange={setLanguage}
      />
      <SideNav section={section} onSectionChange={setSection} />

      <main className={styles.main}>
        {section === "assistant" ? (
          <>
            {/* Hero */}
            <div className={styles.hero}>
              <span className={styles.heroIcon}>
                <Icon name="leaf" size={20} />
              </span>
              <div style={{ flex: 1 }}>
                <h1>Charaka IP Assistant</h1>
                <p>
                  {mode === "deep_research"
                    ? "Describe your innovation — we'll guide you through a full IP & regulatory assessment."
                    : "Ask questions, get evidence-backed statutory guidance and citations."}
                </p>
              </div>
              <button
                type="button"
                className={styles.graphPillBtn}
                onClick={() => setSection("knowledge-base")}
                title="View IP Knowledge Graph"
              >
                <Icon name="network" size={14} />
                Knowledge Graph
              </button>
              {mode === "deep_research" && (
                <span className={styles.deepResearchBadge}>
                  <Icon name="search" size={13} />
                  Deep Research
                </span>
              )}
            </div>

            {/* Context Bar with mode toggle */}
            <ContextBar
              jurisdiction={jurisdiction}
              onJurisdictionChange={setJurisdiction}
              category={category}
              onCategoryChange={setCategory}
              language={language}
              onLanguageChange={setLanguage}
              onResetContext={handleResetContext}
              mode={mode}
              onModeChange={handleModeChange}
            />

            {/* Hero search */}
            <SearchComposer
              variant="hero"
              value={heroDraft}
              onChange={setHeroDraft}
              onSend={() => handleSend()}
              isTyping={isTyping}
              placeholder={
                mode === "deep_research"
                  ? "Describe your Ayurvedic innovation or formulation…"
                  : "Describe your IP or regulatory question…"
              }
              language={language}
            />

            <SuggestedQuestions onSelect={(q) => handleSend(q)} />

            {/* Stepper: shows query steps or live case progress */}
            <Stepper
              mode={mode}
              activeStep={stepperStep}
              caseId={caseId}
            />

            {/* Demo banner */}
            {usingDemoData && (
              <div className={styles.demoBanner}>
                <Icon name="info" size={13} />
                Backend unreachable — showing a demo answer so you can keep testing the flow.
              </div>
            )}

            {/* Chat thread */}
            <ChatThread
              messages={messages}
              isTyping={isTyping}
              onFollowUpClick={(q) => handleSend(q)}
              scrollRef={threadEndRef}
            />

            <div className={styles.disclaimer}>
              Educational &amp; guidance purposes only — does not constitute formal legal advice.
            </div>

            {/* Follow-up composer */}
            <SearchComposer
              variant="followup"
              value={followUpDraft}
              onChange={setFollowUpDraft}
              onSend={() => handleSend()}
              isTyping={isTyping}
              placeholder={
                mode === "deep_research" && caseId
                  ? "Reply to continue your case intake…"
                  : "Ask a follow-up question…"
              }
              language={language}
              onLanguageChange={setLanguage}
            />
          </>
        ) : section === "knowledge-base" ? (
          <KnowledgeGraph onOpenAssistant={() => setSection("assistant")} />
        ) : (
          <SectionPlaceholder section={section} onOpenAssistant={() => setSection("assistant")} />
        )}
      </main>

      {section !== "knowledge-base" && (
        <RightPanel
          onQuickAction={(q) => handleSend(q)}
          onSelectRecentQuery={handleSelectRecentQuery}
          activeRecentId={activeRecentId}
          onViewAllRecent={() => setSection("query-history")}
          onEscalate={() => setShowEscalateModal(true)}
          conversationId={conversationIdRef.current}
        />
      )}

      <FeatureStrip />

      {showEscalateModal && (
        <EscalateModal onClose={() => setShowEscalateModal(false)} />
      )}
    </div>
  )
}
