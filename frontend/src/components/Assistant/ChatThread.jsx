import styles from "./ChatThread.module.css"
import MessageBubble from "./MessageBubble"
import Logo from "../Logo/Logo"

export default function ChatThread({ messages, isTyping, onFollowUpClick, scrollRef }) {
  if (!messages.length && !isTyping) return null

  return (
    <div className={styles.thread} ref={scrollRef}>
      {messages.map((msg, i) => (
        <MessageBubble
          key={msg.id}
          message={msg}
          isLast={i === messages.length - 1}
          isTyping={isTyping}
          onFollowUpClick={onFollowUpClick}
        />
      ))}

      {isTyping && (
        <div className={styles.typingRow}>
          <span className={styles.typingAvatar}>
            <Logo withText={false} size="sm" />
          </span>
          <div className={styles.typingBubble}>
            <span className={styles.dot} />
            <span className={styles.dot} />
            <span className={styles.dot} />
          </div>
        </div>
      )}
    </div>
  )
}
