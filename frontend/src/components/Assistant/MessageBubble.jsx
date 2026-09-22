import { useEffect, useRef, useState } from "react"
import styles from "./MessageBubble.module.css"
import Icon from "../Icons/IconSet"
import Logo from "../Logo/Logo"

// ── Markdown renderer ─────────────────────────────────────────────────────────
// Converts a subset of markdown to React elements without any library dependency.
function renderMarkdown(text) {
  if (!text) return null
  const lines = text.split("\n")
  const elements = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i]

    // Blank line
    if (!line.trim()) {
      i++
      continue
    }

    // Heading h3
    if (line.startsWith("### ")) {
      elements.push(
        <h3 key={i} className={styles.mdH3}>{inlineFormat(line.slice(4))}</h3>
      )
      i++
      continue
    }

    // Heading h2
    if (line.startsWith("## ")) {
      elements.push(
        <h2 key={i} className={styles.mdH2}>{inlineFormat(line.slice(3))}</h2>
      )
      i++
      continue
    }

    // Heading h1
    if (line.startsWith("# ")) {
      elements.push(
        <h1 key={i} className={styles.mdH1}>{inlineFormat(line.slice(2))}</h1>
      )
      i++
      continue
    }

    // Horizontal rule
    if (/^---+$/.test(line.trim())) {
      elements.push(<hr key={i} className={styles.mdHr} />)
      i++
      continue
    }

    // Unordered list
    if (/^[-*] /.test(line)) {
      const items = []
      while (i < lines.length && /^[-*] /.test(lines[i])) {
        items.push(
          <li key={i} className={styles.mdLi}>
            {inlineFormat(lines[i].replace(/^[-*] /, ""))}
          </li>
        )
        i++
      }
      elements.push(<ul key={`ul-${i}`} className={styles.mdUl}>{items}</ul>)
      continue
    }

    // Ordered list
    if (/^\d+\. /.test(line)) {
      const items = []
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        items.push(
          <li key={i} className={styles.mdLi}>
            {inlineFormat(lines[i].replace(/^\d+\. /, ""))}
          </li>
        )
        i++
      }
      elements.push(<ol key={`ol-${i}`} className={styles.mdOl}>{items}</ol>)
      continue
    }

    // Blockquote
    if (line.startsWith("> ")) {
      elements.push(
        <blockquote key={i} className={styles.mdBlockquote}>
          {inlineFormat(line.slice(2))}
        </blockquote>
      )
      i++
      continue
    }

    // Default paragraph
    elements.push(
      <p key={i} className={styles.mdP}>{inlineFormat(line)}</p>
    )
    i++
  }

  return elements
}

