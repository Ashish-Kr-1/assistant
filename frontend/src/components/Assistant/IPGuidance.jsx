import styles from "./IPGuidance.module.css"
import Icon from "../Icons/IconSet"

const GUIDANCE_MODULES = [
  {
    id: "patents-act",
    title: "Indian Patents Act, 1970",
    subtitle: "Patentability Exclusions & Traditional Knowledge Bars",
    icon: "scale",
    color: "#dd8a3e",
    sections: [
      {
        ref: "Section 3(p)",
        title: "Traditional Knowledge Exclusion",
        summary:
          "An invention which in effect is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components is non-patentable.",
        checklist: [
          "Check classical text disclosure in TKDL (Charaka, Sushruta, Ashtanga Hridaya).",
          "Demonstrate non-obvious synergistic efficacy beyond mere addition of components.",
          "Consider patenting novel extraction, delivery, or processing methods rather than formulation composition.",
        ],
        query: "What are the patentability criteria and Section 3(p) TK defense strategies for my Ayurvedic innovation?",
      },
      {
        ref: "Section 3(d)",
        title: "Enhanced Efficacy Threshold",
        summary:
          "The mere discovery of a new form of a known substance which does not result in the enhancement of the known efficacy is not patentable.",
        checklist: [
          "Provide comparative in-vitro / in-vivo pharmacological data against the classical formulation.",
          "Show significant improvement in bioavailability, pharmacokinetic profile, or therapeutic index.",
        ],
        query: "How can I prove enhanced efficacy under Section 3(d) of the Patents Act for a modified herbal extract?",
      },
      {
        ref: "Section 3(e)",
        title: "Mere Admixture Bar",
        summary:
          "A substance obtained by a mere admixture resulting only in the aggregation of the properties of the components is not an invention.",
        checklist: [
          "Document synergistic interaction or biochemical interaction between active phytochemicals.",
          "Include statistical synergy calculation (e.g., Combination Index < 1).",
        ],
        query: "How do I overcome Section 3(e) mere admixture rejection for herbal combinations in India?",
      },
    ],
  },
  {
    id: "bda-act",
    title: "Biological Diversity Act, 2002",
    subtitle: "National Biodiversity Authority (NBA) & ABS Regulations",
    icon: "globe",
    color: "#0e4a52",
    sections: [
      {
        ref: "Section 6 (NBA Form III)",
        title: "Prior Approval for Patent Applications",
        summary:
          "No person shall apply for any intellectual property right in or outside India for any invention based on any research or information on a biological resource obtained from India without prior approval of the NBA.",
        checklist: [
          "File NBA Form III before patent grant (preferably concurrently with patent application).",
          "Specify the exact source and geographical origin of the biological material.",
          "Sign the formal Benefit-Sharing agreement with the NBA.",
        ],
        query: "What is the procedure for filing NBA Form III for patent applications based on Indian herbs?",
      },
      {
        ref: "Section 3 & 4 (NBA Form I)",
        title: "Bio-resource Access for Commercial Utilization",
        summary:
          "Certain individuals and foreign entities must obtain prior approval from the NBA before accessing any biological resource occurring in India for commercial utilization or biosurvey.",
        checklist: [
          "Determine applicant status: Indian citizens/entities vs foreign-held corporate entities.",
          "Check whether accessed ingredients are sourced from local cultivators or wild collection.",
          "Calculate applicable ABS royalty (typically 0.1% to 0.5% of ex-factory sale value).",
        ],
        query: "Do I need NBA Form I approval and what are the ABS royalty percentages under the Biological Diversity Act?",
      },
    ],
  },
  {
    id: "dca-act",
    title: "Drugs & Cosmetics Act, 1940 & Rules 1945",
    subtitle: "Ayurvedic Licensing vs Phytopharmaceutical Drug Pathway",
    icon: "document",
    color: "#3f9152",
    sections: [
      {
        ref: "Rule 158B",
        title: "Licensing of ASU (Ayurveda, Siddha, Unani) Medicines",
        summary:
          "Prescribes evidence requirements for manufacturing licenses: Classical formulations (cited in First Schedule texts) vs Patent/Proprietary ASU medicines (Bal/Siddha formulations).",
        checklist: [
          "Identify First Schedule authoritative text reference for classical medicines.",
          "For proprietary ASU drugs: Conduct acute toxicity studies and published safety evidence.",
          "Comply with Good Manufacturing Practices (GMP) under Schedule T.",
        ],
        query: "What is the difference between classical ASU license and proprietary medicine license under Rule 158B?",
      },
      {
        ref: "Rule 122E (Phytopharmaceuticals)",
        title: "Phytopharmaceutical Drug Pathway",
        summary:
          "Defined as purified and standardized fraction with minimum 4 active markers for therapeutic use. Follows modern drug clinical trial pathway under CDSCO.",
        checklist: [
          "Complete botanical characterization and fingerprinting (HPTLC / HPLC / LC-MS).",
          "Provide animal safety pharmacology, sub-acute toxicity, and mutagenicity profiles.",
          "Conduct Phase I to Phase III clinical trials as per New Drugs and Clinical Trials Rules 2019.",
        ],
        query: "What are the CDSCO regulatory requirements for a Phytopharmaceutical drug under Rule 122E?",
      },
    ],
  },
  {
    id: "fssai-act",
    title: "FSSAI (Food Safety & Standards) Regulations, 2022",
    subtitle: "Ayurveda Aahar & Nutraceutical Classification Boundaries",
    icon: "shield-check",
    color: "#8b5cf6",
    sections: [
      {
        ref: "Ayurveda Aahar Regs",
        title: "Ayurveda Aahar Regulatory Framework",
        summary:
          "Applies to food prepared in accordance with classical Ayurvedic texts. Cannot contain synthetic vitamins/minerals and cannot make disease-treatment or medical cure claims.",
        checklist: [
          "Ensure formulation adheres exclusively to ingredients listed in Schedule A.",
          "Display mandatory 'Ayurveda Aahar' logo and advisory statements on packaging.",
          "Confine label claims to physiological well-being, Rasayana, and nutritional balance.",
        ],
        query: "What claims are permitted on Ayurveda Aahar products and what is the food versus drug boundary?",
      },
    ],
  },
]

