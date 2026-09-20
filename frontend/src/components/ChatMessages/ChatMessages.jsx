import { Fragment } from "react"
import styles from "./ChatMessages.module.css"

/**
 * Lightweight zero-dependency markdown parser.
 * Handles: **bold**, *italic*, `code`, bullet lists (- item), numbered lists, double-newline paragraphs.
 */
function renderMarkdown(text) {
  if (!text) return null
  const lines = text.split("\n")
  const result = []
  let listBuffer = []
  let listType = null // 'ul' or 'ol'

  function flushList() {
    if (!listBuffer.length) return
    const Tag = listType === "ol" ? "ol" : "ul"
    result.push(
      <Tag key={`list-${result.length}`} style={{ margin: "6px 0 6px 18px", padding: 0 }}>
        {listBuffer.map((item, i) => (
          <li key={i} style={{ marginBottom: 3 }}>{renderInline(item)}</li>
        ))}
      </Tag>
    )
    listBuffer = []
    listType = null
  }

  lines.forEach((line, i) => {
    const ulMatch = line.match(/^[-*•]\s+(.+)/)
    const olMatch = line.match(/^\d+\.\s+(.+)/)
    if (ulMatch) {
      if (listType === "ol") flushList()
      listType = "ul"
      listBuffer.push(ulMatch[1])
    } else if (olMatch) {
      if (listType === "ul") flushList()
      listType = "ol"
      listBuffer.push(olMatch[1])
    } else {
      flushList()
      if (line.trim() === "") {
        result.push(<br key={`br-${i}`} />)
      } else {
        result.push(<span key={`ln-${i}`}>{renderInline(line)}<br /></span>)
      }
    }
  })
  flushList()
  return result
}

function renderInline(text) {
  const parts = []
  const re = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g
  let last = 0
  let m
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index))
    if (m[2]) parts.push(<strong key={m.index}>{m[2]}</strong>)
    else if (m[3]) parts.push(<em key={m.index}>{m[3]}</em>)
    else if (m[4]) parts.push(<code key={m.index} style={{ background: "rgba(0,0,0,.08)", padding: "1px 5px", borderRadius: 4, fontFamily: "monospace", fontSize: "0.9em" }}>{m[4]}</code>)
    last = m.index + m[0].length
  }
  if (last < text.length) parts.push(text.slice(last))
  return parts.length ? parts : text
}

