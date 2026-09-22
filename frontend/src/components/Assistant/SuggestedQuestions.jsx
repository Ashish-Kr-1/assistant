import styles from "./SuggestedQuestions.module.css"
import Icon from "../Icons/IconSet"
import { suggestedQuestions } from "../../demo"

export default function SuggestedQuestions({ onSelect }) {
  return (
    <div className={styles.block}>
      <div className={styles.heading}>
        <Icon name="lightbulb" size={15} />
        Suggested questions
      </div>
      <div className={styles.list}>
        {suggestedQuestions.map((q) => (
          <button key={q} type="button" className={styles.item} onClick={() => onSelect(q)}>
            <span>{q}</span>
            <Icon name="chevron-right" size={16} />
          </button>
        ))}
      </div>
    </div>
  )
}
