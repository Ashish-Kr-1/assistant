// Centralized demo/mock data for IP-SAKTI Sahayak.
// Anything the live backend doesn't yet serve (nav content, quick actions,
// recent-query history, canned answers) lives here so the UI stays fully
// interactive/testable with the FastAPI backend offline.

export const brand = {
  name: "IP-SAKTI",
  tagline: "Sahayak",
  quote: "From ancient wisdom to modern protection.",
}

export const currentUser = {
  name: "Udit Kumar Mahato",
  initials: "UK",
  role: "Innovator",
}

export const jurisdictions = [
  { key: "india", label: "India", icon: "flag-india" },
  { key: "international", label: "International", icon: "globe" },
]

export const productCategories = [
  { key: "ayurvedic-formulation", label: "Ayurvedic Formulation" },
  { key: "herbal-cosmetic", label: "Herbal Cosmetic" },
  { key: "nutraceutical", label: "Nutraceutical / Ayurveda-Aahar" },
  { key: "phytopharmaceutical", label: "Phytopharmaceutical Drug" },
  { key: "process-innovation", label: "Process / Extraction Innovation" },
]

export const languages = [
  { code: "en", label: "English" },
  { code: "hi", label: "Hindi" },
  { code: "bn", label: "Bengali" },
  { code: "ta", label: "Tamil" },
  { code: "te", label: "Telugu" },
  { code: "mr", label: "Marathi" },
  { code: "gu", label: "Gujarati" },
  { code: "kn", label: "Kannada" },
  { code: "ml", label: "Malayalam" },
  { code: "pa", label: "Punjabi" },
]

// First few shown as quick pills in the composer; the rest roll into "+N more".
export const composerLanguagePills = languages.slice(0, 6)

export const topNavLinks = [
  { key: "home", label: "Home", to: "/" },
  { key: "assistant", label: "Ask IP-SAKTI", to: "/assistant" },
  { key: "ip-guidance", label: "IP Guidance", section: "ip-guidance", dropdown: true },
  { key: "resources", label: "Resources", section: "resources", dropdown: true },
  { key: "about", label: "About", section: "about", dropdown: true },
]

export const sideNavItems = [
  { key: "assistant", label: "AI Assistant", icon: "chat" },
  { key: "ip-guidance", label: "IP Guidance", icon: "document" },
  { key: "knowledge-base", label: "Knowledge Base", icon: "book" },
  { key: "query-history", label: "Query History", icon: "clock" },
  { key: "expert-escalation", label: "Expert Escalation", icon: "user" },
  { key: "resources", label: "Resources", icon: "folder" },
  { key: "about", label: "About", icon: "info" },
]

export const suggestedQuestions = [
  "Can this formulation be patented?",
  "Is this traditional knowledge already documented?",
  "What regulations apply to my product?",
]

export const processSteps = [
  { key: "knowledge", label: "Knowledge", icon: "book" },
  { key: "source", label: "Source", icon: "document" },
  { key: "law", label: "Law", icon: "scale" },
  { key: "guidance", label: "Guidance", icon: "compass" },
]

export const quickActions = [
  {
    key: "patent-eligibility",
    icon: "shield-check",
    title: "Check Patent Eligibility",
    subtitle: "Get preliminary assessment",
    query: "Can my Ayurvedic formulation be patented in India?",
  },
  {
    key: "regulatory",
    icon: "shield",
    title: "Verify Regulatory Requirements",
    subtitle: "AYUSH, FSSAI, CDSCO etc.",
    query: "What regulatory approvals (AYUSH, FSSAI, CDSCO) apply to my product?",
  },
  {
    key: "tkdl",
    icon: "search",
    title: "Search Traditional Knowledge",
    subtitle: "TKDL & classical texts",
    query: "Is this formulation already documented in TKDL or classical texts?",
  },
  {
    key: "acts",
    icon: "document",
    title: "Find Relevant Acts & Rules",
    subtitle: "With section references",
    query: "Which Acts and Rules are relevant to my Ayurvedic product?",
  },
]

export const recentQueries = [
  {
    id: "rq-1",
    question: "Can this Ayurvedic formulation be patented?",
    timeLabel: "Today",
    jurisdiction: "India",
    confidence: "High",
  },
  {
    id: "rq-2",
    question: "Does this product require FSSAI compliance?",
    timeLabel: "Yesterday",
    jurisdiction: "India",
    confidence: "Medium",
  },
  {
    id: "rq-3",
    question: "Is this traditional knowledge already documented?",
    timeLabel: "2 days ago",
    jurisdiction: "India",
    confidence: "High",
  },
  {
    id: "rq-4",
    question: "What are the international IP rights for herbal products?",
    timeLabel: "3 days ago",
    jurisdiction: "International",
    confidence: "Medium",
  },
]