// Inline formatting: **bold**, *italic*, `code`, [source N] citation chips
function inlineFormat(text) {
  if (!text) return null
  const parts = []
  // Split on bold (**text**), italic (*text*), inline code (`text`), citation [N]
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`|\[(\d+)\])/g
  let last = 0
  let match

  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) {
      parts.push(text.slice(last, match.index))
    }
    if (match[2]) {
      parts.push(<strong key={match.index}>{match[2]}</strong>)
    } else if (match[3]) {
      parts.push(<em key={match.index}>{match[3]}</em>)
    } else if (match[4]) {
      parts.push(<code key={match.index} className={styles.mdCode}>{match[4]}</code>)
    } else if (match[5]) {
      parts.push(
        <span key={match.index} className={styles.citationChip}>
          {match[5]}
        </span>
      )
    }
    last = match.index + match[0].length
  }

  if (last < text.length) {
    parts.push(text.slice(last))
  }

  return parts.length === 1 ? parts[0] : parts
}

// ── Streaming typewriter hook ─────────────────────────────────────────────────
function useTypewriter(fullText, isStreaming) {
  const [displayed, setDisplayed] = useState("")
  const indexRef = useRef(0)
  const timerRef = useRef(null)

  useEffect(() => {
    if (!isStreaming) {
      setDisplayed(fullText)
      return
    }

    // Reset when new message starts
    indexRef.current = 0
    setDisplayed("")

    function tick() {
      if (indexRef.current < fullText.length) {
        // Advance by 1-3 chars per tick for natural feel
        const step = fullText[indexRef.current] === " " ? 2 : 1
        indexRef.current = Math.min(indexRef.current + step, fullText.length)
        setDisplayed(fullText.slice(0, indexRef.current))
        timerRef.current = setTimeout(tick, 14)
      }
    }

    timerRef.current = setTimeout(tick, 40)
    return () => clearTimeout(timerRef.current)
  }, [fullText, isStreaming])

  return displayed
}

// ── Confidence colour map ─────────────────────────────────────────────────────
const CONFIDENCE_COLOR = { High: "green", Medium: "orange", Low: "muted" }

// ── Typing dots animation component ──────────────────────────────────────────
function TypingDots() {
  return (
    <div className={styles.typingRow}>
      <span className={styles.assistantAvatar}>
        <Logo withText={false} size="sm" />
      </span>
      <div className={styles.typingDots}>
        <span /><span /><span />
      </div>
    </div>
  )
}

// ── Intake question card ──────────────────────────────────────────────────────
function IntakeCard({ message }) {
  return (
    <div className={styles.assistantRow}>
      <div className={styles.assistantMain}>
        <span className={styles.assistantAvatar}>
          <Logo withText={false} size="sm" />
        </span>
        <div className={`${styles.assistantCard} ${styles.intakeCard}`}>
          <div className={styles.intakeHeader}>
            <span className={styles.intakeBadge}>
              <Icon name="search" size={11} />
              Deep Research · Case {message.caseId || ""}
            </span>
            {message.caseStatus && (
              <span className={styles.caseStatusPill}>
                {message.caseStatus.replace(/_/g, " ")}
              </span>
            )}
          </div>
          <div className={styles.intakeQuestion}>
            <Icon name="info" size={16} className={styles.intakeQuestionIcon} />
            <p>{message.text}</p>
          </div>
          {message.missingInfo?.length > 0 && (
            <div className={styles.intakeMissing}>
              <span className={styles.intakeMissingLabel}>Still needed:</span>
              <div className={styles.intakeMissingChips}>
                {message.missingInfo.map((m) => (
                  <span key={m} className={styles.intakeMissingChip}>{m}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export default function MessageBubble({
  message,
  isLast,
  isTyping,
  onFollowUpClick,
  onRetry,
}) {
  // Streaming typewriter for assistant messages
  const displayed = useTypewriter(
    message.role === "assistant" ? (message.text || "") : "",
    isLast && message.isStreaming === true
  )

  // User message
  if (message.role === "user") {
    return (
      <div className={styles.userRow}>
        <div className={styles.userBubble}>
          <p>{message.text}</p>
          {message.timeLabel && (
            <span className={styles.timeLabel}>{message.timeLabel}</span>
          )}
        </div>
        <span className={styles.userAvatar}>
          <Icon name="user" size={16} />
        </span>
      </div>
    )
  }

  // Typing indicator
  if (message.role === "typing") {
    return <TypingDots />
  }

  // Intake question card (deep research mode)
  if (message.isIntake) {
    return <IntakeCard message={message} />
  }

  // Error card
  if (message.isError) {
    return (
      <div className={styles.assistantRow}>
        <div className={styles.assistantMain}>
          <span className={styles.assistantAvatar}>
            <Logo withText={false} size="sm" />
          </span>
          <div className={`${styles.assistantCard} ${styles.errorCard}`}>
            <div className={styles.errorHeader}>
              <Icon name="info" size={15} />
              <span>Query Execution Issue</span>
            </div>
            <div className={styles.answerText}>
              {renderMarkdown(message.text)}
            </div>
            {message.failedQuery && onRetry && (
              <button
                type="button"
                className={styles.retryBtn}
                onClick={() => onRetry(message.failedQuery)}
              >
                <Icon name="sparkle" size={13} />
                Retry Query
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Standard assistant answer
  const confidenceTone = CONFIDENCE_COLOR[message.confidence] || "muted"
  const textToShow = message.isStreaming === true ? displayed : (message.text || "")
  const stillStreaming = message.isStreaming === true && displayed.length < (message.text || "").length

  return (
    <div className={styles.assistantRow}>
      <div className={styles.assistantMain}>
        <span className={styles.assistantAvatar}>
          <Logo withText={false} size="sm" />
        </span>

        <div className={styles.assistantCard}>
          {/* Header badges */}
          <div className={styles.cardHeader}>
            {message.jurisdictionBadge && (
              <span className={styles.jurisdictionBadge}>
                <Icon name="globe" size={11} />
                {message.jurisdictionBadge}
              </span>
            )}
            {message.confidence && (
              <span className={`${styles.confidenceTag} ${styles[confidenceTone]}`}>
                <span className={styles.confidenceDot} />
                {message.confidence} Confidence
              </span>
            )}
          </div>

          {/* Answer text with markdown + streaming cursor */}
          <div className={styles.answerBody}>
            <div className={styles.answerText}>
              {renderMarkdown(textToShow)}
            </div>
            {stillStreaming && (
              <span className={styles.streamCursor} aria-hidden="true">▊</span>
            )}
          </div>

          {/* Evidence / Sources — only after streaming finishes */}
          {!stillStreaming && message.evidence?.length > 0 && (
            <div className={styles.evidenceBlock}>
              <div className={styles.evidenceHeading}>
                <Icon name="document" size={14} />
                Key Evidence &amp; Statutory Sources
              </div>
              <div className={styles.evidenceGrid}>
                {message.evidence.map((ev, idx) => {
                  const Wrapper = ev.url ? "a" : "div"
                  return (
                    <Wrapper
                      key={ev.key}
                      className={styles.evidenceCard}
                      {...(ev.url
                        ? { href: ev.url, target: "_blank", rel: "noopener noreferrer" }
                        : {})}
                    >
                      <span className={styles.evidenceIndex}>{idx + 1}</span>
                      <span className={styles.evidenceIcon}>
                        <Icon name={ev.icon || "document"} size={14} />
                      </span>
                      <span className={styles.evidenceText}>
                        <span className={styles.evidenceTitle}>{ev.title}</span>
                        <span className={styles.evidenceSubtitle}>{ev.subtitle}</span>
                      </span>
                      {ev.url && (
                        <Icon
                          name="external-link"
                          size={12}
                          className={styles.evidenceExternal}
                        />
                      )}
                    </Wrapper>
                  )
                })}
              </div>
            </div>
          )}

          {/* Footer: confidence + view analysis */}
          {!stillStreaming && message.confidence && (
            <div className={styles.confidenceRow}>
              <span className={styles.confidenceRowLabel}>
                <Icon name="shield-check" size={13} />
                Verified answer · {message.confidence} confidence
              </span>
              {message.evidence?.length > 0 && (
                <span className={styles.sourceCount}>
                  {message.evidence.length} source{message.evidence.length !== 1 ? "s" : ""}
                </span>
              )}
            </div>
          )}

          {/* Related insight callout */}
          {!stillStreaming && message.relatedInsight && (
            <div className={styles.insightCallout}>
              <Icon name="lightbulb" size={16} className={styles.insightIcon} />
              <div className={styles.insightBody}>
                <span className={styles.insightTitle}>Related Insight</span>
                <p>{message.relatedInsight}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Follow-up suggestions */}
      {!stillStreaming && message.followUps?.length > 0 && isLast && !isTyping && (
        <div className={styles.followUpRow}>
          <span className={styles.followUpLabel}>Suggested follow-ups</span>
          <div className={styles.followUpChips}>
            {message.followUps.map((q) => (
              <button
                key={q}
                type="button"
                className={styles.followUpChip}
                onClick={() => onFollowUpClick(q)}
              >
                {q}
                <Icon name="arrow-right" size={12} />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
