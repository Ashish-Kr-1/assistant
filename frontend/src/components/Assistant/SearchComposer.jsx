import { useEffect, useRef, useState } from "react"
import styles from "./SearchComposer.module.css"
import Icon from "../Icons/IconSet"
import { composerLanguagePills, languages } from "../../demo"

const SPEECH_LANG_MAP = {
  en: "en-IN",
  hi: "hi-IN",
  bn: "bn-IN",
  ta: "ta-IN",
  te: "te-IN",
  mr: "mr-IN",
}

export default function SearchComposer({
  variant = "hero",
  value,
  onChange,
  onSend,
  isTyping,
  placeholder,
  language,
  onLanguageChange,
}) {
  const [isListening, setIsListening] = useState(false)
  const [notice, setNotice] = useState("")
  const recognitionRef = useRef(null)
  const noticeTimerRef = useRef(null)

  useEffect(() => {
    return () => {
      if (noticeTimerRef.current) clearTimeout(noticeTimerRef.current)
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort()
        } catch (_) {}
      }
    }
  }, [])

  function showNotice(msg, timeoutMs = 4000) {
    if (noticeTimerRef.current) clearTimeout(noticeTimerRef.current)
    setNotice(msg)
    if (timeoutMs > 0) {
      noticeTimerRef.current = setTimeout(() => setNotice(""), timeoutMs)
    }
  }

  function handleMicClick() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      showNotice("Voice input isn't supported in this browser — try Chrome or Edge.")
      return
    }
    if (isListening) {
      try {
        recognitionRef.current?.stop()
      } catch (_) {}
      setIsListening(false)
      return
    }
    try {
      const recognition = new SpeechRecognition()
      recognitionRef.current = recognition
      recognition.lang = SPEECH_LANG_MAP[language] || "en-IN"
      recognition.continuous = false
      recognition.interimResults = false
      recognition.onstart = () => {
        setIsListening(true)
        showNotice("Listening… speak now.", 0)
      }
      recognition.onresult = (e) => {
        const transcript = e.results?.[0]?.[0]?.transcript?.trim()
        if (transcript) {
          onChange((prev) => (prev ? `${prev.trim()} ${transcript}` : transcript))
          showNotice(`Captured: "${transcript}"`)
        }
      }
      recognition.onerror = () => {
        setIsListening(false)
        showNotice("Couldn't capture audio — check microphone permissions.")
      }
      recognition.onend = () => setIsListening(false)
      recognition.start()
    } catch (_) {
      setIsListening(false)
      showNotice("Couldn't start the microphone.")
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  return (
    <div className={`${styles.wrap} ${styles[variant]}`}>
      <div className={styles.inputRow}>
        <span className={styles.leadingIcon}>
          <Icon name={variant === "hero" ? "sparkle" : "chat"} size={17} />
        </span>
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isListening ? "Listening…" : placeholder}
        />
        <button
          type="button"
          className={`${styles.ghostIconBtn} ${isListening ? styles.listening : ""}`}
          onClick={handleMicClick}
          aria-pressed={isListening}
          aria-label="Voice input"
        >
          <Icon name="mic" size={17} />
        </button>
        <button
          type="button"
          className={styles.sendBtn}
          onClick={() => onSend()}
          disabled={!value.trim() || isTyping}
          aria-label="Send"
        >
          <Icon name="arrow-right" size={17} />
        </button>
      </div>

      {notice && <div className={styles.notice}>{notice}</div>}

      {variant === "followup" && (
        <div className={styles.footerRow}>
          <div className={styles.langPills}>
            {composerLanguagePills.map((l) => (
              <button
                key={l.code}
                type="button"
                className={`${styles.langPill} ${language === l.code ? styles.langPillActive : ""}`}
                onClick={() => onLanguageChange(l.code)}
              >
                {l.label}
              </button>
            ))}
            <span className={styles.moreLangs}>+{languages.length - composerLanguagePills.length} more</span>
          </div>
          <span className={styles.hint}>Press Enter to send</span>
        </div>
      )}
    </div>
  )
}