export default function IPGuidance({ onAskAssistant }) {
  return (
    <div className={styles.wrap}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.headerIcon}>
            <Icon name="document" size={20} />
          </span>
          <div>
            <h1 className={styles.title}>IP &amp; Regulatory Guidance</h1>
            <p className={styles.subtitle}>
              Authoritative statutory reference on patentability, bio-diversity access, and drug classification
            </p>
          </div>
        </div>
        <button
          type="button"
          className={styles.backBtn}
          onClick={() => onAskAssistant?.("Can you summarize the major IP laws applicable to Ayurvedic innovations?")}
        >
          <Icon name="chat" size={14} />
          Ask Assistant
        </button>
      </div>

      {/* Modules */}
      <div className={styles.modules}>
        {GUIDANCE_MODULES.map((module) => (
          <div key={module.id} className={styles.moduleCard}>
            <div className={styles.moduleHeader}>
              <span className={styles.moduleIcon} style={{ background: module.color }}>
                <Icon name={module.icon} size={16} />
              </span>
              <div>
                <h2 className={styles.moduleTitle}>{module.title}</h2>
                <span className={styles.moduleSubtitle}>{module.subtitle}</span>
              </div>
            </div>

            <div className={styles.sectionsList}>
              {module.sections.map((sec, idx) => (
                <div key={idx} className={styles.sectionItem}>
                  <div className={styles.sectionTop}>
                    <span className={styles.sectionRefBadge} style={{ color: module.color, background: `${module.color}15` }}>
                      {sec.ref}
                    </span>
                    <h3 className={styles.sectionHeading}>{sec.title}</h3>
                  </div>

                  <p className={styles.sectionSummary}>{sec.summary}</p>

                  <div className={styles.checklistBlock}>
                    <span className={styles.checklistLabel}>Key Due Diligence Checklist:</span>
                    <ul className={styles.checklistItems}>
                      {sec.checklist.map((item, ci) => (
                        <li key={ci}>
                          <Icon name="check" size={12} className={styles.checkIcon} />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <button
                    type="button"
                    className={styles.askButton}
                    onClick={() => onAskAssistant?.(sec.query)}
                  >
                    <Icon name="sparkle" size={13} />
                    <span>Ask Assistant about {sec.ref}</span>
                    <Icon name="arrow-right" size={12} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
