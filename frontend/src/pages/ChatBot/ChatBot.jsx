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
    text: "Namaste. I'm IP-SAKTI Sahayak — ask me about IP protection, ABS duties, or regulatory classification for an Ayurvedic formulation. I'll always cite the underlying statute or treaty.",
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
  "I couldn't reach the IP-SAKTI Sahayak backend just now. Make sure the FastAPI server is running on port 8000, then try again."

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
  const [activeCase, setActiveCase] = useState(null) // Phase 2 Innovation Intake case, if one is active
  const scrollRef = useRef(null)
  const isMountedRef = useRef(true)
  // Phase 2 — stable per-chat-session id so the backend can attach an Innovation
  // Intake case to this conversation (see backend/app/services/case_service.py).
  const conversationIdRef = useRef(
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `conv-${Date.now()}-${Math.random().toString(16).slice(2)}`
  )

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [messages, isTyping])

  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
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

    try {
      const { data } = await api.post("/query", {
        query: text,
        jurisdiction,
        language: LANGUAGE_CODES[language] || "en",
        dpdp_consent: true,
        conversation_id: conversationIdRef.current,
      })

      if (!isMountedRef.current) return

      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          text: data.answer,
          citations: citationLabels(data.citations),
          confidence: confidenceLabel(data.confidence_level),
          escalate: data.escalate_to_human,
        },
      ])

      if (data.case_id) {
        setActiveCase({
          caseId: data.case_id,
          status: data.case_status,
          readyForResearch: Boolean(data.ready_for_research),
          missingInformation: data.missing_information || [],
        })
      }
    } catch (err) {
      if (!isMountedRef.current) return
      setMessages((prev) => [
        ...prev,
        { id: `a-${Date.now()}`, role: "assistant", text: err.message || GENERIC_ERROR_REPLY },
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
      />

      <main className={styles.chatMain}>
        <ChatTopbar
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen((v) => !v)}
          jurisdiction={jurisdiction}
          onJurisdictionChange={setJurisdiction}
          theme={theme}
          onToggleTheme={toggleTheme}
        />

        <ChatMessages
          messages={messages}
          isTyping={isTyping}
          onFollowUpClick={handleSend}
          scrollRef={scrollRef}
        />

        {activeCase && (
          <div className={styles.caseStatusBar}>
            Case {activeCase.caseId} —{" "}
            {activeCase.readyForResearch
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
        />
      </main>
    </div>
  )
}
