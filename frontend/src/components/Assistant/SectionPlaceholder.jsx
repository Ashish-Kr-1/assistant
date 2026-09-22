import styles from "./SectionPlaceholder.module.css"
import Icon from "../Icons/IconSet"
import { placeholderSections } from "../../demo"

export default function SectionPlaceholder({ section, onOpenAssistant }) {
  const data = placeholderSections[section]
  if (!data) return null

  return (
    <div className={styles.wrap}>
      <div className={styles.header}>
        <span className={styles.icon}>
          <Icon name={data.icon} size={20} />
        </span>
        <div>
          <h2>{data.title}</h2>
          <p>{data.subtitle}</p>
        </div>
      </div>

      <div className={styles.list}>
        {data.items.map((item) => (
          <div key={item.title} className={styles.item}>
            <Icon name="chevron-right" size={15} className={styles.itemIcon} />
            <span className={styles.itemText}>
              <span className={styles.itemTitle}>{item.title}</span>
              <span className={styles.itemSubtitle}>{item.subtitle}</span>
            </span>
          </div>
        ))}
      </div>

      <button type="button" className={styles.cta} onClick={onOpenAssistant}>
        Ask IP-SAKTI about this
        <Icon name="arrow-right" size={14} />
      </button>
    </div>
  )
}
