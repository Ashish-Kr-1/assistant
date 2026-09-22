import styles from "./SideNav.module.css"
import Icon from "../Icons/IconSet"
import { sideNavItems, brand } from "../../demo"

export default function SideNav({ section, onSectionChange }) {
  return (
    <aside className={styles.sideNav}>
      <nav className={styles.nav}>
        {sideNavItems.map((item) => (
          <button
            key={item.key}
            type="button"
            className={`${styles.navItem} ${section === item.key ? styles.active : ""}`}
            onClick={() => onSectionChange(item.key)}
          >
            <Icon name={item.icon} size={18} />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className={styles.quoteBlock}>
        <p className={styles.quote}>&ldquo;{brand.quote}&rdquo;</p>
        <span className={styles.quoteRule} aria-hidden="true" />
      </div>
    </aside>
  )
}
