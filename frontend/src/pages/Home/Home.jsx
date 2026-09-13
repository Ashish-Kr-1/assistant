import { Link } from "react-router-dom"
import styles from "./Home.module.css"

export default function Home() {
  return (
    <div className={styles.landing}>
      <div className={styles.bgOrbs} aria-hidden="true">
        <span className={styles.orb1} />
        <span className={styles.orb2} />
        <span className={styles.orb3} />
      </div>
      <div className={styles.grain} aria-hidden="true" />

      <main className={styles.hero}>
        <div className={styles.logoWrap}>
          <span className={styles.logoRing} />
          <span className={styles.logoMark}>IS</span>
        </div>

        <h1 className={styles.brandName}>
          IP-SAKTI
          <span className={styles.brandNameSub}>Sahayak</span>
        </h1>

        <p className={styles.tagline}>Ancient wisdom, rigorously defended.</p>

        <p className={styles.subtext}>
          Your guide through India&rsquo;s IP law, ABS duties, and traditional-knowledge
          protection — built for the ones who keep showing up, one question at a time.
        </p>

        <Link to="/chatbot" className={styles.ctaBtn}>
          <span>Begin the Conversation</span>
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={styles.ctaArrow}
            aria-hidden="true"
          >
            <line x1="4" y1="12" x2="20" y2="12" />
            <polyline points="13 5 20 12 13 19" />
          </svg>
        </Link>

        <div className={styles.trustRow}>
          <span>Patents Act</span>
          <span className={styles.dot} />
          <span>TKDL</span>
          <span className={styles.dot} />
          <span>Nagoya Protocol</span>
        </div>
      </main>

      <footer className={styles.footer}>
        Educational &amp; guidance purposes only — does not constitute formal legal advice.
      </footer>
    </div>
  )
}
