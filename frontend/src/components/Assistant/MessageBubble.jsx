import styles from "./MessageBubble.module.css"
import Icon from "../Icons/IconSet"
import Logo from "../Logo/Logo"
import { currentUser } from "../../demo"

function renderBold(text) {
  if (!text) return null
  const parts = text.split(/(\*\*.+?\*\*)/g)
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i}>{part.slice(2, -2)}</strong>
    ) : (
      <span key={i}>{part}</span>
    )
  )
}

const CONFIDENCE_COLOR = {
  High: "green",
  Medium: "orange",
  Low: "muted",
}

export default function MessageBubble({ message, isLast, isTyping, onFollowUpClick }) {
  if (message.role === "user") {
    return (
      <div className={styles.userRow}>
        <div className={styles.userBubble}>
          <p>{message.text}</p>
          {message.timeLabel && <span className={styles.timeLabel}>{message.timeLabel}</span>}
        </div>
        <span className={styles.userAvatar}>
          <Icon name="user" size={16} />
        </span>
      </div>
    )
  }

  const confidenceTone = CONFIDENCE_COLOR[message.confidence] || "muted"

  return (
    <div className={styles.assistantRow}>
      <div className={styles.assistantMain}>
      <span className={styles.assistantAvatar}>
        <Logo withText={false} size="sm" />
      </span>
      <div className={styles.assistantCard}>
        <div className={styles.cardHeader}>
          {message.jurisdictionBadge && (
            <span className={styles.jurisdictionBadge}>{message.jurisdictionBadge}</span>
          )}
          {message.confidence && (
            <span className={`${styles.confidenceTag} ${styles[confidenceTone]}`}>
              <span className={styles.confidenceDot} />
              {message.confidence} Confidence
            </span>
          )}
        </div>

        <p className={styles.answerText}>{renderBold(message.text)}</p>

        {message.evidence?.length > 0 && (
          <div className={styles.evidenceBlock}>
            <div className={styles.evidenceHeading}>
              <Icon name="document" size={14} />
              Key Evidence &amp; Sources
            </div>
            <div className={styles.evidenceGrid}>
              {message.evidence.map((ev) => {
                const Wrapper = ev.url ? "a" : "div"
                return (
                  <Wrapper
                    key={ev.key}
                    className={styles.evidenceCard}
                    {...(ev.url ? { href: ev.url, target: "_blank", rel: "noopener noreferrer" } : {})}
                  >
                    <span className={styles.evidenceIcon}>
                      <Icon name={ev.icon || "document"} size={16} />
                    </span>
                    <span className={styles.evidenceText}>
                      <span className={styles.evidenceTitle}>{ev.title}</span>
                      <span className={styles.evidenceSubtitle}>{ev.subtitle}</span>
                    </span>
                    {ev.url && <Icon name="external-link" size={13} className={styles.evidenceExternal} />}
                  </Wrapper>
                )
              })}
            </div>
          </div>
        )}

        {message.confidence && (
          <div className={styles.confidenceRow}>
            <span className={styles.confidenceRowLabel}>
              <Icon name="shield-check" size={13} />
              Confidence: {message.confidence}
              <Icon name="info" size={12} className={styles.infoIcon} />
            </span>
            <button type="button" className={styles.detailLink}>
              View detailed analysis
              <Icon name="arrow-right" size={13} />
            </button>
          </div>
        )}

        {message.relatedInsight && (
          <div className={styles.insightCallout}>
            <Icon name="lightbulb" size={17} className={styles.insightIcon} />
            <div className={styles.insightBody}>
              <span className={styles.insightTitle}>Related Insights</span>
              <p>{message.relatedInsight}</p>
            </div>
            <button type="button" className={styles.insightBtn}>
              View related queries
            </button>
          </div>
        )}
      </div>
      </div>

      {message.followUps?.length > 0 && isLast && !isTyping && (
        <div className={styles.followUpRow}>
          {message.followUps.map((q) => (
            <button key={q} type="button" className={styles.followUpChip} onClick={() => onFollowUpClick(q)}>
              {q}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
