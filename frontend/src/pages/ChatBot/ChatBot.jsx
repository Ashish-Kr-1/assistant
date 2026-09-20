import { useState, useRef, useEffect } from "react"
import styles from "./ChatBot.module.css"
import Sidebar from "../../components/Sidebar/Sidebar"
import ChatTopbar from "../../components/ChatTopbar/ChatTopbar"
import ChatMessages from "../../components/ChatMessages/ChatMessages"
import Composer from "../../components/Composer/Composer"
import api from "../../api/axiosInstance"

const currentUser = {
  name: "Ananya Verma",
  role: "IP Facilitator",
}

const chatHistory = [
  { id: "1", title: "Ashwagandha extract patent bar (Sec 3(p))", date: "Today" },
  { id: "2", title: "ABS fee calc — Turmeric formulation export", date: "Today" },
  { id: "3", title: "Classical Generic vs Proprietary classification", date: "Yesterday" },
  { id: "4", title: "Nagoya Protocol prior-informed consent steps", date: "Yesterday" },
  { id: "5", title: "TKDL prior-art search — Triphala", date: "3 days ago" },
]

const initialMessages = [
  {
    id: "m1",
    role: "assistant",
    text: "Namaste. I'm Charaka IP — ask me about IP protection, ABS duties, or regulatory classification for an Ayurvedic formulation. I'll always cite the underlying statute or treaty.",
  },
  {
    id: "m2",
    role: "user",
    text: "Is a classical Ashwagandha churna formulation patentable in India?",
  },
  {
    id: "m3",
    role: "assistant",
    text: "No. A formulation drawn directly from a First Schedule classical text is treated as traditional knowledge and is barred from patenting as an existing product. A patent may still cover a novel, inventive modification — e.g. a new extraction process or a synergistic combination not disclosed in the classical texts.",
    citations: [
      { label: "Patents Act 1970, Sec 3(p)", url: "https://www.indiacode.nic.in/handle/123456789/1989" },
      { label: "TKDL Prior-Art Classification", url: "" },
    ],
    confidence: "High confidence",
    followUps: [
      "What counts as a novel, inventive modification here?",
      "Does this bar apply to Ayurveda-Aahar products too?",
      "What ABS duties would apply if I export this formulation?",
    ],
  },
]

const GENERIC_ERROR_REPLY =
  "I couldn't reach the Charaka IP backend just now. Make sure the FastAPI server is running on port 8000, then try again."

function confidenceLabel(level) {
  switch ((level || "").toUpperCase()) {
    case "HIGH":
      return "High confidence"
    case "MEDIUM":
      return "Medium confidence"
    case "LOW":
      return "Low confidence"
    default:
      return null
  }
}

function citationLabels(citations) {
  if (!Array.isArray(citations) || citations.length === 0) return undefined
  return citations.map((c) => {
    if (c.source_type === "web") {
      return { label: `Web: ${c.title || "Source"}`, url: c.official_url || "" }
    }
    const statute = c.statute || c.treaty || c.act_name || "Source"
    const locator = c.section || c.rule || c.article || c.section_id || ""
    const label = locator ? `${statute}, ${locator}` : statute
    return { label, url: c.official_url || "" }
  })
}

const LANGUAGE_CODES = {
  English: "en",
  Hindi: "hi",
  Tamil: "ta",
  Telugu: "te",
}

const INITIAL_TERMINAL_LOGS = [
  "2026-09-15 03:07:13,035 [INFO] legal_scraper: Loaded 37/37 statutory chunks via RealLegalScraper.",
  "2026-09-15 03:07:26,860 [INFO] vector_store_manager: Indexed 38 chunks into Qdrant vector store.",
  "2026-09-15 03:07:27,036 [INFO] llm_factory: Pluggable LLM factory active (command-a-03-2025).",
  "2026-09-15 03:07:27,050 [INFO] uvicorn: Application startup complete on http://127.0.0.1:8000.",
]

const SIDEBAR_MIN_WIDTH = 220
const SIDEBAR_MAX_WIDTH = 680