export const featureStrip = [
  {
    key: "evidence",
    icon: "book",
    title: "Evidence-First",
    subtitle: "Cited sources, not just answers",
  },
  {
    key: "jurisdiction",
    icon: "globe",
    title: "Jurisdiction-Aware",
    subtitle: "India & International regimes",
  },
  {
    key: "multilingual",
    icon: "chat",
    title: "Multilingual",
    subtitle: "22+ Indian languages",
  },
  {
    key: "human",
    icon: "user",
    title: "Human-in-the-Loop",
    subtitle: "AI guidance + expert support",
  },
]

// The seeded conversation shown on first load, matching the reference design.
export const initialConversation = [
  {
    id: "m-1",
    role: "user",
    text: "Can this Ayurvedic formulation be patented?",
    timeLabel: "10:24 AM",
  },
  {
    id: "m-2",
    role: "assistant",
    jurisdictionBadge: "INDIA",
    confidence: "High",
    text:
      "Based on the information provided, your Ayurvedic formulation **may require further assessment** before determining **patent eligibility**. Since it uses known traditional ingredients, it may be considered prior art under Section 3(p) of the Indian Patents Act. However, if it demonstrates novelty, inventive step and industrial application, it could still be eligible for a patent.",
    evidence: [
      {
        key: "patents-act",
        icon: "document",
        title: "Indian Patents Act, 1970",
        subtitle: "Section 3(p) – Exclusions",
        url: "https://www.indiacode.nic.in/handle/123456789/1989",
      },
      {
        key: "tkdl",
        icon: "book",
        title: "TKDL Database",
        subtitle: "Classical formulation match",
        url: "",
      },
      {
        key: "patent-office",
        icon: "shield-check",
        title: "Patent Office of India",
        subtitle: "Guidelines on patentability",
        url: "",
      },
    ],
    relatedInsight:
      "You may also want to check if the formulation is covered under TKDL or has been disclosed in any prior art publications.",
    followUps: [
      "Can this formulation be trademarked?",
      "Does it require FSSAI approval?",
      "What are the IP rights for herbal products?",
    ],
  },
]

// Loaded when a Recent Query row is clicked, so the history panel feels alive.
export const recentQueryConversations = {
  "rq-1": initialConversation,
  "rq-2": [
    {
      id: "rq2-1",
      role: "user",
      text: "Does this product require FSSAI compliance?",
      timeLabel: "Yesterday",
    },
    {
      id: "rq2-2",
      role: "assistant",
      jurisdictionBadge: "INDIA",
      confidence: "Medium",
      text:
        "If your product is consumed as a food or dietary supplement rather than administered as a medicine, it likely falls under **FSSAI's Ayurveda Aahar** framework rather than the Drugs & Cosmetics Act. You would need to verify ingredient limits, labelling claims and whether any ingredient requires prior FSSAI approval as a novel food.",
      evidence: [
        {
          key: "fssai",
          icon: "shield",
          title: "FSSAI Ayurveda Aahar Regulations, 2022",
          subtitle: "Scope & permitted ingredients",
          url: "",
        },
        {
          key: "dca",
          icon: "document",
          title: "Drugs & Cosmetics Act, 1940",
          subtitle: "Rule 158B – classification boundary",
          url: "",
        },
      ],
      relatedInsight:
        "Products straddling the food/drug boundary are frequently escalated — consider a formal classification opinion before packaging claims are finalised.",
      followUps: [
        "What separates a food claim from a drug claim?",
        "Does this need CDSCO approval instead?",
      ],
    },
  ],
  "rq-3": [
    {
      id: "rq3-1",
      role: "user",
      text: "Is this traditional knowledge already documented?",
      timeLabel: "2 days ago",
    },
    {
      id: "rq3-2",
      role: "assistant",
      jurisdictionBadge: "INDIA",
      confidence: "High",
      text:
        "A search against the **Traditional Knowledge Digital Library (TKDL)** suggests formulations using this ingredient combination appear in classical texts such as the Charaka Samhita. This constitutes documented prior art, which would bar a product patent on the formulation itself, though process innovations may remain patentable.",
      evidence: [
        {
          key: "tkdl-2",
          icon: "book",
          title: "TKDL Database",
          subtitle: "Classical text cross-reference",
          url: "",
        },
        {
          key: "charaka",
          icon: "document",
          title: "Charaka Samhita (First Schedule Text)",
          subtitle: "Classical formulation reference",
          url: "",
        },
      ],
      relatedInsight:
        "Consider whether a novel extraction process or delivery method could still be independently patentable.",
      followUps: ["What counts as a novel process modification?", "Can this formulation be trademarked?"],
    },
  ],
  "rq-4": [
    {
      id: "rq4-1",
      role: "user",
      text: "What are the international IP rights for herbal products?",
      timeLabel: "3 days ago",
    },
    {
      id: "rq4-2",
      role: "assistant",
      jurisdictionBadge: "INTERNATIONAL",
      confidence: "Medium",
      text:
        "Internationally, herbal product protection depends heavily on jurisdiction. Under the **WIPO PCT**, you can file a single international application, but each designated country applies its own patentability and traditional-knowledge exclusions. The **Nagoya Protocol** also requires prior informed consent and benefit-sharing when genetic resources or associated traditional knowledge are used across borders.",
      evidence: [
        {
          key: "pct",
          icon: "globe",
          title: "WIPO Patent Cooperation Treaty",
          subtitle: "Article 3 – international application",
          url: "",
        },
        {
          key: "nagoya",
          icon: "shield",
          title: "Nagoya Protocol on ABS",
          subtitle: "Prior informed consent & benefit-sharing",
          url: "",
        },
      ],
      relatedInsight:
        "If you plan to export, map each target market's ABS and patentability rules separately — they are not harmonised.",
      followUps: ["What is required for ABS prior informed consent?", "Which countries exclude traditional knowledge from patents?"],
    },
  ],
}

