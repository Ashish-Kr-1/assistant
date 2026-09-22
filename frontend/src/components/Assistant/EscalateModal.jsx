import { useState } from "react"
import styles from "./EscalateModal.module.css"
import Icon from "../Icons/IconSet"
import api from "../../api/axiosInstance"
import { productCategories } from "../../demo"

export default function EscalateModal({ onClose, defaultCategory = "ayurvedic-formulation", defaultNote = "" }) {
  const [name, setName]         = useState("")
  const [email, setEmail]       = useState("")
  const [phone, setPhone]       = useState("")
  const [category, setCategory] = useState(defaultCategory)
  const [note, setNote]         = useState(defaultNote)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState("")
  const [result, setResult]     = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError("")

    try {
      const payload = {
        user_name: name.trim(),
        user_email: email.trim(),
        user_phone: phone.trim(),
        formulation_category: category,
        query_summary: note.trim(),
        preferred_facilitator_type: "Patent Agent (Ayurvedic/Pharma Specialization)",
      }

      const res = await api.post("/escalation/connect", payload)
      setResult(res.data)
    } catch (err) {
      setError(err.message || "Failed to submit escalation request. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h3>
            <Icon name="user" size={17} />
            Escalate to an IP Facilitator
          </h3>
          <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Close">
            <Icon name="x" size={16} />
          </button>
        </div>

        {result ? (
          <div className={styles.success}>
            <span className={styles.successIcon}>
              <Icon name="check" size={24} />
            </span>
            <h4 className={styles.successTitle}>Request Successfully Logged</h4>
            <div className={styles.ticketBadge}>
              <Icon name="document" size={13} />
              Reference Ticket: <strong>{result.reference_ticket_id}</strong>
            </div>
            <p className={styles.successMsg}>{result.message}</p>

            {result.matched_facilitators?.length > 0 && (
              <div className={styles.facilitatorsBlock}>
                <span className={styles.facilitatorsHeading}>Matched AYUSH IP Facilitators:</span>
                <div className={styles.facilitatorList}>
                  {result.matched_facilitators.map((fac, i) => (
                    <div key={i} className={styles.facilitatorCard}>
                      <span className={styles.facAvatar}>
                        <Icon name="user" size={15} />
                      </span>
                      <div className={styles.facDetails}>
                        <span className={styles.facName}>{fac.name}</span>
                        <span className={styles.facSpec}>{fac.specialization}</span>
                        <span className={styles.facLoc}>
                          <Icon name="globe" size={11} /> {fac.location}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button type="button" className={styles.doneBtn} onClick={onClose}>
              Done
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className={styles.form}>
            <p className={styles.intro}>
              Connect directly with registered patent agents and facilitators specializing in ASU
              formulations, Section 3(p) prior art defense, and Biological Diversity Act compliance.
            </p>

            {error && <div className={styles.errorNotice}>{error}</div>}

            <div className={styles.inputGroup}>
              <label>Your Full Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Dr. Rajesh Verma"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div className={styles.row}>
              <div className={styles.inputGroup}>
                <label>Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="name@domain.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className={styles.inputGroup}>
                <label>Phone Number</label>
                <input
                  type="tel"
                  required
                  placeholder="+91 98765 43210"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>
            </div>

            <div className={styles.inputGroup}>
              <label>Innovation Category</label>
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                {productCategories.map((c) => (
                  <option key={c.key} value={c.key}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>

            <div className={styles.inputGroup}>
              <label>Query Summary &amp; Key Issues</label>
              <textarea
                rows={4}
                required
                placeholder="Describe your formulation, herbs used, novel process, or specific ABS / patent issues needing expert review…"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
            </div>

            <div className={styles.footer}>
              <button type="button" className={styles.cancelBtn} onClick={onClose} disabled={loading}>
                Cancel
              </button>
              <button type="submit" className={styles.submitBtn} disabled={loading}>
                {loading ? "Connecting…" : "Submit Escalation"}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
