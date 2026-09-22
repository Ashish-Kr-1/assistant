// Application configuration & domain constants for IP-SAKTI Sahayak.

export const brand = {
  name: "IP-SAKTI",
  tagline: "Sahayak",
  quote: "From ancient wisdom to modern protection.",
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
  { key: "assistant", label: "AI Assistant", to: "/assistant" },
  { key: "knowledge-base", label: "Knowledge Graph", section: "knowledge-base" },
  { key: "ip-guidance", label: "IP Guidance", section: "ip-guidance" },
]

export const sideNavItems = [
  { key: "assistant", label: "AI Assistant", icon: "chat" },
  { key: "knowledge-base", label: "Knowledge Graph", icon: "network" },
  { key: "ip-guidance", label: "IP Guidance", icon: "document" },
  { key: "expert-escalation", label: "Expert Escalation", icon: "user" },
]

export const suggestedQuestions = [
  "Can this formulation be patented under Section 3(p)?",
  "Is this traditional knowledge already documented in TKDL?",
  "What NBA approvals (Form I / III) apply to export?",
  "Does my product qualify as Ayurveda Aahar or a Phytopharmaceutical drug?",
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
    subtitle: "Screen Section 3(p) & 3(d)",
    query: "Can my Ayurvedic formulation be patented in India, and what are the Section 3(p) and 3(d) implications?",
  },
  {
    key: "regulatory",
    icon: "shield",
    title: "Verify Regulatory Requirements",
    subtitle: "AYUSH, FSSAI, CDSCO pathways",
    query: "What regulatory approvals (AYUSH Rule 158B, FSSAI Ayurveda Aahar, CDSCO Rule 122E) apply to my product?",
  },
  {
    key: "tkdl",
    icon: "search",
    title: "Search Traditional Knowledge",
    subtitle: "TKDL & classical texts",
    query: "Is this formulation already documented in the Traditional Knowledge Digital Library (TKDL) or Charaka Samhita?",
  },
  {
    key: "abs",
    icon: "document",
    title: "Access & Benefit-Sharing (ABS)",
    subtitle: "Biological Diversity Act & NBA",
    query: "What are my Access and Benefit-Sharing (ABS) obligations under the Biological Diversity Act 2002 and NBA Form I/III?",
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
    subtitle: "22+ Indian languages via Bhashini",
  },
  {
    key: "human",
    icon: "user",
    title: "Human-in-the-Loop",
    subtitle: "AI guidance + certified patent agent escalation",
  },
]