export default function ChatBot() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sidebarWidth, setSidebarWidth] = useState(360)
  const [isResizingSidebar, setIsResizingSidebar] = useState(false)
  const [jurisdiction, setJurisdiction] = useState("national")
  const [language, setLanguage] = useState("English")
  const [activeChatId, setActiveChatId] = useState("1")
  const [messages, setMessages] = useState(initialMessages)
  const [draft, setDraft] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [theme, setTheme] = useState("light")
  const [mode, setMode] = useState("query") // "query" | "deep_research"
  const [showIntakeModal, setShowIntakeModal] = useState(false)
  const [intakeFormData, setIntakeFormData] = useState({
    name: "",
    problem_solved: "",
    ingredients: "",
    category: "Patent & Proprietary Medicine",
  })
  const [activeCase, setActiveCase] = useState(null) // Phase 2 Innovation Intake case, if one is active
  const [terminalLogs, setTerminalLogs] = useState(INITIAL_TERMINAL_LOGS)
  const scrollRef = useRef(null)
  const isMountedRef = useRef(true)
  // Phase 2 — stable per-chat-session id so the backend can attach an Innovation
  // Intake case to this conversation (see backend/app/services/case_service.py).
  const conversationIdRef = useRef(
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `conv-${Date.now()}-${Math.random().toString(16).slice(2)}`
  )

  const streamTimerRef = useRef(null)

  function streamResponse(messageId, fullAnswer, meta = {}) {
    if (streamTimerRef.current) {
      clearInterval(streamTimerRef.current)
      streamTimerRef.current = null
    }

    const answerStr = fullAnswer || ""

    // Mount the initial assistant message in streaming state
    setMessages((prev) => [
      ...prev,
      {
        id: messageId,
        role: "assistant",
        text: "",
        isStreaming: true,
        citations: undefined,
        confidence: undefined,
        escalate: meta.escalate || false,
        assessment: null,
        caseId: meta.caseId || null,
        followUps: undefined,
      },
    ])
    setIsTyping(false)

    // Tokenize text into chunks (words + spaces + punctuation)
    const tokens = answerStr.match(/(\s+|\S+)/g) || [answerStr]
    let tokenIdx = 0
    let accumulated = ""

    // Dynamically pace streaming: 1-3 tokens per tick
    const step = tokens.length > 300 ? 3 : tokens.length > 100 ? 2 : 1
    const delay = tokens.length > 300 ? 12 : 18

    streamTimerRef.current = setInterval(() => {
      if (!isMountedRef.current) {
        clearInterval(streamTimerRef.current)
        streamTimerRef.current = null
        return
      }

      if (tokenIdx < tokens.length) {
        const nextChunk = tokens.slice(tokenIdx, tokenIdx + step).join("")
        tokenIdx += step
        accumulated += nextChunk

        setMessages((prev) =>
          prev.map((m) =>
            m.id === messageId ? { ...m, text: accumulated } : m
          )
        )
      } else {
        clearInterval(streamTimerRef.current)
        streamTimerRef.current = null

        // Finalize: remove cursor, reveal citations, confidence & assessment panels
        setMessages((prev) =>
          prev.map((m) =>
            m.id === messageId
              ? {
                  ...m,
                  text: answerStr,
                  isStreaming: false,
                  citations: meta.citations,
                  confidence: meta.confidence,
                  assessment: meta.assessment,
                  followUps: meta.followUps,
                }
              : m
          )
        )
      }
    }, delay)
  }

  function handleModeChange(newMode) {
    setMode(newMode)
    if (newMode === "query") {
      setActiveCase(null)
    }
  }

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [messages, isTyping])

  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
      if (streamTimerRef.current) clearInterval(streamTimerRef.current)
    }
  }, [])

  useEffect(() => {
    if (!isResizingSidebar) return

    function handleMouseMove(e) {
      const next = Math.min(SIDEBAR_MAX_WIDTH, Math.max(SIDEBAR_MIN_WIDTH, e.clientX))
      setSidebarWidth(next)
    }
    function handleMouseUp() {
      setIsResizingSidebar(false)
    }

    document.body.style.cursor = "col-resize"
    document.body.style.userSelect = "none"
    window.addEventListener("mousemove", handleMouseMove)
    window.addEventListener("mouseup", handleMouseUp)
    return () => {
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
      window.removeEventListener("mousemove", handleMouseMove)
      window.removeEventListener("mouseup", handleMouseUp)
    }
  }, [isResizingSidebar])

  function handleResizeStart(e) {
    e.preventDefault()
    setIsResizingSidebar(true)
  }

  async function handleSend(overrideText) {
    const text = (overrideText ?? draft).trim()
    if (!text || isTyping) return
    setMessages((prev) => [...prev, { id: `u-${Date.now()}`, role: "user", text }])
    setDraft("")
    setIsTyping(true)

    const nowStr = () => {
      const d = new Date()
      return `${d.toISOString().slice(0, 10)} ${d.toTimeString().slice(0, 8)},${String(d.getMilliseconds()).padStart(3, "0")}`
    }

    setTerminalLogs((prev) => [
      ...prev,
      `${nowStr()} [INFO] query_api: Inbound request [mode=${mode.toUpperCase()}] '${text.slice(0, 45)}${text.length > 45 ? "..." : ""}' [jurisdiction=${jurisdiction}]`,
      `${nowStr()} [INFO] crag_graph: Retrieving statutory chunks for query: '${text.slice(0, 35)}' [${jurisdiction.toUpperCase()}]`,
    ])

    const timer1 = setTimeout(() => {
      if (isMountedRef.current) {
        setTerminalLogs((prev) => [
          ...prev,
          `${nowStr()} [INFO] vector_store: Vector similarity search in Qdrant (top_k=4)...`,
        ])
      }
    }, 350)

    const timer2 = setTimeout(() => {
      if (isMountedRef.current) {
        setTerminalLogs((prev) => [
          ...prev,
          `${nowStr()} [INFO] crag_grader: Evaluating retrieved statutory provisions...`,
          `${nowStr()} [INFO] abs_pointer: Inspecting botanical ingredients and ABS provisions...`,
        ])
      }
    }, 850)

    try {
      const { data } = await api.post("/query", {
        query: text,
        jurisdiction,
        language: LANGUAGE_CODES[language] || "en",
        dpdp_consent: true,
        conversation_id: conversationIdRef.current,
        mode: mode,
      })

      clearTimeout(timer1)
      clearTimeout(timer2)

      if (Array.isArray(data.execution_logs) && data.execution_logs.length > 0) {
        setTerminalLogs((prev) => [...prev, ...data.execution_logs].slice(-100))
      } else {
        setTerminalLogs((prev) => [
          ...prev,
          `${nowStr()} [INFO] query_api: Response received (${data.confidence_level || "HIGH"}, ${data.citations?.length || 0} citations) [200 OK]`,
        ].slice(-100))
      }

      if (!isMountedRef.current) return

      // Phase 3: if in deep_research and the case just became ready, fetch the assessment to show in-chat.
      let assessment = null
      let followUps = undefined
      if (mode === "deep_research" && data.case_id && data.ready_for_research) {
        try {
          const caseResp = await api.get(`/cases/${data.case_id}`, {
            params: { user_id: "anonymous_user" },
          })
          if (caseResp.data?.assessment?.assessment_status === "COMPLETED") {
            assessment = caseResp.data.assessment
            // Generate contextual follow-up suggestions from the research plan
            const queries = assessment.research_plan?.recommended_crag_queries || []
            followUps = queries.slice(0, 3)
          }
        } catch (_) {
          // Non-fatal: assessment fetch can fail without breaking the chat
        }
      }

      streamResponse(
        `a-${Date.now()}`,
        data.answer,
        {
          citations: citationLabels(data.citations),
          confidence: confidenceLabel(data.confidence_level),
          escalate: data.escalate_to_human,
          assessment,
          caseId: mode === "deep_research" ? data.case_id : null,
          followUps,
        }
      )

      if (mode === "deep_research" && data.case_id) {
        setActiveCase({
          caseId: data.case_id,
          status: data.case_status,
          readyForResearch: Boolean(data.ready_for_research),
          missingInformation: data.missing_information || [],
          hasAssessment: Boolean(assessment),
        })
      } else if (mode === "query") {
        setActiveCase(null)
      }
    } catch (err) {
      clearTimeout(timer1)
      clearTimeout(timer2)
      setTerminalLogs((prev) => [
        ...prev,
        `${nowStr()} [ERROR] query_api: Request failed: ${err.message || "Network Error"}`,
      ])
      if (!isMountedRef.current) return
      setMessages((prev) => [
        ...prev,
        { id: `a-${Date.now()}`, role: "assistant", text: err.message || GENERIC_ERROR_REPLY },
      ])
    } finally {
      if (isMountedRef.current) setIsTyping(false)
    }
  }

  async function handleGenerateReport(caseId, messageId) {
    setIsTyping(true)
    setMessages((prev) =>
      prev.map((m) => (m.id === messageId ? { ...m, reportRequested: true } : m))
    )
    try {
      // Phase 4 runs several CRAG retrieval calls sequentially, so give it more
      // headroom than the default request timeout.
      const { data } = await api.post(`/cases/${caseId}/report`, null, {
        params: { user_id: "anonymous_user" },
        timeout: 90_000,
      })
      if (!isMountedRef.current) return
      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId ? { ...m, report: data.research_report, reportRequested: true } : m
        )
      )
    } catch (err) {
      if (!isMountedRef.current) return
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          text: err.message || "Couldn't generate the research report just now. Please try again.",
        },
      ])
    } finally {
      if (isMountedRef.current) setIsTyping(false)
    }
  }

  async function handleQuickFormSubmit(e) {
    e.preventDefault()
    if (!intakeFormData.name.trim()) return
    setShowIntakeModal(false)
    setIsTyping(true)

    const summaryText = `I am submitting an Ayurvedic innovation for Deep Research intake:
- Innovation / Product Name: ${intakeFormData.name}
- Purpose & Problem Solved: ${intakeFormData.problem_solved}
- Ingredients: ${intakeFormData.ingredients}
- Target Classification: ${intakeFormData.category}`

    setMessages((prev) => [...prev, { id: `u-${Date.now()}`, role: "user", text: summaryText }])

    try {
      const { data } = await api.post("/query", {
        query: summaryText,
        jurisdiction,
        language: LANGUAGE_CODES[language] || "en",
        dpdp_consent: true,
        conversation_id: conversationIdRef.current,
        mode: "deep_research",
      })

      let assessment = null
      if (data.case_id && data.ready_for_research) {
        try {
          const caseResp = await api.get(`/cases/${data.case_id}`, {
            params: { user_id: "anonymous_user" },
          })
          if (caseResp.data?.assessment?.assessment_status === "COMPLETED") {
            assessment = caseResp.data.assessment
          }
        } catch (_) {}
      }

      streamResponse(
        `a-${Date.now()}`,
        data.answer || "Innovation intake received. Case profile registered.",
        {
          citations: citationLabels(data.citations),
          confidence: confidenceLabel(data.confidence_level),
          assessment,
          caseId: data.case_id,
          followUps: assessment?.research_plan?.recommended_crag_queries?.slice(0, 3),
        }
      )

      if (data.case_id) {
        setActiveCase({
          caseId: data.case_id,
          status: data.case_status,
          readyForResearch: Boolean(data.ready_for_research),
          missingInformation: data.missing_information || [],
          hasAssessment: Boolean(assessment),
        })
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { id: `err-${Date.now()}`, role: "assistant", text: GENERIC_ERROR_REPLY },
      ])
    } finally {
      if (isMountedRef.current) setIsTyping(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function toggleTheme() {
    setTheme((t) => (t === "dark" ? "light" : "dark"))
  }

  return (
    <div className={styles.chatbotPage} data-theme={theme}>
      <Sidebar
        isOpen={sidebarOpen}
        width={sidebarWidth}
        isResizing={isResizingSidebar}
        onResizeStart={handleResizeStart}
        chatHistory={chatHistory}
        activeChatId={activeChatId}
        onSelectChat={setActiveChatId}
        currentUser={currentUser}
        terminalLogs={terminalLogs}
        isTyping={isTyping}
        onClearTerminal={() => setTerminalLogs([])}
      />

      <main className={styles.chatMain}>
        <ChatTopbar
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen((v) => !v)}
          jurisdiction={jurisdiction}
          onJurisdictionChange={setJurisdiction}
          theme={theme}
          onToggleTheme={toggleTheme}
          mode={mode}
          onModeChange={handleModeChange}
        />

        {mode === "deep_research" && (
          <div className={styles.deepResearchPillBanner}>
            <span className={styles.deepResearchPillBadge}>🔬 DEEP RESEARCH MODE</span>
            <span className={styles.deepResearchPillText}>
              Innovation Intake, Statutory Classification &amp; Report Generator Active
            </span>
            <button
              type="button"
              className={styles.openFormBtn}
              onClick={() => setShowIntakeModal(true)}
            >
              📝 Open Intake Form
            </button>
          </div>
        )}

        <ChatMessages
          messages={messages}
          isTyping={isTyping}
          onFollowUpClick={handleSend}
          onGenerateReport={handleGenerateReport}
          scrollRef={scrollRef}
        />

        {mode === "deep_research" && activeCase && (
          <div className={styles.caseStatusBar}>
            Case {activeCase.caseId} —{" "}
            {activeCase.hasAssessment
              ? "✓ Phase 3 assessment complete"
              : activeCase.readyForResearch
              ? "ready for research"
              : `intake in progress${
                  activeCase.missingInformation.length
                    ? ` (${activeCase.missingInformation.length} item${
                        activeCase.missingInformation.length === 1 ? "" : "s"
                      } remaining)`
                    : ""
                }`}
          </div>
        )}

        <div className={styles.disclaimerBar}>
          Educational &amp; guidance purposes only — does not constitute formal legal advice.
        </div>

        <Composer
          draft={draft}
          onDraftChange={setDraft}
          onKeyDown={handleKeyDown}
          onSend={handleSend}
          isTyping={isTyping}
          language={language}
          onLanguageChange={setLanguage}
          placeholder={
            mode === "query"
              ? "Ask any legal, IP, patentability, or ABS question (e.g., Is Ashwagandha patentable in India?)..."
              : "Describe your innovation or answer intake questions for Deep Research report..."
          }
        />
      </main>

      {/* Quick Innovation Intake Form Modal */}
      {showIntakeModal && (
        <div className={styles.modalOverlay} onClick={() => setShowIntakeModal(false)}>
          <div className={styles.modalCard} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h3>🔬 Innovation Intake &amp; Deep Research</h3>
              <button
                type="button"
                className={styles.closeBtn}
                onClick={() => setShowIntakeModal(false)}
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleQuickFormSubmit}>
              <div className={styles.modalBody}>
                <div className={styles.formField}>
                  <label>Innovation / Product Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., AyurGlyco Topical Gel"
                    value={intakeFormData.name}
                    onChange={(e) => setIntakeFormData({ ...intakeFormData, name: e.target.value })}
                  />
                </div>
                <div className={styles.formField}>
                  <label>Purpose &amp; Problem Solved *</label>
                  <textarea
                    rows={3}
                    required
                    placeholder="e.g., Novel synergistic transdermal formulation for diabetic neuropathy and pain relief"
                    value={intakeFormData.problem_solved}
                    onChange={(e) => setIntakeFormData({ ...intakeFormData, problem_solved: e.target.value })}
                  />
                </div>
                <div className={styles.formField}>
                  <label>Botanical / Classical Ingredients</label>
                  <input
                    type="text"
                    placeholder="e.g., Ashwagandha (Withania somnifera), Shallaki, Sesame Oil"
                    value={intakeFormData.ingredients}
                    onChange={(e) => setIntakeFormData({ ...intakeFormData, ingredients: e.target.value })}
                  />
                </div>
                <div className={styles.formField}>
                  <label>Target Regulatory Classification</label>
                  <select
                    value={intakeFormData.category}
                    onChange={(e) => setIntakeFormData({ ...intakeFormData, category: e.target.value })}
                  >
                    <option value="Patent & Proprietary Medicine">Patent &amp; Proprietary Medicine (DCA Rule 158B)</option>
                    <option value="Classical Formulation">Classical Formulation (First Schedule Text)</option>
                    <option value="Ayurveda Aahara">Ayurveda Aahara (FSSAI Regulations 2022)</option>
                    <option value="Phytopharmaceutical Drug">Phytopharmaceutical Drug (CDSCO Rule 122E)</option>
                  </select>
                </div>
              </div>
              <div className={styles.modalFooter}>
                <button
                  type="button"
                  className={styles.modalCancelBtn}
                  onClick={() => setShowIntakeModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className={styles.modalSubmitBtn}>
                  🚀 Submit &amp; Run Deep Research
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
