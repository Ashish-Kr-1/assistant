// Maps a live /query backend response (see backend/app/schemas/query_schema.py)
// into the evidence-card shape MessageBubble expects, so real API answers and
// the demo.js fallback answers render identically.

function evidenceIcon(citation) {
  if (citation.source_type === "web") return "globe"
  if (/tkdl/i.test(citation.statute || citation.source || "")) return "book"
  return "document"
}

export function mapCitationsToEvidence(citations) {
  if (!Array.isArray(citations) || citations.length === 0) return []
  return citations.map((c, i) => {
    if (c.source_type === "web") {
      return {
        key: `web-${i}`,
        icon: "globe",
        title: c.title || "Web source",
        subtitle: c.official_url ? new URL(c.official_url).hostname.replace(/^www\./, "") : "External reference",
        url: c.official_url || "",
      }
    }
    const statute = c.statute || c.treaty || c.act_name || "Source"
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

export function mapConfidence(level) {
  switch ((level || "").toUpperCase()) {
    case "HIGH":
      return "High"
    case "MEDIUM":
      return "Medium"
    case "LOW":
      return "Low"
    default:
      return "Medium"
  }
}
