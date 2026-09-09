import { useState, useRef, useEffect } from "react"
import styles from "./ChatBot.module.css"

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
  },
]

const UNDER_CONSTRUCTION_REPLY = "I am under construction, feel free to ask anything!"

function HamburgerIcon() {
  return <span className={styles.bar} aria-hidden="true" />
}

function SendIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  )
}

function MicIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  )
}

function LogoutIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  )
}

function SunIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4" />
      <line x1="12" y1="2" x2="12" y2="4" />
      <line x1="12" y1="20" x2="12" y2="22" />
      <line x1="4.2" y1="4.2" x2="5.6" y2="5.6" />
      <line x1="18.4" y1="18.4" x2="19.8" y2="19.8" />
      <line x1="2" y1="12" x2="4" y2="12" />
      <line x1="20" y1="12" x2="22" y2="12" />
      <line x1="4.2" y1="19.8" x2="5.6" y2="18.4" />
      <line x1="18.4" y1="5.6" x2="19.8" y2="4.2" />
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  )
}

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

  function handleSend() {
    const text = draft.trim()
    if (!text || isTyping) return
    setMessages((prev) => [...prev, { id: `u-${Date.now()}`, role: "user", text }])
    setDraft("")
    setIsTyping(true)
    replyTimeoutRef.current = setTimeout(() => {
      setMessages((prev) => [...prev, { id: `a-${Date.now()}`, role: "assistant", text: UNDER_CONSTRUCTION_REPLY }])
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
      <aside
        className={`${styles.sidebar}${sidebarOpen ? "" : ` ${styles.collapsed}`}`}
        style={{
          width: sidebarOpen ? sidebarWidth : 0,
          transition: isResizingSidebar ? "none" : undefined,
        }}
      >
        <div className={styles.sidebarBrand}>
          <div className={styles.sidebarBrandMark}>IS</div>
          <div className={styles.sidebarBrandText}>
            IP-SAKTI
            <span>Sahayak</span>
          </div>
        </div>

        <div className={styles.historyLabel}>Recent</div>
        <nav className={styles.historyList}>
          {chatHistory.map((chat) => (
            <button
              type="button"
              key={chat.id}
              className={`${styles.historyItem}${chat.id === activeChatId ? ` ${styles.active}` : ""}`}
              onClick={() => setActiveChatId(chat.id)}
            >
              <span className={styles.historyItemTitle}>{chat.title}</span>
              <span className={styles.historyItemDate}>{chat.date}</span>
            </button>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          <div className={styles.profileRow}>
            <div className={`${styles.profileAvatar} ${styles.nmInset}`}>
              {currentUser.name.split(" ").map((n) => n[0]).join("")}
            </div>
            <div>
              <div className={styles.profileName}>{currentUser.name}</div>
              <div className={styles.profileRole}>{currentUser.role}</div>
            </div>
          </div>
          <button type="button" className={styles.logoutBtn}>
            <LogoutIcon />
            Log out
          </button>
        </div>

        {sidebarOpen && (
          <div
            className={styles.resizer}
            onMouseDown={handleResizeStart}
            role="separator"
            aria-orientation="vertical"
            aria-label="Resize chat history panel"
          />
        )}
      </aside>

      <main className={styles.chatMain}>
        <div className={styles.chatTopbar}>
          <button
            type="button"
            className={`${styles.hamburgerBtn} ${styles.nmRaised}`}
            onClick={() => setSidebarOpen((v) => !v)}
            aria-label="Toggle chat history panel"
          >
            <HamburgerIcon />
          </button>
          <div className={`${styles.jurisdictionToggle} ${styles.nmInset}`}>
            <button
              type="button"
              className={jurisdiction === "national" ? `${styles.active} ${styles.national}` : ""}
              onClick={() => setJurisdiction("national")}
            >
              National
            </button>
            <button
              type="button"
              className={jurisdiction === "international" ? `${styles.active} ${styles.international}` : ""}
              onClick={() => setJurisdiction("international")}
            >
              International
            </button>
          </div>
          <button
            type="button"
            className={`${styles.themeToggle} ${styles.nmInset}`}
            onClick={toggleTheme}
            aria-label="Toggle light/dark theme"
          >
            <SunIcon />
            <span className={`${styles.themeToggleThumb}${theme === "dark" ? ` ${styles.dark}` : ""}`} />
            <MoonIcon />
          </button>
        </div>

        <div className={styles.messagesScroll} ref={scrollRef}>
          {messages.map((msg) => (
            <div className={`${styles.msgRow} ${styles[msg.role]}`} key={msg.id}>
              <div className={`${styles.msgBubble} ${msg.role === "assistant" ? styles.nmRaised : ""}`}>
                {msg.text}
                {msg.citations && (
                  <div className={styles.msgMeta}>
                    {msg.citations.map((c) => (
                      <span className={styles.citationChip} key={c}>
                        <span className={styles.citationMark} aria-hidden="true" />
                        {c}
                      </span>
                    ))}
                    <span className={styles.confidenceChip}>{msg.confidence}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isTyping && (
            <div className={`${styles.msgRow} ${styles.assistant}`}>
              <div className={`${styles.msgBubble} ${styles.nmRaised} ${styles.typingBubble}`}>
                <span className={styles.typingDot} />
                <span className={styles.typingDot} />
                <span className={styles.typingDot} />
              </div>
            </div>
          )}
        </div>

        <div className={styles.disclaimerBar}>
          Educational &amp; guidance purposes only — does not constitute formal legal advice.
        </div>

        <div className={styles.composer}>
          <div className={`${styles.composerInner} ${styles.nmInset}`}>
            <textarea
              rows={1}
              placeholder="Ask about IP protection, ABS duties, or classification…"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button type="button" className={styles.iconBtn} aria-label="Voice input">
              <MicIcon />
            </button>
            <button
              type="button"
              className={styles.sendBtn}
              onClick={handleSend}
              disabled={!draft.trim() || isTyping}
              aria-label="Send message"
            >
              <SendIcon />
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
