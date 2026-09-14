import { Fragment } from "react"
import styles from "./ChatMessages.module.css"

export default function ChatMessages({ messages, isTyping, onFollowUpClick, scrollRef }) {
  return (
    <div className={styles.messagesScroll} ref={scrollRef}>
      {messages.map((msg, index) => {
        const isLastMessage = index === messages.length - 1
        return (
          <Fragment key={msg.id}>
            <div className={`${styles.msgRow} ${styles[msg.role]}`}>
              <div className={`${styles.msgBubble} ${msg.role === "assistant" ? styles.nmRaised : ""}`}>
                {msg.text}
                {msg.citations && (
                  <div className={styles.msgMeta}>
                    {msg.citations.map((c) =>
                      c.url ? (
                        <a
                          className={styles.citationChip}
                          key={c.label}
                          href={c.url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <span className={styles.citationMark} aria-hidden="true" />
                          {c.label}
                        </a>
                      ) : (
                        <span className={styles.citationChip} key={c.label}>
                          <span className={styles.citationMark} aria-hidden="true" />
                          {c.label}
                        </span>
                      )
                    )}
                    <span className={styles.confidenceChip}>{msg.confidence}</span>
                  </div>
                )}
              </div>
            </div>
            {msg.role === "assistant" && msg.followUps && isLastMessage && !isTyping && (
              <div className={styles.followUpRow}>
                {msg.followUps.map((question) => (
                  <button
                    type="button"
                    key={question}
                    className={styles.followUpChip}
                    onClick={() => onFollowUpClick(question)}
                  >
                    {question}
                  </button>
                ))}
              </div>
            )}
          </Fragment>
        )
      })}
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
  )
}
