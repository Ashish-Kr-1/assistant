import { useState, useRef, useEffect } from "react"
import styles from "./ChatBot.module.css"
import Sidebar from "../../components/Sidebar/Sidebar"
import ChatTopbar from "../../components/ChatTopbar/ChatTopbar"
import ChatMessages from "../../components/ChatMessages/ChatMessages"
import Composer from "../../components/Composer/Composer"

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
    citations: ["Patents Act 1970, Sec 3(p)", "TKDL Prior-Art Classification"],
    confidence: "High confidence",
    followUps: [
      "What counts as a novel, inventive modification here?",
      "Does this bar apply to Ayurveda-Aahar products too?",
      "What ABS duties would apply if I export this formulation?",
    ],
  },
]

const UNDER_CONSTRUCTION_REPLY = "I am under construction, feel free to ask anything!"

const UNDER_CONSTRUCTION_FOLLOWUPS = [
  "What documents are needed for an ABS approval?",
  "How is a formulation classified under Indian law?",
  "What's the difference between National and International guidance here?",
]

const SIDEBAR_MIN_WIDTH = 220
const SIDEBAR_MAX_WIDTH = 680

export default function ChatBot() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sidebarWidth, setSidebarWidth] = useState(360)
  const [isResizingSidebar, setIsResizingSidebar] = useState(false)
  const [jurisdiction, setJurisdiction] = useState("national")
  const [activeChatId, setActiveChatId] = useState("1")
  const [messages, setMessages] = useState(initialMessages)
  const [draft, setDraft] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const [theme, setTheme] = useState("light")
  const scrollRef = useRef(null)
  const replyTimeoutRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [messages, isTyping])

  useEffect(() => {
    return () => {
      if (replyTimeoutRef.current) clearTimeout(replyTimeoutRef.current)
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

  function handleSend(overrideText) {
    const text = (overrideText ?? draft).trim()
    if (!text || isTyping) return
    setMessages((prev) => [...prev, { id: `u-${Date.now()}`, role: "user", text }])
    setDraft("")
    setIsTyping(true)
    replyTimeoutRef.current = setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { id: `a-${Date.now()}`, role: "assistant", text: UNDER_CONSTRUCTION_REPLY, followUps: UNDER_CONSTRUCTION_FOLLOWUPS },
      ])
      setIsTyping(false)
    }, 5000)
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

        <div className={styles.disclaimerBar}>
          Educational &amp; guidance purposes only — does not constitute formal legal advice.
        </div>

        <Composer
          draft={draft}
          onDraftChange={setDraft}
          onKeyDown={handleKeyDown}
          onSend={handleSend}
          isTyping={isTyping}
        />
      </main>
    </div>
  )
}
