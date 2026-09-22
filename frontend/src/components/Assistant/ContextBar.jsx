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
}) {
  const [justReset, setJustReset] = useState(false)

  function handleReset() {
    onResetContext?.()
    setJustReset(true)
    setTimeout(() => setJustReset(false), 1400)
  }

  return (
    <div className={styles.bar}>
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
              <Icon name={j.icon} size={14} />
              {j.label}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.group}>
        <span className={styles.groupLabel}>Product Category</span>
        <div className={styles.selectWrap}>
          <Icon name="leaf" size={14} className={styles.selectIcon} />
          <select value={category} onChange={(e) => onCategoryChange(e.target.value)}>
            {productCategories.map((c) => (
              <option key={c.key} value={c.key}>
                {c.label}
              </option>
            ))}
          </select>
          <Icon name="chevron-down" size={13} className={styles.selectChevron} />
        </div>
      </div>

      <div className={styles.group}>
        <span className={styles.groupLabel}>Language</span>
        <div className={styles.selectWrap}>
          <Icon name="globe" size={14} className={styles.selectIcon} />
          <select value={language} onChange={(e) => onLanguageChange(e.target.value)}>
            {languages.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
          <Icon name="chevron-down" size={13} className={styles.selectChevron} />
        </div>
      </div>

      <button type="button" className={styles.changeContext} onClick={handleReset}>
        <Icon name="document" size={13} />
        {justReset ? "Context reset" : "Change context"}
      </button>
    </div>
  )
}