/** Phase 3 Assessment bubble — rendered in-chat when a case reaches READY_FOR_RESEARCH */
function AssessmentBubble({ assessment }) {
  if (!assessment || assessment.assessment_status !== "COMPLETED") return null

  const cls = assessment.product_classification
  const ip = assessment.ip_domain
  const reg = assessment.regulatory_mapping
  const plan = assessment.research_plan
  const norm = assessment.normalized

  const priorityColor = { HIGH: "#b8834a", MEDIUM: "#6b7f5b", LOW: "#888" }

  return (
    <div className={styles.assessmentCard}>
      <div className={styles.assessmentHeader}>
        <span className={styles.assessmentBadge}>⚖ Phase 3 Assessment</span>
        <span className={styles.assessmentTitle}>
          {norm?.innovation_name || "Innovation"} — {cls?.category_name || "Classification"}
        </span>
      </div>

      {assessment.executive_summary && (
        <div className={styles.assessmentSection}>
          <div className={styles.sectionLabel}>Executive Summary</div>
          <div className={styles.assessmentBody}>{renderMarkdown(assessment.executive_summary)}</div>
        </div>
      )}

      {ip && (
        <div className={styles.assessmentSection}>
          <div className={styles.sectionLabel}>IP Domain &amp; Posture</div>
          <div className={styles.assessmentBody}>{renderMarkdown(ip.ip_posture)}</div>
          {ip.tkdl_relevance && ip.tkdl_note && (
            <div className={styles.assessmentNote}>🔍 {ip.tkdl_note}</div>
          )}
        </div>
      )}

      {reg?.jurisdiction_maps?.length > 0 && (
        <div className={styles.assessmentSection}>
          <div className={styles.sectionLabel}>Jurisdiction &amp; Regulatory Map</div>
          <div className={styles.jurisdictionGrid}>
            {reg.jurisdiction_maps.map((jm) => (
              <div key={jm.jurisdiction} className={styles.jurisdictionCard}>
                <div className={styles.jurName}>{jm.jurisdiction}</div>
                <div className={styles.jurAuthority}>{jm.regulatory_authority}</div>
                {jm.abs_applicable && <div className={styles.jurAbs}>⚠ ABS compliance required</div>}
                {jm.required_licenses?.length > 0 && (
                  <ul className={styles.jurList}>
                    {jm.required_licenses.slice(0, 2).map((l, i) => <li key={i}>{l}</li>)}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {plan?.research_tasks?.length > 0 && (
        <div className={styles.assessmentSection}>
          <div className={styles.sectionLabel}>Research Plan ({plan.research_tasks.length} tasks)</div>
          <div className={styles.researchTasks}>
            {plan.research_tasks.map((t) => (
              <div key={t.task_id} className={styles.researchTask}>
                <div className={styles.taskHeader}>
                  <span className={styles.taskId}>{t.task_id}</span>
                  <span className={styles.taskPriority} style={{ color: priorityColor[t.priority] }}>
                    ● {t.priority}
                  </span>
                  <span className={styles.taskTitle}>{t.title}</span>
                </div>
                <div className={styles.taskDesc}>{t.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {assessment.key_risks?.length > 0 && (
        <div className={styles.assessmentSection}>
          <div className={styles.sectionLabel}>Key Risks</div>
          <ul className={styles.riskList}>
            {assessment.key_risks.map((r, i) => <li key={i}>⚠ {r}</li>)}
          </ul>
        </div>
      )}

      {assessment.key_opportunities?.length > 0 && (
        <div className={styles.assessmentSection}>
          <div className={styles.sectionLabel}>Opportunities</div>
          <ul className={styles.opportunityList}>
            {assessment.key_opportunities.map((o, i) => <li key={i}>✓ {o}</li>)}
          </ul>
        </div>
      )}

      <div className={styles.assessmentDisclaimer}>{assessment.DISCLAIMER}</div>
    </div>
  )
}

/** Phase 4 Research Report bubble — rendered in-chat once the Research Engine has run */
function ReportBubble({ report }) {
  if (!report) return null
  const riskColor = { HIGH: "#c0392b", MEDIUM: "#b8834a", LOW: "#6b7f5b", UNKNOWN: "#888" }

  return (
    <div className={styles.assessmentCard}>
      <div className={styles.assessmentHeader}>
        <span className={styles.assessmentBadge}>📄 Phase 4 Research Report</span>
        <span className={styles.assessmentTitle}>
          Confidence: {report.overall_confidence_level}
          {report.needs_human_review ? " · ⚠ Human review recommended" : ""}
        </span>
      </div>

      <div className={styles.assessmentSection}>
        <div className={styles.sectionLabel}>Executive Summary</div>
        <div className={styles.assessmentBody}>{renderMarkdown(report.executive_summary)}</div>
      </div>

      {report.risks?.length > 0 && (
        <div className={styles.assessmentSection}>
          <div className={styles.sectionLabel}>Risk Assessment</div>
          <ul className={styles.riskList}>
            {report.risks.map((r, i) => (
              <li key={i} style={{ color: riskColor[r.level] || undefined }}>
                <strong>{r.risk}</strong> [{r.level}] — {r.reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {report.evidence?.length > 0 && (
        <div className={styles.assessmentSection}>
          <div className={styles.sectionLabel}>Evidence &amp; Sources ({report.evidence.length})</div>
          <ul className={styles.jurList}>
            {report.evidence.slice(0, 8).map((e) => (
              <li key={e.evidence_id}>
                [{e.source_tier}] {e.title || e.act_name || e.source} ({e.jurisdiction})
                {e.official_url ? (
                  <>
                    {" — "}
                    <a href={e.official_url} target="_blank" rel="noopener noreferrer">source</a>
                  </>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      )}

      {report.evidence_gaps?.length > 0 && (
        <div className={styles.assessmentSection}>
          <div className={styles.sectionLabel}>Evidence Gaps</div>
          <ul className={styles.riskList}>
            {report.evidence_gaps.map((g, i) => <li key={i}>⚠ {g}</li>)}
          </ul>
        </div>
      )}

      {report.recommended_next_steps?.length > 0 && (
        <div className={styles.assessmentSection}>
          <div className={styles.sectionLabel}>Recommended Next Steps</div>
          <ul className={styles.opportunityList}>
            {report.recommended_next_steps.map((s, i) => <li key={i}>✓ {s}</li>)}
          </ul>
        </div>
      )}

      <div className={styles.assessmentDisclaimer}>{report.DISCLAIMER}</div>
    </div>
  )
}

export default function ChatMessages({ messages, isTyping, onFollowUpClick, onGenerateReport, scrollRef }) {
  return (
    <div className={styles.messagesScroll} ref={scrollRef}>
      {messages.map((msg, index) => {
        const isLastMessage = index === messages.length - 1
        return (
          <Fragment key={msg.id}>
            <div className={`${styles.msgRow} ${styles[msg.role]}`}>
              <div className={`${styles.msgBubble} ${msg.role === "assistant" ? styles.nmRaised : ""}`}>
                {msg.role === "assistant" ? (
                  <>
                    {renderMarkdown(msg.text)}
                    {msg.isStreaming && <span className={styles.streamingCursor} aria-hidden="true" />}
                  </>
                ) : (
                  msg.text
                )}
                {!msg.isStreaming && msg.citations && msg.citations.length > 0 && (
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
            {/* Phase 3 Assessment panel — rendered once after the triggering message */}
            {msg.assessment && (
              <div className={`${styles.msgRow} ${styles.assistant}`}>
                <AssessmentBubble assessment={msg.assessment} />
              </div>
            )}
            {/* Phase 4 — offer to run the full evidence-backed research report */}
            {msg.assessment && !msg.report && (
              <div className={styles.followUpRow}>
                <button
                  type="button"
                  className={styles.followUpChip}
                  disabled={isTyping || msg.reportRequested}
                  onClick={() => onGenerateReport(msg.caseId, msg.id)}
                >
                  {msg.reportRequested ? "Generating report…" : "📄 Generate Full Research Report"}
                </button>
              </div>
            )}
            {msg.report && (
              <div className={`${styles.msgRow} ${styles.assistant}`}>
                <ReportBubble report={msg.report} />
              </div>
            )}
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
            <div className={styles.thinkingRow}>
              <span className={styles.typingDot} />
              <span className={styles.typingDot} />
              <span className={styles.typingDot} />
              <span className={styles.thinkingStatusText}>
                Retrieving legal corpus &amp; generating response…
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
