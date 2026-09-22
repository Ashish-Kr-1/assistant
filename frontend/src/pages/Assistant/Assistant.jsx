import { useEffect, useRef, useState, useCallback } from "react"
import { useSearchParams } from "react-router-dom"
import styles from "./Assistant.module.css"
import TopNav from "../../components/TopNav/TopNav"
import SideNav from "../../components/SideNav/SideNav"
import FeatureStrip from "../../components/FeatureStrip/FeatureStrip"
import ContextBar from "../../components/Assistant/ContextBar"
import SearchComposer from "../../components/Assistant/SearchComposer"
import Stepper from "../../components/Assistant/Stepper"
import ChatThread from "../../components/Assistant/ChatThread"
import RightPanel from "../../components/Assistant/RightPanel"
import EscalateModal from "../../components/Assistant/EscalateModal"
import KnowledgeGraph from "../../components/Assistant/KnowledgeGraph"
import IPGuidance from "../../components/Assistant/IPGuidance"
import Icon from "../../components/Icons/IconSet"
import api from "../../api/axiosInstance"
import {
  mapCitationsToEvidence,
  mapConfidence,
  mapDeepResearchResponse,
  mapCaseStatusToStep,
} from "../../utils/mapQueryResponse"
import { quickActions } from "../../demo"

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

