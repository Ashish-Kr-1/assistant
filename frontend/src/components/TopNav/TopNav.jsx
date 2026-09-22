import { Link } from "react-router-dom"
import { useState } from "react"
import styles from "./TopNav.module.css"
import Logo from "../Logo/Logo"
import Icon from "../Icons/IconSet"
import { topNavLinks, languages } from "../../demo"

export default function TopNav({
  section,
  onSectionChange,
  language,
  onLanguageChange,
  onNewChat,
}) {
  const [langOpen, setLangOpen] = useState(false)

  return (
    <header className={styles.topNav}>
      <Link to="/assistant" className={styles.brand} onClick={() => onSectionChange?.("assistant")}>
        <Logo />
      </Link>

      <nav className={styles.links}>
        {topNavLinks.map((link) => {
          const isActive = link.to ? section === "route-" + link.to : section === link.section
          if (link.to) {
            return (
              <Link
                key={link.key}
                to={link.to}
                className={`${styles.link} ${isActive ? styles.active : ""}`}
                onClick={() => onSectionChange?.(link.key === "home" ? "route-/" : "assistant")}
              >
                {link.label}
              </Link>
            )
          }
          return (
            <button
              key={link.key}
              type="button"
              className={`${styles.link} ${section === link.section ? styles.active : ""}`}
              onClick={() => onSectionChange?.(link.section)}
            >
              {link.label}
            </button>
          )
        })}
      </nav>

      <div className={styles.actions}>
        {onNewChat && (
          <button
            type="button"
            className={styles.newChatBtn}
            onClick={onNewChat}
            title="Start a new consultation session"
          >
            <Icon name="plus" size={13} />
            New Chat
          </button>
        )}

        <div className={styles.langWrap}>
          <button
            type="button"
            className={styles.langBtn}
            onClick={() => setLangOpen((v) => !v)}
            onBlur={() => setTimeout(() => setLangOpen(false), 120)}
          >
            {(languages.find((l) => l.code === language)?.code || "en").toUpperCase()}
            <Icon name="chevron-down" size={13} />
          </button>
          {langOpen && (
            <div className={styles.langMenu}>
              {languages.map((l) => (
                <button
                  key={l.code}
                  type="button"
                  className={styles.langOption}
                  onClick={() => {
                    onLanguageChange?.(l.code)
                    setLangOpen(false)
                  }}
                >
                  {l.label}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className={styles.userBadge} title="Active Innovator Workspace">
          <span className={styles.userBadgeAvatar}>IP</span>
          <span>Innovator</span>
        </div>
      </div>
    </header>
  )
}
