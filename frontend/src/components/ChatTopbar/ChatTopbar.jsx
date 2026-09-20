import styles from "./ChatTopbar.module.css"
import { HamburgerIcon, SunIcon, MoonIcon } from "../Icons/Icons"

export default function ChatTopbar({
  sidebarOpen,
  onToggleSidebar,
  jurisdiction,
  onJurisdictionChange,
  theme,
  onToggleTheme,
  mode = "query",
  onModeChange,
}) {
  return (
    <div className={styles.chatTopbar}>
      <button
        type="button"
        className={`${styles.hamburgerBtn} ${styles.nmRaised}`}
        onClick={onToggleSidebar}
        aria-label="Toggle chat history panel"
      >
        <HamburgerIcon />
      </button>
      {!sidebarOpen && (
        <div className={styles.topbarBrand}>
          <div className={styles.sidebarBrandMark}>CI</div>
          <div className={styles.sidebarBrandText}>
            Charaka IP
          </div>
        </div>
      )}

      {/* 2 Main Operation Modes: 1. Query (Default) | 2. Deep Research */}
      <div className={`${styles.modeToggle} ${styles.nmInset}`}>
        <button
          type="button"
          className={`${styles.modeBtn} ${mode === "query" ? styles.activeQuery : ""}`}
          onClick={() => onModeChange?.("query")}
          title="Direct AI Legal Q&A with statutory citations"
        >
          <span className={styles.modeIcon}>💬</span>
          <span>Query</span>
        </button>
        <button
          type="button"
          className={`${styles.modeBtn} ${mode === "deep_research" ? styles.activeDeepResearch : ""}`}
          onClick={() => onModeChange?.("deep_research")}
          title="Comprehensive Innovation Intake, Assessment & Deep Research Report"
        >
          <span className={styles.modeIcon}>🔬</span>
          <span>Deep Research</span>
        </button>
      </div>

      <div className={`${styles.jurisdictionToggle} ${styles.nmInset}`}>
        <button
          type="button"
          className={jurisdiction === "national" ? `${styles.active} ${styles.national}` : ""}
          onClick={() => onJurisdictionChange("national")}
        >
          National
        </button>
        <button
          type="button"
          className={jurisdiction === "international" ? `${styles.active} ${styles.international}` : ""}
          onClick={() => onJurisdictionChange("international")}
        >
          International
        </button>
      </div>
      <button
        type="button"
        className={`${styles.themeToggle} ${styles.nmInset}`}
        onClick={onToggleTheme}
        aria-label="Toggle light/dark theme"
      >
        <SunIcon />
        <span className={`${styles.themeToggleThumb}${theme === "dark" ? ` ${styles.dark}` : ""}`} />
        <MoonIcon />
      </button>
    </div>
  )
}