function generateUUID() {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `conv-${Date.now()}-${Math.random().toString(16).slice(2)}`
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
  const [mode, setMode]                 = useState("query") // "query" | "deep_research"
  const [heroDraft, setHeroDraft]       = useState("")
  const [followUpDraft, setFollowUpDraft] = useState("")
  const [messages, setMessages]         = useState([]) // Clean initial state
  const [isTyping, setIsTyping]         = useState(false)
  const [activeRecentId, setActiveRecentId] = useState(null)
  const [showEscalateModal, setShowEscalateModal] = useState(false)

  // Deep Research case tracking
  const [caseId, setCaseId]             = useState(null)
  const [caseStatus, setCaseStatus]     = useState(null)
  const [stepperStep, setStepperStep]   = useState(-1)

  const threadEndRef      = useRef(null)
  const isMountedRef      = useRef(true)
  const conversationIdRef = useRef(generateUUID())

  useEffect(() => {
    isMountedRef.current = true
    return () => { isMountedRef.current = false }
  }, [])

  useEffect(() => {
    if (messages.length > 0) {
      threadEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
    }
  }, [messages, isTyping])

  // ── Mode switch ───────────────────────────────────────────────────────────
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

  // ── New Chat ──────────────────────────────────────────────────────────────
  function handleNewChat() {
    setMessages([])
    setCaseId(null)
    setCaseStatus(null)
    setStepperStep(-1)
    setHeroDraft("")
    setFollowUpDraft("")
    setActiveRecentId(null)
    conversationIdRef.current = generateUUID()
    setSection("assistant")
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

      // Append user message
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
          ...(caseId ? { case_id: caseId } : {}),
        }

        const { data } = await api.post("/query", payload)

        if (!isMountedRef.current) return

        // ── Deep Research branch ──────────────────────────────────────────
        if (mode === "deep_research") {
          if (data.case_id)     setCaseId(data.case_id)
          if (data.case_status) {
            setCaseStatus(data.case_status)
            setStepperStep(mapCaseStatusToStep(data.case_status))
          }

          const msg = mapDeepResearchResponse(data, jurisdiction)
          setMessages((prev) => [...prev, { ...msg, isStreaming: true }])
          return
        }

        // ── Standard Query branch ─────────────────────────────────────────
        const answerText = data.answer || "No assessment was generated for this query."
        const confidenceLevel = mapConfidence(data.confidence_level)

        setMessages((prev) => [
          ...prev,
          {
            id:               makeId("a"),
            role:             "assistant",
            isStreaming:      true,
            jurisdictionBadge: jurisdiction === "india" ? "INDIA" : "INTERNATIONAL",
            confidence:       confidenceLevel,
            text:             answerText,
            evidence:         mapCitationsToEvidence(data.citations),
            relatedInsight:   data.related_insight,
            followUps:        data.follow_up_questions?.slice(0, 3) || [],
          },
        ])

        // Persist to local search history
        try {
          const raw = localStorage.getItem("ipsakti_recent_queries")
          const list = raw ? JSON.parse(raw) : []
          const entry = {
            id: `q-${Date.now()}`,
            question: text,
            timeLabel: nowLabel(),
            jurisdiction: jurisdiction === "india" ? "India" : "International",
            confidence: confidenceLevel,
          }
          const updated = [entry, ...list.filter((x) => x.question !== text).slice(0, 9)]
          localStorage.setItem("ipsakti_recent_queries", JSON.stringify(updated))
          window.dispatchEvent(new Event("ipsakti_history_updated"))
        } catch (_) {}
      } catch (err) {
        if (!isMountedRef.current) return
        const errMsg =
          err?.response?.data?.detail ||
          err?.message ||
          "Unable to complete query. Please check your connection to the analysis engine."

        setMessages((prev) => [
          ...prev,
          {
            id:          makeId("err"),
            role:        "assistant",
            isError:     true,
            failedQuery: text,
            text:        `Unable to process analysis: ${errMsg}`,
            timeLabel:   nowLabel(),
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

  function handleResetContext() {
    setJurisdiction("india")
    setCategory("ayurvedic-formulation")
    setLanguage("en")
    setMode("query")
    setCaseId(null)
    setCaseStatus(null)
    setStepperStep(-1)
  }

  const isWide = section === "knowledge-base" || section === "ip-guidance"

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className={`${styles.page} ${isWide ? styles.widePage : ""}`}>
      <TopNav
        section={section}
        onSectionChange={handleSectionChange}
        language={language}
        onLanguageChange={setLanguage}
        onNewChat={handleNewChat}
      />
      <SideNav
        section={section}
        onSectionChange={setSection}
        onEscalate={() => setShowEscalateModal(true)}
      />

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
              caseId={caseId}
            />

            {/* Stepper */}
            <Stepper mode={mode} activeStep={stepperStep} caseId={caseId} />

            {/* Thread or Welcome Starter */}
            {messages.length === 0 ? (
              <div className={styles.welcomeState}>
                <div className={styles.welcomeHeader}>
                  <span className={styles.welcomeEyebrow}>India's Traditional-Knowledge IP Companion</span>
                  <h2 className={styles.welcomeTitle}>How can Charaka assist your innovation today?</h2>
                  <p className={styles.welcomeDesc}>
                    Every answer is cited against the Patents Act 1970, Biological Diversity Act 2002,
                    Drugs &amp; Cosmetics Act 1940, and the Traditional Knowledge Digital Library (TKDL).
                  </p>
                </div>

                <div className={styles.starterGrid}>
                  {quickActions.map((qa) => (
                    <button
                      key={qa.key}
                      type="button"
                      className={styles.starterCard}
                      onClick={() => handleSend(qa.query)}
                    >
                      <span className={styles.starterIcon}>
                        <Icon name={qa.icon} size={18} />
                      </span>
                      <div className={styles.starterText}>
                        <span className={styles.starterTitle}>{qa.title}</span>
                        <span className={styles.starterSubtitle}>{qa.subtitle}</span>
                      </div>
                      <Icon name="arrow-right" size={13} className={styles.starterArrow} />
                    </button>
                  ))}
                </div>

                {/* Hero composer */}
                <SearchComposer
                  variant="hero"
                  value={heroDraft}
                  onChange={setHeroDraft}
                  onSend={() => handleSend()}
                  isTyping={isTyping}
                  placeholder={
                    mode === "deep_research"
                      ? "Describe your innovation to start deep intake (e.g. herbal extract for arthritis)…"
                      : "Ask any question about patentability, TKDL prior art, or regulatory compliance…"
                  }
                  language={language}
                  onLanguageChange={setLanguage}
                />
              </div>
            ) : (
              <>
                <ChatThread
                  messages={messages}
                  isTyping={isTyping}
                  onFollowUpClick={(q) => handleSend(q)}
                  onRetry={(q) => handleSend(q)}
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
            )}
          </>
        ) : section === "knowledge-base" ? (
          <KnowledgeGraph onOpenAssistant={() => setSection("assistant")} />
        ) : section === "ip-guidance" ? (
          <IPGuidance
            onAskAssistant={(q) => {
              setSection("assistant")
              handleSend(q)
            }}
          />
        ) : null}
      </main>

      {!isWide && (
        <RightPanel
          onQuickAction={(q) => handleSend(q)}
          onSelectRecentQuery={(rq) => handleSend(rq.question)}
          activeRecentId={activeRecentId}
          onEscalate={() => setShowEscalateModal(true)}
          conversationId={conversationIdRef.current}
        />
      )}

      <FeatureStrip />

      {showEscalateModal && (
        <EscalateModal
          onClose={() => setShowEscalateModal(false)}
          defaultCategory={category}
        />
      )}
    </div>
  )
}
