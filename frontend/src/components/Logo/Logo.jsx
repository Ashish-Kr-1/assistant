import styles from "./Logo.module.css"
import Icon from "../Icons/IconSet"
import { brand } from "../../demo"

export default function Logo({ withText = true, size = "md" }) {
  return (
    <div className={`${styles.logo} ${styles[size]}`}>
      <span className={styles.mark}>
        <Icon name="leaf" size={size === "sm" ? 16 : 20} strokeWidth={2.2} />
      </span>
      {withText && (
        <span className={styles.text}>
          <span className={styles.name}>{brand.name}</span>
          <span className={styles.tagline}>{brand.tagline}</span>
        </span>
      )}
    </div>
  )
}
