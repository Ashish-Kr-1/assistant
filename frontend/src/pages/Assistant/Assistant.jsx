import { useEffect, useRef, useState } from "react"
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
import Icon from "../../components/Icons/IconSet"
import api from "../../api/axiosInstance"
import { mapCitationsToEvidence, mapConfidence } from "../../utils/mapQueryResponse"
import {
  initialConversation,
  recentQueryConversations,
  getDemoAnswer,
} from "../../demo"

export default function Assistant() {
  const [section, setSection] = useState("assistant")
  const [jurisdiction, setJurisdiction] = useState("india")
  const [category, setCategory] = useState("ayurvedic-formulation")
  const [language, setLanguage] = useState("en")
  const [heroDraft, setHeroDraft] = useState("")
  const [followUpDraft, setFollowUpDraft] = useState("")
  const [messages, setMessages] = useState(initialConversation)
  const [isTyping, setIsTyping] = useState(false)
  const [activeRecentId, setActiveRecentId] = useState("rq-1")
  const [showEscalateModal, setShowEscalateModal] = useState(false)
  const [usingDemoData, setUsingDemoData] = useState(false)

  const threadEndRef = useRef(null)
  const isMountedRef = useRef(true)
  const conversationIdRef = useRef(
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `conv-${Date.now()}-${Math.random().toString(16).slice(2)}`
  )

  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
    }
  }, [])

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [messages, isTyping])

  function handleSectionChange(next) {
    if (next?.startsWith("route-")) return
    setSection(next)
  }

  async function handleSend(overrideText) {
    const text = (overrideText ?? followUpDraft ?? heroDraft ?? "").trim()
    if (!text || isTyping) return

    setSection("assistant")
    setActiveRecentId(null)
    setHeroDraft("")
    setFollowUpDraft("")
    setMessages((prev) => [
      ...prev,
      { id: `u-${Date.now()}`, role: "user", text, timeLabel: nowLabel() },
    ])
    setIsTyping(true)

    try {
      const { data } = await api.post("/query", {
        query: text,
        jurisdiction,
        language,
        dpdp_consent: true,
        conversation_id: conversationIdRef.current,
        mode: "query",
      })

      if (!isMountedRef.current) return
      setUsingDemoData(false)
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          jurisdictionBadge: jurisdiction === "india" ? "INDIA" : "INTERNATIONAL",
          confidence: mapConfidence(data.confidence_level),
          text: data.answer || "I couldn't generate a confident answer for that just now.",
          evidence: mapCitationsToEvidence(data.citations),
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
      // Backend unreachable (e.g. during frontend-only testing) — fall back to
      // the canned demo answer bank so the flow stays fully interactive.
      await new Promise((r) => setTimeout(r, 550))
      if (!isMountedRef.current) return
      setUsingDemoData(true)
      const demo = getDemoAnswer(text)
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          jurisdictionBadge: jurisdiction === "india" ? "INDIA" : demo.jurisdictionBadge,
          confidence: demo.confidence,
          text: demo.text,
          evidence: demo.evidence,
          relatedInsight: demo.relatedInsight,
          followUps: demo.followUps,
        },
      ])
    } finally {
      if (isMountedRef.current) setIsTyping(false)
    }
  }

  function handleSelectRecentQuery(id) {
    setSection("assistant")
    setActiveRecentId(id)
    setMessages(recentQueryConversations[id] || initialConversation)
  }

  function handleResetContext() {
    setJurisdiction("india")
    setCategory("ayurvedic-formulation")
    setLanguage("en")
  }

  return (
    <div className={styles.page}>
      <TopNav section={section} onSectionChange={handleSectionChange} language={language} onLanguageChange={setLanguage} />
      <SideNav section={section} onSectionChange={setSection} />

      <main className={styles.main}>
        {section === "assistant" ? (
          <>
            <div className={styles.hero}>
              <span className={styles.heroIcon}>
                <Icon name="leaf" size={20} />
              </span>
              <div>
                <h1>IP-SAKTI Assistant</h1>
                <p>Ask questions, get evidence-backed guidance and take the next step.</p>
              </div>
            </div>

            <ContextBar
              jurisdiction={jurisdiction}
              onJurisdictionChange={setJurisdiction}
              category={category}
              onCategoryChange={setCategory}
              language={language}
              onLanguageChange={setLanguage}
              onResetContext={handleResetContext}
            />

            <SearchComposer
              variant="hero"
              value={heroDraft}
              onChange={setHeroDraft}
              onSend={() => handleSend()}
              isTyping={isTyping}
              placeholder="Describe your IP or regulatory question…"
              language={language}
            />

            <SuggestedQuestions onSelect={(q) => handleSend(q)} />

            <Stepper />

            {usingDemoData && (
              <div className={styles.demoBanner}>
                <Icon name="info" size={13} />
                Backend unreachable — showing a demo answer so you can keep testing the flow.
              </div>
            )}

            <ChatThread
              messages={messages}
              isTyping={isTyping}
              onFollowUpClick={(q) => handleSend(q)}
              scrollRef={threadEndRef}
            />

            <div className={styles.disclaimer}>
              Educational &amp; guidance purposes only — does not constitute formal legal advice.
            </div>

            <SearchComposer
              variant="followup"
              value={followUpDraft}
              onChange={setFollowUpDraft}
              onSend={() => handleSend()}
              isTyping={isTyping}
              placeholder="Ask a follow-up question…"
              language={language}
              onLanguageChange={setLanguage}
            />
          </>
        ) : (
          <SectionPlaceholder section={section} onOpenAssistant={() => setSection("assistant")} />
        )}
      </main>

      <RightPanel
        onQuickAction={(q) => handleSend(q)}
        onSelectRecentQuery={handleSelectRecentQuery}
        activeRecentId={activeRecentId}
        onViewAllRecent={() => setSection("query-history")}
        onEscalate={() => setShowEscalateModal(true)}
      />

      <FeatureStrip />

      {showEscalateModal && <EscalateModal onClose={() => setShowEscalateModal(false)} />}
    </div>
  )
}

function nowLabel() {
  const d = new Date()
  const h = d.getHours()
  const m = d.getMinutes().toString().padStart(2, "0")
  const period = h >= 12 ? "PM" : "AM"
  const h12 = h % 12 === 0 ? 12 : h % 12
  return `${h12}:${m} ${period}`
}
