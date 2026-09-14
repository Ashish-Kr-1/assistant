import { useState, useRef, useEffect } from "react"
import styles from "./BackendTerminal.module.css"

export default function BackendTerminal({ logs = [], isRunning = false, onClear }) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isMaximized, setIsMaximized] = useState(false)
  const terminalEndRef = useRef(null)

  useEffect(() => {
    if (!isCollapsed) {
      terminalEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }
  }, [logs, isCollapsed, isRunning])

  function formatLogLine(line) {
    if (!line) return null

    // Pattern: YYYY-MM-DD HH:MM:SS,mmm [LEVEL] module: message
    const match = line.match(/^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d{3})?)\s+\[(INFO|WARNING|ERROR|DEBUG)\]\s+([^:]+):\s*(.*)$/)
    if (!match) {
      // Fallback formatting
      const isWarn = line.includes("[WARNING]") || line.includes("429")
      const isErr = line.includes("[ERROR]") || line.includes("Failed")
      return (
        <span className={isErr ? styles.levelError : isWarn ? styles.levelWarning : styles.msgText}>
          {line}
        </span>
      )
    }

    const [, timestamp, level, moduleName, message] = match
    const levelClass =
      level === "ERROR"
        ? styles.levelError
        : level === "WARNING"
        ? styles.levelWarning
        : styles.levelInfo

    return (
      <div className={styles.logRow}>
        <span className={styles.timestamp}>{timestamp.slice(11)}</span>
        <span className={`${styles.levelBadge} ${levelClass}`}>[{level}]</span>
        <span className={styles.moduleName}>{moduleName}:</span>
        <span className={styles.messageContent}>
          {message}
        </span>
      </div>
    )
  }

  return (
    <div
      className={`${styles.terminalContainer} ${isCollapsed ? styles.collapsed : ""} ${
        isMaximized ? styles.maximized : ""
      }`}
    >
      <div className={styles.terminalHeader}>
        <div className={styles.windowControls}>
          <span className={`${styles.dot} ${styles.dotRed}`} onClick={() => setIsCollapsed(!isCollapsed)} title="Minimize" />
          <span className={`${styles.dot} ${styles.dotYellow}`} onClick={() => setIsMaximized(!isMaximized)} title="Resize" />
          <span className={`${styles.dot} ${styles.dotGreen}`} title="Online" />
        </div>

        <div className={styles.terminalTitle}>
          <span className={styles.terminalPrompt}>$</span> uvicorn : 8000
          {isRunning ? (
            <span className={styles.runningBadge}>
              <span className={styles.pulseDot} /> RUNNING
            </span>
          ) : (
            <span className={styles.idleBadge}>● IDLE</span>
          )}
        </div>

        <div className={styles.terminalActions}>
          {onClear && (
            <button
              type="button"
              className={styles.headerBtn}
              onClick={onClear}
              title="Clear terminal"
            >
              Clear
            </button>
          )}
          <button
            type="button"
            className={styles.headerBtn}
            onClick={() => setIsCollapsed(!isCollapsed)}
            title={isCollapsed ? "Expand" : "Collapse"}
          >
            {isCollapsed ? "▲" : "▼"}
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <div className={styles.terminalBody}>
          {logs.length === 0 ? (
            <div className={styles.emptyPrompt}>
              <span className={styles.promptPrefix}>backend@assistant:~$</span> Waiting for incoming queries...
            </div>
          ) : (
            logs.map((line, idx) => (
              <div key={idx} className={styles.logLine}>
                {formatLogLine(line)}
              </div>
            ))
          )}
          {isRunning && (
            <div className={styles.inFlightIndicator}>
              <span className={styles.spinner} />
              <span className={styles.inFlightText}>CRAG pipeline executing in background...</span>
            </div>
          )}
          <div ref={terminalEndRef} />
        </div>
      )}
    </div>
  )
}
