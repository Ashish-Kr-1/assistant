import { useEffect, useState } from "react"
import styles from "./RightPanel.module.css"
import Icon from "../Icons/IconSet"
import { quickActions, recentQueries } from "../../demo"
import api from "../../api/axiosInstance"

const CONFIDENCE_DOT = {
  High:   "green",
  Medium: "orange",
  Low:    "muted",
}

function confidenceFromScore(score) {
  if (!score && score !== 0) return "Medium"
  if (score >= 0.85) return "High"
  if (score >= 0.50) return "Medium"
  return "Low"
}

export default function RightPanel({
  onQuickAction,
  onSelectRecentQuery,
  activeRecentId,
  onViewAllRecent,
  onEscalate,
  conversationId,
}) {
  const [recentHistory, setRecentHistory] = useState(recentQueries) // start with demo
  const [loadingHistory, setLoadingHistory] = useState(false)

  // Attempt to fetch real active case from backend on mount
  useEffect(() => {
    if (!conversationId) return
    setLoadingHistory(true)
    api
      .get(`/cases/active?conversation_id=${conversationId}&user_id=anonymous_user`)
      .then((res) => {
        const c = res.data
        if (!c) return
        // Build a synthetic recent-query entry from the active case
        const syntheticEntry = {
          id: c.case_id,
          question: c.title || c.profile?.innovation_name || "Deep Research Case",
          timeLabel: new Date(c.updated_at || Date.now()).toLocaleTimeString("en-IN", {
            hour: "2-digit",
            minute: "2-digit",
          }),
          jurisdiction: "India",
          confidence: confidenceFromScore(c.assessment?.confidence_score),
        }
        setRecentHistory((prev) => [syntheticEntry, ...prev.slice(0, 4)])
      })
      .catch(() => {
        // Backend not available — demo data stays
      })
      .finally(() => setLoadingHistory(false))
  }, [conversationId])

  return (
    <aside className={styles.panel}>
      {/* Quick Actions */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <span className={`${styles.sectionHeaderLeft} ${styles.boltHeader}`}>
            <Icon name="bolt" size={14} />
            Quick Actions
          </span>
        </div>
        <div className={styles.actionList}>
          {quickActions.map((action) => (
            <button
              key={action.key}
              type="button"
              className={styles.actionCard}
              onClick={() => onQuickAction(action.query)}
            >
              <span className={styles.actionIcon}>
                <Icon name={action.icon} size={16} />
              </span>
              <span className={styles.actionText}>
                <span className={styles.actionTitle}>{action.title}</span>
                <span className={styles.actionSubtitle}>{action.subtitle}</span>
              </span>
              <Icon name="chevron-right" size={14} className={styles.actionChevron} />
            </button>
          ))}
        </div>
      </section>

      {/* Recent Queries / Cases */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionHeaderLeft}>
            <Icon name="clock" size={14} />
            Recent Queries
            {loadingHistory && <span className={styles.loadingDot} />}
          </span>
          <button type="button" className={styles.viewAll} onClick={onViewAllRecent}>
            View all
            <Icon name="arrow-right" size={12} />
          </button>
        </div>
        <div className={styles.recentList}>
          {recentHistory.map((rq) => (
            <button
              key={rq.id}
              type="button"
              className={`${styles.recentItem} ${activeRecentId === rq.id ? styles.recentItemActive : ""}`}
              onClick={() => onSelectRecentQuery(rq.id)}
            >
              <span className={`${styles.recentDot} ${styles[CONFIDENCE_DOT[rq.confidence] || "muted"]}`} />
              <span className={styles.recentText}>
                <span className={styles.recentQuestion}>{rq.question}</span>
                <span className={styles.recentMeta}>
                  {rq.timeLabel} &middot; {rq.jurisdiction}
                </span>
              </span>
              <span className={`${styles.confidenceBadge} ${styles[CONFIDENCE_DOT[rq.confidence] || "muted"]}`}>
                {rq.confidence}
              </span>
            </button>
          ))}
        </div>
      </section>

      {/* Expert Escalation */}
      <section className={styles.expertCard}>
        <span className={styles.expertIcon}>
          <Icon name="user" size={18} />
        </span>
        <h4>Need Expert Guidance?</h4>
        <p>When your case requires professional interpretation, escalate directly to a certified IP professional.</p>
        <button type="button" className={styles.expertBtn} onClick={onEscalate}>
          Escalate to an Expert
          <Icon name="arrow-right" size={13} />
        </button>
      </section>
    </aside>
  )
}
