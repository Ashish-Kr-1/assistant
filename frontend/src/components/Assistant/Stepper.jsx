import styles from "./Stepper.module.css"
import Icon from "../Icons/IconSet"

const CASE_STEPS = [
  { key: "intake",     label: "Intake",     icon: "chat",           desc: "Collecting your formulation details" },
  { key: "assessment", label: "Assessment", icon: "scale",          desc: "Legal classification & IP domain mapping" },
  { key: "research",   label: "Research",   icon: "search",         desc: "Running CRAG queries across legal corpus" },
  { key: "report",     label: "Report",     icon: "shield-check",   desc: "8-section due diligence report ready" },
]

const QUERY_STEPS = [
  { key: "knowledge",  label: "Knowledge",  icon: "book" },
  { key: "source",     label: "Source",     icon: "document" },
  { key: "law",        label: "Law",        icon: "scale" },
  { key: "guidance",   label: "Guidance",   icon: "compass" },
]

// activeStep: -1 = no case, 0..3 = current step (0-indexed)
export default function Stepper({ mode = "query", activeStep = -1, caseId = null }) {
  if (mode === "deep_research" && activeStep >= 0) {
    return (
      <div className={styles.wrap}>
        {caseId && (
          <div className={styles.caseId}>
            <Icon name="document" size={12} />
            Case {caseId}
          </div>
        )}
        <div className={styles.caseSteps}>
          {CASE_STEPS.map((step, i) => {
            const isComplete = i < activeStep
            const isActive   = i === activeStep
            return (
              <div
                key={step.key}
                className={`${styles.caseStep} ${isComplete ? styles.complete : ""} ${isActive ? styles.active : ""}`}
              >
                <div className={styles.caseStepLeft}>
                  <span className={styles.caseCircle}>
                    {isComplete
                      ? <Icon name="shield-check" size={14} />
                      : <Icon name={step.icon} size={14} />
                    }
                  </span>
                  {i < CASE_STEPS.length - 1 && (
                    <span className={`${styles.caseLine} ${isComplete ? styles.caseLineComplete : ""}`} />
                  )}
                </div>
                <div className={styles.caseStepContent}>
                  <span className={styles.caseStepLabel}>{step.label}</span>
                  {isActive && (
                    <span className={styles.caseStepDesc}>{step.desc}</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  // Default: query mode stepper (static)
  return (
    <div className={styles.wrap}>
      <div className={styles.steps}>
        {QUERY_STEPS.map((step, i) => (
          <div className={styles.step} key={step.key}>
            <span className={styles.circle}>
              <Icon name={step.icon} size={15} />
            </span>
            <span className={styles.label}>{step.label}</span>
            {i < QUERY_STEPS.length - 1 && <span className={styles.line} aria-hidden="true" />}
          </div>
        ))}
      </div>
      <p className={styles.note}>
        <Icon name="document" size={12} />
        Answers include statutory sources and relevant sections where available.
      </p>
    </div>
  )
}
