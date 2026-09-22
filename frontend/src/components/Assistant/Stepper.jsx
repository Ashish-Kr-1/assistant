import styles from "./Stepper.module.css"
import Icon from "../Icons/IconSet"
import { processSteps } from "../../demo"

export default function Stepper() {
  return (
    <div className={styles.wrap}>
      <div className={styles.steps}>
        {processSteps.map((step, i) => (
          <div className={styles.step} key={step.key}>
            <span className={styles.circle}>
              <Icon name={step.icon} size={16} />
            </span>
            <span className={styles.label}>{step.label}</span>
            {i < processSteps.length - 1 && <span className={styles.line} aria-hidden="true" />}
          </div>
        ))}
      </div>
      <p className={styles.note}>
        <Icon name="document" size={13} />
        Answers include sources and relevant sections where available.
      </p>
    </div>
  )
}
