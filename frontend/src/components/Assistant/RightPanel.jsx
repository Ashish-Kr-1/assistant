import styles from "./RightPanel.module.css"
import Icon from "../Icons/IconSet"
import { quickActions, recentQueries } from "../../demo"

const CONFIDENCE_DOT = {
  High: "green",
  Medium: "orange",
  Low: "muted",
}

export default function RightPanel({ onQuickAction, onSelectRecentQuery, activeRecentId, onViewAllRecent, onEscalate }) {
  return (
    <aside className={styles.panel}>
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <span className={`${styles.sectionHeaderLeft} ${styles.boltHeader}`}>
            <Icon name="bolt" size={15} />
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
                <Icon name={action.icon} size={17} />
              </span>
              <span className={styles.actionText}>
                <span className={styles.actionTitle}>{action.title}</span>
                <span className={styles.actionSubtitle}>{action.subtitle}</span>
              </span>
              <Icon name="chevron-right" size={15} className={styles.actionChevron} />
            </button>
          ))}
        </div>
      </section>

      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionHeaderLeft}>
            <Icon name="clock" size={15} />
            Recent Queries
          </span>
          <button type="button" className={styles.viewAll} onClick={onViewAllRecent}>
            View all
            <Icon name="arrow-right" size={12} />
          </button>
        </div>
        <div className={styles.recentList}>
          {recentQueries.map((rq) => (
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

      <section className={styles.expertCard}>
        <span className={styles.expertIcon}>
          <Icon name="user" size={20} />
        </span>
        <h4>Need Expert Guidance?</h4>
        <p>When your case requires professional interpretation, escalate directly to a certified IP professional.</p>
        <button type="button" className={styles.expertBtn} onClick={onEscalate}>
          Escalate to an Expert
          <Icon name="arrow-right" size={14} />
        </button>
      </section>
    </aside>
  )
}
