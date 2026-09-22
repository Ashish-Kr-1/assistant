import { useState } from "react"
import styles from "./EscalateModal.module.css"
import Icon from "../Icons/IconSet"

export default function EscalateModal({ onClose }) {
  const [submitted, setSubmitted] = useState(false)
  const [note, setNote] = useState("")

  function handleSubmit(e) {
    e.preventDefault()
    setSubmitted(true)
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h3>
            <Icon name="user" size={17} />
            Escalate to an Expert
          </h3>
          <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Close">
            <Icon name="x" size={16} />
          </button>
        </div>

        {submitted ? (
          <div className={styles.success}>
            <span className={styles.successIcon}>
              <Icon name="check" size={20} />
            </span>
            <p>Your request has been queued for a certified IP professional. They typically respond within one business day.</p>
            <button type="button" className={styles.doneBtn} onClick={onClose}>
              Close
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <p className={styles.intro}>
              Describe what you need reviewed, and a certified IP professional will follow up with tailored advice.
            </p>
            <textarea
              rows={5}
              required
              placeholder="e.g., I need help interpreting whether my formulation's ABS obligations apply before export…"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
            <div className={styles.footer}>
              <button type="button" className={styles.cancelBtn} onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className={styles.submitBtn}>
                Submit Request
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
