import { useState, useRef, useEffect } from "react"
import styles from "./Composer.module.css"
import { MicIcon, SendIcon } from "../Icons/Icons"

const LANGUAGES = ["English", "Hindi", "Tamil", "Telugu"]

const LANGUAGE_SPEECH_MAP = {
  English: "en-IN",
  Hindi: "hi-IN",
  Tamil: "ta-IN",
  Telugu: "te-IN",
}

export default function Composer({
  draft,
  onDraftChange,
  onKeyDown,
  onSend,
  isTyping,
  language,
  onLanguageChange,
  placeholder,
}) {
  const [isListening, setIsListening] = useState(false)
  const [voiceNotice, setVoiceNotice] = useState("")
  const recognitionRef = useRef(null)
  const isListeningRef = useRef(false)
  const startTimeRef = useRef(0)
  const noticeTimerRef = useRef(null)

  function showNotice(msg, timeoutMs = 5000) {
    if (noticeTimerRef.current) clearTimeout(noticeTimerRef.current)
    setVoiceNotice(msg)
    if (timeoutMs > 0) {
      noticeTimerRef.current = setTimeout(() => {
        setVoiceNotice("")
      }, timeoutMs)
    }
  }

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

  function handleToggleVoice() {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      showNotice(
        "Voice input is not supported in this browser. Please use Google Chrome, Edge, or Safari.",
        6000
      )
      return
    }

    // If currently listening, stop it
    if (isListeningRef.current || isListening) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop()
        } catch (_) {}
      }
      isListeningRef.current = false
      setIsListening(false)
      showNotice("Voice recording stopped.", 2000)
      return
    }

    try {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort()
        } catch (_) {}
      }

      const recognition = new SpeechRecognition()
      recognitionRef.current = recognition

      const targetLang = LANGUAGE_SPEECH_MAP[language] || "en-IN"
      recognition.lang = targetLang
      // continuous: false is essential on macOS Safari & Chrome to avoid instant termination
      recognition.continuous = false
      recognition.interimResults = false
      recognition.maxAlternatives = 1

      startTimeRef.current = Date.now()

      recognition.onstart = () => {
        isListeningRef.current = true
        setIsListening(true)
        showNotice(`🎙️ Listening in ${language}... please speak now.`, 0)
      }

      recognition.onresult = (event) => {
        if (!event.results || event.results.length === 0) return
        const transcript = event.results[0][0].transcript
        if (transcript && transcript.trim()) {
          const spoken = transcript.trim()
          onDraftChange((prev) => (prev ? `${prev.trim()} ${spoken}` : spoken))
          showNotice(`✓ Captured: "${spoken}"`, 3500)
        }
      }

      recognition.onerror = (e) => {
        console.warn("Speech recognition error:", e.error)
        isListeningRef.current = false
        setIsListening(false)
        recognitionRef.current = null

        if (e.error === "not-allowed") {
          showNotice(
            "Microphone permission blocked. Please allow microphone in browser address bar (lock icon).",
            6000
          )
        } else if (e.error === "no-speech") {
          showNotice("No speech detected. Please speak closer to your microphone and try again.", 4000)
        } else if (e.error === "network") {
          showNotice(
            "Speech service network error. If using Brave browser, enable Google Services for Speech in Settings, or use Chrome/Safari.",
            7000
          )
        } else if (e.error === "audio-capture") {
          showNotice("No microphone found or microphone is currently in use by another application.", 5000)
        } else {
          showNotice(`Voice input ended: ${e.error}`, 4000)
        }
      }

      recognition.onend = () => {
        const elapsedMs = Date.now() - startTimeRef.current
        isListeningRef.current = false
        setIsListening(false)
        recognitionRef.current = null

        if (elapsedMs < 600) {
          showNotice(
            "Microphone was closed immediately by the browser. Check microphone permissions or use Google Chrome / Safari.",
            6000
          )
        }
      }

      recognition.start()
    } catch (err) {
      console.error("Speech recognition startup error:", err)
      isListeningRef.current = false
      setIsListening(false)
      recognitionRef.current = null
      showNotice("Could not start microphone: " + (err.message || "Unknown error"), 5000)
    }
  }

  return (
    <div className={styles.composer}>
      {voiceNotice && (
        <div
          className={`${styles.voiceNoticeBanner} ${
            isListening ? styles.listeningNotice : ""
          }`}
          role="status"
          aria-live="polite"
        >
          <span>{voiceNotice}</span>
          {isListening && (
            <span className={styles.dots}>
              <span className={styles.dot}>●</span>
              <span className={`${styles.dot} ${styles.dot2}`}>●</span>
              <span className={`${styles.dot} ${styles.dot3}`}>●</span>
            </span>
          )}
        </div>
      )}

      <div className={styles.composerRow}>
        <div className={`${styles.composerInner} ${styles.nmInset}`}>
          <textarea
            rows={1}
            placeholder={
              isListening
                ? `Listening in ${language}... speak now`
                : placeholder || "Ask about IP protection, ABS duties, or classification…"
            }
            value={draft}
            onChange={(e) => onDraftChange(e.target.value)}
            onKeyDown={onKeyDown}
          />

          <button
            type="button"
            className={`${styles.iconBtn}${isListening ? ` ${styles.listening}` : ""}`}
            onClick={handleToggleVoice}
            aria-pressed={isListening}
            aria-label={isListening ? "Stop voice input" : "Start voice input"}
            title={isListening ? "Click to stop recording" : `Click to speak in ${language}`}
          >
            <MicIcon />
          </button>

          <button
            type="button"
            className={styles.sendBtn}
            onClick={() => onSend()}
            disabled={!draft.trim() || isTyping}
            aria-label="Send message"
          >
            <SendIcon />
          </button>
        </div>

        <select
          className={`${styles.languageSelect} ${styles.nmRaised}`}
          value={language}
          onChange={(e) => {
            onLanguageChange(e.target.value)
            if (isListening && recognitionRef.current) {
              try {
                recognitionRef.current.stop()
              } catch (_) {}
              isListeningRef.current = false
              setIsListening(false)
              showNotice(`Language switched to ${e.target.value}. Click mic to speak.`, 3000)
            }
          }}
          aria-label="Choose response language"
        >
          {LANGUAGES.map((lang) => (
            <option key={lang} value={lang}>
              {lang}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
