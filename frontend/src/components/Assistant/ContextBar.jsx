import { useState } from "react"
import styles from "./ContextBar.module.css"
import Icon from "../Icons/IconSet"
import { jurisdictions, productCategories, languages } from "../../demo"

export default function ContextBar({
  jurisdiction,
  onJurisdictionChange,
  category,
  onCategoryChange,
  language,
  onLanguageChange,
  onResetContext,
  mode,
  onModeChange,
}) {
  const [justReset, setJustReset] = useState(false)

  function handleReset() {
    onResetContext?.()
    setJustReset(true)
    setTimeout(() => setJustReset(false), 1400)
  }

  return (
    <div className={styles.bar}>
      {/* ── Mode Toggle ──────────────────────────── */}
      <div className={styles.modeToggle}>
        <button
          type="button"
          className={`${styles.modeBtn} ${mode === "query" ? styles.modeBtnActive : ""}`}
          onClick={() => onModeChange?.("query")}
          aria-pressed={mode === "query"}
        >
          <Icon name="chat" size={13} />
          Query
        </button>
        <button
          type="button"
          className={`${styles.modeBtn} ${mode === "deep_research" ? styles.modeBtnActive : ""}`}
          onClick={() => onModeChange?.("deep_research")}
          aria-pressed={mode === "deep_research"}>
          <Icon name="search" size={13} />
          Deep Research
        </button>
      </div>

      <div className={styles.divider} aria-hidden="true" />

      {/* ── Jurisdiction ─────────────────────────── */}
      <div className={styles.group}>
        <span className={styles.groupLabel}>Jurisdiction</span>
        <div className={styles.pillRow}>
          {jurisdictions.map((j) => (
            <button
              key={j.key}
              type="button"
              className={`${styles.pill} ${jurisdiction === j.key ? styles.pillActive : ""}`}
              onClick={() => onJurisdictionChange(j.key)}
            >
              <Icon name={j.icon} size={13} />
              {j.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Category ─────────────────────────────── */}
      <div className={styles.group}>
        <span className={styles.groupLabel}>Category</span>
        <div className={styles.selectWrap}>
          <Icon name="leaf" size={13} className={styles.selectIcon} />
          <select value={category} onChange={(e) => onCategoryChange(e.target.value)}>
            {productCategories.map((c) => (
              <option key={c.key} value={c.key}>{c.label}</option>
            ))}
          </select>
          <Icon name="chevron-down" size={12} className={styles.selectChevron} />
        </div>
      </div>

      {/* ── Language ─────────────────────────────── */}
      <div className={styles.group}>
        <span className={styles.groupLabel}>Language</span>
        <div className={styles.selectWrap}>
          <Icon name="globe" size={13} className={styles.selectIcon} />
          <select value={language} onChange={(e) => onLanguageChange(e.target.value)}>
            {languages.map((l) => (
              <option key={l.code} value={l.code}>{l.label}</option>
            ))}
          </select>
          <Icon name="chevron-down" size={12} className={styles.selectChevron} />
        </div>
      </div>

      <button type="button" className={styles.changeContext} onClick={handleReset}>
        <Icon name="document" size={12} />
        {justReset ? "Context reset ✓" : "Reset context"}
      </button>
    </div>
  )
}
