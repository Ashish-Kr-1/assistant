import styles from "./Composer.module.css"
import { MicIcon, SendIcon } from "../Icons/Icons"

export default function Composer({ draft, onDraftChange, onKeyDown, onSend, isTyping }) {
  return (
    <div className={styles.composer}>
      <div className={`${styles.composerInner} ${styles.nmInset}`}>
        <textarea
          rows={1}
          placeholder="Ask about IP protection, ABS duties, or classification…"
          value={draft}
          onChange={(e) => onDraftChange(e.target.value)}
          onKeyDown={onKeyDown}
        />
        <button type="button" className={styles.iconBtn} aria-label="Voice input">
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
    </div>
  )
}
