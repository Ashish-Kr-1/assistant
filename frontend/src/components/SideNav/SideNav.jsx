import styles from "./SideNav.module.css"
import Icon from "../Icons/IconSet"
import { sideNavItems, brand } from "../../demo"

export default function SideNav({ section, onSectionChange, onEscalate }) {
  return (
    <aside className={styles.sideNav}>
      <nav className={styles.nav}>
        {sideNavItems.map((item) => {
          const isEscalate = item.key === "expert-escalation"
          return (
            <button
              key={item.key}
              type="button"
              className={`${styles.navItem} ${!isEscalate && section === item.key ? styles.active : ""}`}
              onClick={() => {
                if (isEscalate) {
                  onEscalate?.()
                } else {
                  onSectionChange(item.key)
                }
              }}
            >
              <Icon name={item.icon} size={18} />
              <span>{item.label}</span>
            </button>
          )
        })}
      </nav>

      <div className={styles.quoteBlock}>
        <p className={styles.quote}>&ldquo;{brand.quote}&rdquo;</p>
        <span className={styles.quoteRule} aria-hidden="true" />
      </div>
    </aside>
  )
}
