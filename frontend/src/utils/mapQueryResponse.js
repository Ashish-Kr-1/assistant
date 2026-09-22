// Maps a live /query backend response (see backend/app/schemas/query_schema.py)
// into the message-shape that MessageBubble + Assistant.jsx expect.
// All statutory citations, confidence metrics, and evidence cards render through this mapper.

// ── Citation → Evidence card mapping ─────────────────────────────────────────
function evidenceIcon(citation) {
  if (citation.source_type === "web") return "globe"
  const text = (citation.statute || citation.source || citation.act_name || "").toLowerCase()
  if (text.includes("tkdl") || text.includes("samhita")) return "book"
  if (text.includes("treaty") || text.includes("nagoya") || text.includes("wipo")) return "globe"
  return "document"
}

export function mapCitationsToEvidence(citations) {
  if (!Array.isArray(citations) || citations.length === 0) return []
  return citations.slice(0, 6).map((c, i) => {
    if (c.source_type === "web") {
      let hostname = "External reference"
      try {
        hostname = new URL(c.official_url).hostname.replace(/^www\./, "")
      } catch (_) {}
      return {
        key: `web-${i}`,
        icon: "globe",
        title: c.title || "Web source",
        subtitle: hostname,
        url: c.official_url || "",
      }
    }
    const statute = c.statute || c.treaty || c.act_name || "Statutory Reference"
    const locator = c.section || c.rule || c.article || c.section_id || ""
    return {
      key: `stat-${i}`,
      icon: evidenceIcon(c),
      title: statute,
      subtitle: locator || "Statutory reference",
      url: c.official_url || "",
    }
  })
}

// ── Confidence string normalisation ──────────────────────────────────────────
export function mapConfidence(level) {
  switch ((level || "").toUpperCase()) {
    case "HIGH":   return "High"
    case "MEDIUM": return "Medium"
    case "LOW":    return "Low"
    default:       return "Medium"
  }
}

// ── Deep Research response → intake message shape ─────────────────────────────
// Backend signals needs_clarification = true when it's still asking questions.
// Returns a message object ready for the messages[] array in Assistant.jsx.
export function mapDeepResearchResponse(data, jurisdiction) {
  const isReady = data.ready_for_research === true

  if (data.needs_clarification || !isReady) {
    // Still in intake dialog
    return {
      id: `a-${Date.now()}`,
      role: "assistant",
      isIntake: true,
      text: data.clarification_question || data.answer || "",
      caseId: data.case_id || null,
      caseStatus: data.case_status || null,
      missingInfo: data.missing_information || [],
    }
  }

  // Case is ready for research — show as a normal success message
  return {
    id: `a-${Date.now()}`,
    role: "assistant",
    isIntake: false,
    jurisdictionBadge: jurisdiction === "india" ? "INDIA" : "INTERNATIONAL",
    confidence: "High",
    text: data.answer || "Case intake complete. Your innovation profile is ready for deep legal research.",
    evidence: [],
    caseId: data.case_id || null,
    caseStatus: data.case_status || null,
    relatedInsight: "Click 'Generate Research Report' to run the full IP & regulatory analysis pipeline.",
    followUps: [],
  }
}

// ── Case status → stepper step index ─────────────────────────────────────────
export function mapCaseStatusToStep(caseStatus) {
  switch ((caseStatus || "").toUpperCase()) {
    case "INTAKE_NOT_STARTED":
    case "INTAKE_IN_PROGRESS":
      return 0
    case "READY_FOR_RESEARCH":
    case "ASSESSED":
      return 1
    case "RESEARCH_IN_PROGRESS":
      return 2
    case "COMPLETED":
      return 3
    default:
      return -1 // no active case
  }
}