// --- Fallback answer engine -------------------------------------------------
// Used only when the live /query API call fails (e.g. backend not running),
// so the demo stays fully clickable end-to-end without a server.

const DEMO_ANSWER_BANK = [
  {
    match: /trademark/i,
    jurisdictionBadge: "INDIA",
    confidence: "Medium",
    text:
      "A **product name or brand** associated with your formulation can generally be trademarked under the Trade Marks Act, 1999, independent of whether the formulation itself is patentable. However, purely descriptive or generic Ayurvedic terms (e.g. the classical formulation name itself) are unlikely to be registrable.",
    evidence: [
      { key: "tm-act", icon: "document", title: "Trade Marks Act, 1999", subtitle: "Section 9 – absolute grounds for refusal", url: "" },
      { key: "tm-registry", icon: "shield-check", title: "Trade Marks Registry", subtitle: "Class 5 – pharmaceutical & Ayurvedic goods", url: "" },
    ],
    relatedInsight: "Consider a trademark clearance search before committing to a product name.",
    followUps: ["What trademark class applies to Ayurvedic products?", "Can a Sanskrit term be trademarked?"],
  },
  {
    match: /fssai|food/i,
    jurisdictionBadge: "INDIA",
    confidence: "Medium",
    text:
      "If marketed as a food supplement rather than a medicine, your product likely falls under **FSSAI's Ayurveda Aahar Regulations, 2022**. You'll need to confirm permitted ingredient limits and ensure labelling doesn't make disease-cure claims, which would push it into drug classification instead.",
    evidence: [
      { key: "fssai-2", icon: "shield", title: "FSSAI Ayurveda Aahar Regulations, 2022", subtitle: "Permitted ingredients & claims", url: "" },
    ],
    relatedInsight: "Disease-related claims on packaging are the most common reason for reclassification disputes.",
    followUps: ["What claims are allowed on the label?", "Does this need CDSCO approval instead?"],
  },
  {
    match: /herbal|international|export|abs|nagoya/i,
    jurisdictionBadge: "INTERNATIONAL",
    confidence: "Medium",
    text:
      "For herbal products crossing borders, protection is jurisdiction-specific. The **Nagoya Protocol** requires prior informed consent and benefit-sharing whenever genetic resources or associated traditional knowledge are accessed for commercial use abroad.",
    evidence: [
      { key: "nagoya-2", icon: "shield", title: "Nagoya Protocol on ABS", subtitle: "Prior informed consent & benefit-sharing", url: "" },
    ],
    relatedInsight: "Map ABS requirements separately for each export market — they are not harmonised.",
    followUps: ["What counts as prior informed consent?", "Which countries require ABS clearance?"],
  },
  {
    match: /tkdl|traditional knowledge|prior art|documented/i,
    jurisdictionBadge: "INDIA",
    confidence: "High",
    text:
      "A TKDL search is the standard first step to check whether your formulation (or close variants) already appear in classical Ayurvedic, Siddha or Unani texts. A match constitutes documented prior art and would bar a straightforward product patent, though genuinely novel process or delivery innovations may remain patentable.",
    evidence: [
      { key: "tkdl-3", icon: "book", title: "TKDL Database", subtitle: "Classical formulation match", url: "" },
    ],
    relatedInsight: "A negative TKDL result strengthens — but doesn't guarantee — a novelty argument.",
    followUps: ["What counts as a novel process modification?", "Can this formulation be trademarked?"],
  },
]

