import { useState } from "react"
import styles from "./Composer.module.css"
import { MicIcon, SendIcon } from "../Icons/Icons"

const LANGUAGES = ["English", "Hindi", "Tamil", "Telugu"]

export default function Composer({
  draft,
  onDraftChange,
  onKeyDown,
  onSend,
  isTyping,
  language,
  onLanguageChange,
}) {
  const [isListening, setIsListening] = useState(false)

  return (
    <div className={styles.composer}>
      <div className={styles.composerRow}>
        <div className={`${styles.composerInner} ${styles.nmInset}`}>
          {isListening ? (
            <div className={styles.recordingIndicator} aria-live="polite">
              Recording
              <span className={styles.dots}>
                <span className={styles.dot}>.</span>
                <span className={`${styles.dot} ${styles.dot2}`}>.</span>
                <span className={`${styles.dot} ${styles.dot3}`}>.</span>
              </span>
            </div>
          ) : (
            <textarea
              rows={1}
              placeholder="Ask about IP protection, ABS duties, or classification…"
              value={draft}
              onChange={(e) => onDraftChange(e.target.value)}
              onKeyDown={onKeyDown}
              disabled={isListening}
            />
          )}
          <button
            type="button"
            className={`${styles.iconBtn}${isListening ? ` ${styles.listening}` : ""}`}
            onClick={() => setIsListening((v) => !v)}
            aria-pressed={isListening}
            aria-label="Voice input"
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
          onChange={(e) => onLanguageChange(e.target.value)}
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
