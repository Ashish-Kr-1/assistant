import { Link } from "react-router-dom"
import styles from "./Home.module.css"
import Logo from "../../components/Logo/Logo"
import Icon from "../../components/Icons/IconSet"
import { brand, featureStrip } from "../../demo"

export default function Home() {
  return (
    <div className={styles.landing}>
      <div className={styles.leafDecor} aria-hidden="true" />

      <header className={styles.topBar}>
        <Logo />
        <Link to="/assistant" className={styles.navCta}>
          Ask {brand.name}
        </Link>
      </header>

      <main className={styles.hero}>
        <span className={styles.eyebrow}>India&rsquo;s traditional-knowledge IP companion</span>
        <h1 className={styles.title}>
          {brand.name} <span className={styles.titleAccent}>{brand.tagline}</span>
        </h1>
        <p className={styles.subtitle}>{brand.quote}</p>
        <p className={styles.description}>
          Evidence-backed guidance on patentability, ABS duties and regulatory classification for Ayurvedic and
          herbal innovations &mdash; every answer cited against the underlying statute, treaty or classical text.
        </p>

        <Link to="/assistant" className={styles.ctaBtn}>
          <span>Begin the Conversation</span>
          <Icon name="arrow-right" size={18} />
        </Link>

        <div className={styles.trustRow}>
          <span>Patents Act, 1970</span>
          <span className={styles.dot} />
          <span>TKDL</span>
          <span className={styles.dot} />
          <span>Nagoya Protocol</span>
        </div>
      </main>

      <section className={styles.features}>
        {featureStrip.map((f) => (
          <div className={styles.featureCard} key={f.key}>
            <span className={styles.featureIcon}>
              <Icon name={f.icon} size={18} />
            </span>
            <h3>{f.title}</h3>
            <p>{f.subtitle}</p>
          </div>
        ))}
      </section>

      <footer className={styles.footer}>
        Educational &amp; guidance purposes only — does not constitute formal legal advice.
      </footer>
    </div>
  )
}