const DEFAULT_DEMO_ANSWER = {
  jurisdictionBadge: "INDIA",
  confidence: "Medium",
  text:
    "Based on the information provided, this may require further assessment against the relevant statute before a definitive answer can be given. In general, formulations built directly from known traditional ingredients face a higher bar under **Section 3(p)** of the Indian Patents Act, while genuinely novel processes, combinations or delivery methods have a stronger patentability case.",
  evidence: [
    { key: "patents-act-d", icon: "document", title: "Indian Patents Act, 1970", subtitle: "Section 3(p) – Exclusions", url: "https://www.indiacode.nic.in/handle/123456789/1989" },
    { key: "tkdl-d", icon: "book", title: "TKDL Database", subtitle: "Classical formulation match", url: "" },
  ],
  relatedInsight: "You may also want to check if the formulation is covered under TKDL or has been disclosed in any prior art publications.",
  followUps: ["Can this formulation be trademarked?", "Does it require FSSAI approval?", "What are the IP rights for herbal products?"],
}

export function getDemoAnswer(query) {
  const match = DEMO_ANSWER_BANK.find((entry) => entry.match.test(query))
  const base = match || DEFAULT_DEMO_ANSWER
  return { ...base, text: base.text }
}

export const placeholderSections = {
  "ip-guidance": {
    title: "IP Guidance",
    subtitle: "Step-by-step guidance for protecting Ayurvedic innovations.",
    icon: "document",
    items: [
      { title: "Patentability checklist for Ayurvedic formulations", subtitle: "Novelty, inventive step & Section 3(p) screening" },
      { title: "Trademark filing walkthrough", subtitle: "Choosing a class, clearance search, registration" },
      { title: "Geographical Indication (GI) protection", subtitle: "When a region-linked product qualifies" },
      { title: "ABS & Nagoya Protocol compliance", subtitle: "Prior informed consent and benefit-sharing steps" },
    ],
  },
  "knowledge-base": {
    title: "Knowledge Base",
    subtitle: "Search classical texts, statutes and prior TKDL matches.",
    icon: "book",
    items: [
      { title: "TKDL classical formulation search", subtitle: "Charaka, Sushruta & Ashtanga Hridaya cross-reference" },
      { title: "Indian Patents Act, 1970 — annotated", subtitle: "Section-by-section commentary" },
      { title: "FSSAI Ayurveda Aahar Regulations, 2022", subtitle: "Full text with permitted-ingredient schedules" },
      { title: "WIPO Traditional Knowledge resources", subtitle: "International frameworks & case studies" },
    ],
  },
  resources: {
    title: "Resources",
    subtitle: "Official portals, forms and reference material.",
    icon: "folder",
    items: [
      { title: "Indian Patent Office — e-filing portal", subtitle: "ipindiaonline.gov.in" },
      { title: "TKDL access portal", subtitle: "For patent examiners & authorised users" },
      { title: "AYUSH Ministry notifications", subtitle: "Latest regulatory circulars" },
      { title: "CDSCO phytopharmaceutical guidelines", subtitle: "Rule 122E filing requirements" },
    ],
  },
  about: {
    title: "About IP-SAKTI Sahayak",
    subtitle: "Evidence-first guidance for India's traditional-knowledge innovators.",
    icon: "info",
    items: [
      { title: "Our mission", subtitle: "From ancient wisdom to modern protection." },
      { title: "How answers are sourced", subtitle: "Statutes, treaties, TKDL & classical texts — always cited." },
      { title: "Human-in-the-loop", subtitle: "AI guidance backed by certified IP professionals on escalation." },
      { title: "Disclaimer", subtitle: "Educational & guidance purposes only — not formal legal advice." },
    ],
  },
}
