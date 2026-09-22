import { useEffect, useState } from "react"
import styles from "./RightPanel.module.css"
import Icon from "../Icons/IconSet"
import { quickActions } from "../../demo"
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

function loadLocalHistory() {
  try {
    const raw = localStorage.getItem("ipsakti_recent_queries")
    return raw ? JSON.parse(raw) : []
  } catch (_) {
    return []
  }
}

export default function RightPanel({
  onQuickAction,
  onSelectRecentQuery,
  activeRecentId,
  onEscalate,
  conversationId,
}) {
  const [recentHistory, setRecentHistory] = useState(loadLocalHistory)
  const [loadingHistory, setLoadingHistory] = useState(false)

  // Listen to storage events to keep recent queries in sync across turns
  useEffect(() => {
    function handleStorageChange() {
      setRecentHistory(loadLocalHistory())
    }
    window.addEventListener("ipsakti_history_updated", handleStorageChange)
    return () => window.removeEventListener("ipsakti_history_updated", handleStorageChange)
  }, [])

  // Attempt to fetch real active case from backend on mount
  useEffect(() => {
    if (!conversationId) return
    setLoadingHistory(true)
    api
      .get(`/cases/active?conversation_id=${conversationId}&user_id=anonymous_user`)
      .then((res) => {
        const c = res.data
        if (!c || !c.case_id) return
        const syntheticEntry = {
          id: c.case_id,
          question: c.title || c.profile?.innovation_name || "Deep Research Case",
          timeLabel: new Date(c.updated_at || Date.now()).toLocaleTimeString("en-IN", {
            hour: "2-digit",
            minute: "2-digit",
          }),
          jurisdiction: "India",
          confidence: confidenceFromScore(c.assessment?.confidence_score),
          isCase: true,
        }
        setRecentHistory((prev) => {
          const filtered = prev.filter((p) => p.id !== c.case_id)
          return [syntheticEntry, ...filtered.slice(0, 5)]
        })
      })
      .catch(() => {})
      .finally(() => setLoadingHistory(false))
  }, [conversationId])

  function handleClearHistory() {
    try {
      localStorage.removeItem("ipsakti_recent_queries")
    } catch (_) {}
    setRecentHistory([])
  }

  return (
    <aside className={styles.panel}>
      {/* Quick Actions */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <span className={`${styles.sectionHeaderLeft} ${styles.boltHeader}`}>
            <Icon name="bolt" size={14} />
            Quick Assessment
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
          {recentHistory.length > 0 && (
            <button type="button" className={styles.clearBtn} onClick={handleClearHistory} title="Clear history">
              Clear
            </button>
          )}
        </div>

        {recentHistory.length === 0 ? (
          <div className={styles.emptyHistory}>
            <Icon name="clock" size={18} className={styles.emptyHistoryIcon} />
            <span>No recent queries yet. Your search history will appear here.</span>
          </div>
        ) : (
          <div className={styles.recentList}>
            {recentHistory.map((rq) => (
              <button
                key={rq.id}
                type="button"
                className={`${styles.recentItem} ${activeRecentId === rq.id ? styles.recentItemActive : ""}`}
                onClick={() => (onSelectRecentQuery ? onSelectRecentQuery(rq) : onQuickAction(rq.question))}
              >
                <span className={`${styles.recentDot} ${styles[CONFIDENCE_DOT[rq.confidence] || "muted"]}`} />
                <span className={styles.recentText}>
                  <span className={styles.recentQuestion}>{rq.question}</span>
                  <span className={styles.recentMeta}>
                    {rq.timeLabel} {rq.jurisdiction ? `· ${rq.jurisdiction}` : ""}
                  </span>
                </span>
                {rq.confidence && (
                  <span className={`${styles.confidenceBadge} ${styles[CONFIDENCE_DOT[rq.confidence] || "muted"]}`}>
                    {rq.confidence}
                  </span>
                )}
              </button>
            ))}
          </div>
        )}
      </section>

      {/* Expert Escalation */}
      <section className={styles.expertCard}>
        <span className={styles.expertIcon}>
          <Icon name="user" size={18} />
        </span>
        <h4>Need Expert Guidance?</h4>
        <p>When your case requires professional legal advice, escalate directly to a registered AYUSH patent agent.</p>
        <button type="button" className={styles.expertBtn} onClick={onEscalate}>
          Escalate to an Expert
          <Icon name="arrow-right" size={13} />
        </button>
      </section>
    </aside>
  )
}
