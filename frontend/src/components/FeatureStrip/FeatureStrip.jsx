import styles from "./FeatureStrip.module.css"
import Icon from "../Icons/IconSet"
import { featureStrip, processSteps } from "../../demo"

export default function FeatureStrip() {
  return (
    <footer className={styles.strip}>
      <div className={styles.features}>
        {featureStrip.map((f) => (
          <div className={styles.feature} key={f.key}>
            <span className={styles.featureIcon}>
              <Icon name={f.icon} size={16} />
            </span>
            <span className={styles.featureText}>
              <span className={styles.featureTitle}>{f.title}</span>
              <span className={styles.featureSubtitle}>{f.subtitle}</span>
            </span>
          </div>
        ))}
      </div>

      <div className={styles.stepper}>
        {processSteps.map((step, i) => (
          <span key={step.key} className={styles.stepperItem}>
            <span className={styles.stepperLabel}>{step.label}</span>
            {i < processSteps.length - 1 && <span className={styles.stepperLine} aria-hidden="true" />}
          </span>
        ))}
      </div>
    </footer>
  )
}
