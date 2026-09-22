import { Link } from "react-router-dom"
import { useState } from "react"
import styles from "./TopNav.module.css"
import Logo from "../Logo/Logo"
import Icon from "../Icons/IconSet"
import { topNavLinks, currentUser, languages } from "../../demo"

export default function TopNav({ section, onSectionChange, language, onLanguageChange }) {
  const [langOpen, setLangOpen] = useState(false)
  const [userOpen, setUserOpen] = useState(false)

  return (
    <header className={styles.topNav}>
      <Link to="/assistant" className={styles.brand} onClick={() => onSectionChange?.("assistant")}>
        <Logo />
      </Link>

      <nav className={styles.links}>
        {topNavLinks.map((link) => {
          const isActive = link.to ? section === "route-" + link.to : section === link.section
          const content = (
            <>
              {link.label}
              {link.dropdown && <Icon name="chevron-down" size={13} />}
            </>
          )
          if (link.to) {
            return (
              <Link
                key={link.key}
                to={link.to}
                className={`${styles.link} ${isActive ? styles.active : ""}`}
                onClick={() => onSectionChange?.(link.key === "home" ? "route-/" : "assistant")}
              >
                {content}
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
              {content}
            </button>
          )
        })}
      </nav>

      <div className={styles.actions}>
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

        <button type="button" className={styles.iconBtn} aria-label="Notifications">
          <Icon name="bell" size={18} />
        </button>

        <div className={styles.userWrap}>
          <button
            type="button"
            className={styles.userBtn}
            onClick={() => setUserOpen((v) => !v)}
            onBlur={() => setTimeout(() => setUserOpen(false), 120)}
          >
            <span className={styles.avatar}>{currentUser.initials}</span>
            <span className={styles.userName}>{currentUser.name}</span>
            <Icon name="chevron-down" size={13} />
          </button>
          {userOpen && (
            <div className={styles.userMenu}>
              <div className={styles.userMenuHeader}>
                <span className={styles.userMenuName}>{currentUser.name}</span>
                <span className={styles.userMenuRole}>{currentUser.role}</span>
              </div>
              <button type="button" className={styles.userMenuItem} onClick={() => onSectionChange?.("about")}>
                About IP-SAKTI
              </button>
              <button type="button" className={styles.userMenuItem} onClick={() => onSectionChange?.("expert-escalation")}>
                Expert Escalation
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
