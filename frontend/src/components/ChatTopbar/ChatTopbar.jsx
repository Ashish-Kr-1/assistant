import styles from "./ChatTopbar.module.css"
import { HamburgerIcon, SunIcon, MoonIcon } from "../Icons/Icons"

export default function ChatTopbar({
  sidebarOpen,
  onToggleSidebar,
  jurisdiction,
  onJurisdictionChange,
  theme,
  onToggleTheme,
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
          <div className={styles.sidebarBrandMark}>IS</div>
          <div className={styles.sidebarBrandText}>
            IP-SAKTI
            <span>Sahayak</span>
          </div>
        </div>
      )}
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
