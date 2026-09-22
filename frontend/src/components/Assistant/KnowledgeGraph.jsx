import { useEffect, useRef, useState, useCallback, useMemo } from "react"
import styles from "./KnowledgeGraph.module.css"
import Icon from "../Icons/IconSet"
import api from "../../api/axiosInstance"

// ── Color map (matches backend node_type_meta) ────────────────────────────────
const NODE_COLORS = {
  Herb:             "#3f9152",
  Formulation:      "#0e4a52",
  AuthoritativeText:"#8b5cf6",
  Statute:          "#dd8a3e",
  Section:          "#c2732a",
  TreatyArticle:    "#0ea5e9",
  PatentBar:        "#ef4444",
}

const NODE_RADIUS = {
  Herb:             22,
  Formulation:      28,
  AuthoritativeText:22,
  Statute:          26,
  Section:          20,
  TreatyArticle:    22,
  PatentBar:        20,
}

const EDGE_COLORS = {
  CONTAINS_HERB:      "#3f9152",
  MENTIONED_IN:       "#8b5cf6",
  GOVERNED_BY:        "#dd8a3e",
  BARRED_BY:          "#ef4444",
  REQUIRES_APPROVAL:  "#c2732a",
  PROTECTED_IN:       "#0e4a52",
  PART_OF:            "#94a3b8",
  TRIGGERED_BY:       "#ef4444",
  IMPLEMENTED_BY:     "#0ea5e9",
}

// ── Force-directed layout calculation ─────────────────────────────────────────
// Pre-settles nodes in 160 Verlet iterations in <2ms for instantaneous, stable layout
function computeLayout(nodes, edges, width, height) {
  if (!nodes.length || !width || !height) return {}
  const pos = {}
  nodes.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / nodes.length
    const r = Math.min(width, height) * 0.35
    pos[n.id] = {
      x: width / 2 + r * Math.cos(angle),
      y: height / 2 + r * Math.sin(angle),
      vx: 0,
      vy: 0,
    }
  })

  let alpha = 1.0
  const ALPHA_DECAY = 0.015
  const REPULSION = 4200
  const SPRING_K  = 0.045
  const SPRING_L  = 115
  const CENTER_K  = 0.012

  for (let step = 0; step < 160; step++) {
    alpha *= (1 - ALPHA_DECAY)
    const ids = Object.keys(pos)

    // Repulsion
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        const a = pos[ids[i]], b = pos[ids[j]]
        const dx = b.x - a.x, dy = b.y - a.y
        const d2 = dx * dx + dy * dy + 1
        const f = (REPULSION / d2) * alpha
        const d = Math.sqrt(d2)
        a.vx -= (dx / d) * f
        a.vy -= (dy / d) * f
        b.vx += (dx / d) * f
        b.vy += (dy / d) * f
      }
    }

    // Spring attraction along edges
    edges.forEach(({ source, target }) => {
      if (!pos[source] || !pos[target]) return
      const a = pos[source], b = pos[target]
      const dx = b.x - a.x, dy = b.y - a.y
      const d = Math.sqrt(dx * dx + dy * dy) || 1
      const f = (d - SPRING_L) * SPRING_K * alpha
      a.vx += (dx / d) * f
      a.vy += (dy / d) * f
      b.vx -= (dx / d) * f
      b.vy -= (dy / d) * f
    })

    // Centering & velocity integration
    const r = 32
    ids.forEach((id) => {
      const n = pos[id]
      n.vx += (width / 2 - n.x) * CENTER_K * alpha
      n.vy += (height / 2 - n.y) * CENTER_K * alpha
      n.x += n.vx * 0.9
      n.y += n.vy * 0.9
      n.x = Math.max(r, Math.min(width - r, n.x))
      n.y = Math.max(r, Math.min(height - r, n.y))
    })
  }

  return pos
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function KnowledgeGraph({ onOpenAssistant }) {
  const [graphData, setGraphData]       = useState(null)
  const [loading, setLoading]           = useState(true)
  const [hoveredNode, setHoveredNode]   = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [filterTypes, setFilterTypes]   = useState(new Set())
  const [search, setSearch]             = useState("")
  const [zoom, setZoom]                 = useState(1)
  const [positions, setPositions]       = useState({})

  const containerRef = useRef(null)
  const [dims, setDims] = useState({ width: 900, height: 560 })

  // Responsive sizing
  useEffect(() => {
    const obs = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect
      setDims({ width: Math.max(400, width), height: Math.max(360, height) })
    })
    if (containerRef.current) obs.observe(containerRef.current)
    return () => obs.disconnect()
  }, [])

  // Fetch graph data
  useEffect(() => {
    api.get("/knowledge-graph")
      .then((res) => {
        setGraphData(res.data)
        setFilterTypes(new Set(res.data.stats.node_types))
      })
      .catch(() => {
        // Use embedded fallback when backend is unavailable
        const fallback = getFallbackGraph()
        setGraphData(fallback)
        setFilterTypes(new Set(fallback.stats.node_types))
      })
      .finally(() => setLoading(false))
  }, [])

  const nodes = graphData?.nodes || []
  const edges = graphData?.edges || []

  // Filter nodes (memoized)
  const visibleNodes = useMemo(() => {
    const searchLower = search.trim().toLowerCase()
    return nodes.filter(
      (n) =>
        filterTypes.has(n.type) &&
        (searchLower === "" ||
          n.label.toLowerCase().includes(searchLower) ||
          n.type.toLowerCase().includes(searchLower))
    )
  }, [nodes, filterTypes, search])

  // Filter edges (memoized)
  const visibleEdges = useMemo(() => {
    const visibleIds = new Set(visibleNodes.map((n) => n.id))
    return edges.filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target))
  }, [edges, visibleNodes])

  // Calculate layout whenever visible nodes, edges, or container dims change
  useEffect(() => {
    if (visibleNodes.length && dims.width && dims.height) {
      const layout = computeLayout(visibleNodes, visibleEdges, dims.width, dims.height)
      setPositions(layout)
    }
  }, [visibleNodes, visibleEdges, dims.width, dims.height])

  // Drag state
  const dragRef = useRef(null)

  function handleMouseDown(e, nodeId) {
    e.stopPropagation()
    dragRef.current = { nodeId, startX: e.clientX, startY: e.clientY }
    setSelectedNode((curr) => (curr === nodeId ? null : nodeId))
  }

  function handleMouseMove(e) {
    if (!dragRef.current) return
    const { nodeId } = dragRef.current
    const svgEl = containerRef.current?.querySelector("svg")
    if (!svgEl) return
    const rect = svgEl.getBoundingClientRect()
    const x = (e.clientX - rect.left) / zoom
    const y = (e.clientY - rect.top) / zoom
    setPositions((prev) => ({
      ...prev,
      [nodeId]: {
        ...prev[nodeId],
        x: Math.max(30, Math.min(dims.width - 30, x)),
        y: Math.max(30, Math.min(dims.height - 30, y)),
      },
    }))
  }

  function handleMouseUp() {
    dragRef.current = null
  }

  function toggleFilter(type) {
    setFilterTypes((prev) => {
      const next = new Set(prev)
      if (next.has(type)) { next.delete(type) } else { next.add(type) }
      return next
    })
  }

  // Connected nodes of selected
  const connectedIds = selectedNode
    ? new Set(
        visibleEdges
          .filter((e) => e.source === selectedNode || e.target === selectedNode)
          .flatMap((e) => [e.source, e.target])
      )
    : null

  if (loading) {
    return (
      <div className={styles.loadingWrap}>
        <div className={styles.loadingSpinner} />
        <p>Loading knowledge graph…</p>
      </div>
    )
  }

  const stats = graphData?.stats || {}
  const nodeTypeMeta = graphData?.node_type_meta || {}
  const relationMeta = graphData?.relation_meta || {}

  return (
    <div className={styles.page}>
      {/* ── Header ── */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.headerIcon}>
            <Icon name="globe" size={18} />
          </span>
          <div>
            <h2 className={styles.headerTitle}>IP Knowledge Graph</h2>
            <p className={styles.headerSub}>
              Ayurvedic herbs, formulations, statutes, and their IP relationships
            </p>
          </div>
        </div>
        <div className={styles.headerStats}>
          <span className={styles.stat}><strong>{stats.total_nodes}</strong> nodes</span>
          <span className={styles.statDivider} />
          <span className={styles.stat}><strong>{stats.total_edges}</strong> edges</span>
          <span className={styles.statDivider} />
          <span className={styles.stat}><strong>{stats.node_types?.length}</strong> types</span>
          {onOpenAssistant && (
            <>
              <span className={styles.statDivider} />
              <button
                type="button"
                className={styles.backToAssistantBtn}
                onClick={onOpenAssistant}
              >
                <Icon name="chat" size={14} />
                Ask Assistant
              </button>
            </>
          )}
        </div>
      </div>

      {/* ── Controls ── */}
      <div className={styles.controls}>
        <div className={styles.searchWrap}>
          <Icon name="search" size={14} className={styles.searchIcon} />
          <input
            className={styles.searchInput}
            placeholder="Search nodes…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className={styles.zoomBtns}>
          <button type="button" className={styles.zoomBtn} onClick={() => setZoom((z) => Math.min(2, z + 0.15))}>+</button>
          <span className={styles.zoomLabel}>{Math.round(zoom * 100)}%</span>
          <button type="button" className={styles.zoomBtn} onClick={() => setZoom((z) => Math.max(0.4, z - 0.15))}>−</button>
          <button type="button" className={styles.zoomBtn} onClick={() => setZoom(1)} title="Reset zoom">↺</button>
        </div>
      </div>

      {/* ── Legend / Type filter ── */}
      <div className={styles.legend}>
        {Object.entries(nodeTypeMeta).map(([type, meta]) => (
          <button
            key={type}
            type="button"
            className={`${styles.legendItem} ${filterTypes.has(type) ? styles.legendActive : styles.legendInactive}`}
            onClick={() => toggleFilter(type)}
          >
            <span className={styles.legendDot} style={{ background: meta.color }} />
            {type}
          </button>
        ))}
      </div>

      {/* ── Canvas ── */}
      <div
        className={styles.canvasWrap}
        ref={containerRef}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg
          width={dims.width}
          height={dims.height}
          className={styles.svg}
          style={{ transform: `scale(${zoom})`, transformOrigin: "top left" }}
        >
          <defs>
            {/* Arrow markers for each edge color */}
            {Object.entries(EDGE_COLORS).map(([rel, color]) => (
              <marker
                key={rel}
                id={`arrow-${rel}`}
                viewBox="0 -5 10 10"
                refX="18"
                refY="0"
                markerWidth="6"
                markerHeight="6"
                orient="auto"
              >
                <path d="M0,-5L10,0L0,5" fill={color} />
              </marker>
            ))}
          </defs>

          {/* Edges */}
          {visibleEdges.map((edge, i) => {
            const src = positions[edge.source]
            const tgt = positions[edge.target]
            if (!src || !tgt) return null
            const color = EDGE_COLORS[edge.relation] || "#94a3b8"
            const isHighlighted =
              !selectedNode ||
              edge.source === selectedNode ||
              edge.target === selectedNode
            return (
              <g key={i}>
                <line
                  x1={src.x} y1={src.y}
                  x2={tgt.x} y2={tgt.y}
                  stroke={color}
                  strokeWidth={isHighlighted ? 1.8 : 0.6}
                  strokeOpacity={isHighlighted ? 0.75 : 0.18}
                  markerEnd={`url(#arrow-${edge.relation})`}
                />
              </g>
            )
          })}

          {/* Nodes */}
          {visibleNodes.map((node) => {
            const pos = positions[node.id]
            if (!pos) return null
            const color = NODE_COLORS[node.type] || "#94a3b8"
            const r     = NODE_RADIUS[node.type] || 20
            const isSelected  = selectedNode === node.id
            const isConnected = connectedIds ? connectedIds.has(node.id) : true
            const isDimmed    = selectedNode && !isConnected && !isSelected
            const isHovered   = hoveredNode === node.id
            const labelLines  = node.label.split("\n")

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x},${pos.y})`}
                style={{ cursor: "grab", opacity: isDimmed ? 0.2 : 1, transition: "opacity 0.2s" }}
                onMouseDown={(e) => handleMouseDown(e, node.id)}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
              >
                {/* Glow ring for selected/hovered */}
                {(isSelected || isHovered) && (
                  <circle
                    r={r + 7}
                    fill="none"
                    stroke={color}
                    strokeWidth={2}
                    strokeOpacity={0.35}
                  />
                )}
                {/* Node circle */}
                <circle
                  r={r}
                  fill={color}
                  stroke="#fff"
                  strokeWidth={isSelected ? 2.5 : 1.5}
                  fillOpacity={0.92}
                />
                {/* Label */}
                {labelLines.map((line, li) => (
                  <text
                    key={li}
                    textAnchor="middle"
                    dy={`${(li - (labelLines.length - 1) / 2) * 13}px`}
                    fontSize={labelLines.length > 1 ? 9 : 10}
                    fontWeight="700"
                    fill="#fff"
                    style={{ pointerEvents: "none", userSelect: "none" }}
                  >
                    {line}
                  </text>
                ))}
              </g>
            )
          })}
        </svg>

        {/* Tooltip on hover */}
        {hoveredNode && (() => {
          const node = visibleNodes.find((n) => n.id === hoveredNode)
          const pos  = positions[hoveredNode]
          if (!node || !pos) return null
          const meta = nodeTypeMeta[node.type] || {}
          const connEdges = visibleEdges.filter(
            (e) => e.source === hoveredNode || e.target === hoveredNode
          )
          return (
            <div
              className={styles.tooltip}
              style={{
                left: Math.min(pos.x * zoom + 34, dims.width - 210),
                top:  Math.max(pos.y * zoom - 60, 10),
              }}
            >
              <div className={styles.tooltipType} style={{ color: NODE_COLORS[node.type] }}>
                {node.type}
              </div>
              <div className={styles.tooltipLabel}>{node.label.replace("\n", " ")}</div>
              {meta.description && (
                <div className={styles.tooltipDesc}>{meta.description}</div>
              )}
              {connEdges.length > 0 && (
                <div className={styles.tooltipConnections}>
                  {connEdges.length} connection{connEdges.length !== 1 ? "s" : ""}
                </div>
              )}
            </div>
          )
        })()}
      </div>

      {/* ── Selected node detail panel ── */}
      {selectedNode && (() => {
        const node = visibleNodes.find((n) => n.id === selectedNode)
        if (!node) return null
        const outgoing = visibleEdges.filter((e) => e.source === selectedNode)
        const incoming = visibleEdges.filter((e) => e.target === selectedNode)

        return (
          <div className={styles.detailPanel}>
            <div className={styles.detailHeader}>
              <span
                className={styles.detailTypeDot}
                style={{ background: NODE_COLORS[node.type] }}
              />
              <div>
                <div className={styles.detailType}>{node.type}</div>
                <div className={styles.detailLabel}>{node.label.replace("\n", " ")}</div>
              </div>
              <button
                type="button"
                className={styles.detailClose}
                onClick={() => setSelectedNode(null)}
              >
                ✕
              </button>
            </div>

            {outgoing.length > 0 && (
              <div className={styles.detailSection}>
                <div className={styles.detailSectionLabel}>
                  <Icon name="arrow-right" size={12} /> Outgoing ({outgoing.length})
                </div>
                {outgoing.map((e, i) => {
                  const tgt = nodes.find((n) => n.id === e.target)
                  const rm  = relationMeta[e.relation] || { label: e.relation, color: "#94a3b8" }
                  return (
                    <div key={i} className={styles.detailEdge}>
                      <span className={styles.detailRelBadge} style={{ background: rm.color + "22", color: rm.color }}>
                        {rm.label}
                      </span>
                      <span className={styles.detailEdgeTarget}>{tgt?.label.replace("\n", " ")}</span>
                    </div>
                  )
                })}
              </div>
            )}

            {incoming.length > 0 && (
              <div className={styles.detailSection}>
                <div className={styles.detailSectionLabel}>
                  <Icon name="arrow-right" size={12} style={{ transform: "rotate(180deg)" }} /> Incoming ({incoming.length})
                </div>
                {incoming.map((e, i) => {
                  const src = nodes.find((n) => n.id === e.source)
                  const rm  = relationMeta[e.relation] || { label: e.relation, color: "#94a3b8" }
                  return (
                    <div key={i} className={styles.detailEdge}>
                      <span className={styles.detailRelBadge} style={{ background: rm.color + "22", color: rm.color }}>
                        {rm.label}
                      </span>
                      <span className={styles.detailEdgeTarget}>{src?.label.replace("\n", " ")}</span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )
      })()}

      <div className={styles.hint}>
        Click a node to see its connections · Drag to reposition · Scroll to zoom
      </div>
    </div>
  )
}

// ── Embedded fallback (same data as backend, for offline rendering) ─────────
function getFallbackGraph() {
  return {
    nodes: [
      { id:"h1", label:"Curcuma longa\n(Turmeric)", type:"Herb", group:"herb" },
      { id:"h2", label:"Withania somnifera\n(Ashwagandha)", type:"Herb", group:"herb" },
      { id:"h3", label:"Emblica officinalis\n(Amla)", type:"Herb", group:"herb" },
      { id:"h4", label:"Terminalia chebula\n(Haritaki)", type:"Herb", group:"herb" },
      { id:"h5", label:"Tinospora cordifolia\n(Giloy)", type:"Herb", group:"herb" },
      { id:"f1", label:"Chyawanprash", type:"Formulation", group:"formulation" },
      { id:"f2", label:"Triphala", type:"Formulation", group:"formulation" },
      { id:"f3", label:"Ashwagandha\nExtract", type:"Formulation", group:"formulation" },
      { id:"t1", label:"Charaka Samhita", type:"AuthoritativeText", group:"text" },
      { id:"s1", label:"Patents Act 1970", type:"Statute", group:"statute" },
      { id:"s2", label:"Biological Diversity\nAct 2002", type:"Statute", group:"statute" },
      { id:"sec1", label:"Section 3(p)\nTK Exclusion", type:"Section", group:"section" },
      { id:"tr1", label:"Nagoya Protocol\nArticle 5", type:"TreatyArticle", group:"treaty" },
      { id:"pb1", label:"Prior Art Bar", type:"PatentBar", group:"patentbar" },
    ],
    edges: [
      { source:"f1", target:"h3", relation:"CONTAINS_HERB" },
      { source:"f2", target:"h3", relation:"CONTAINS_HERB" },
      { source:"f2", target:"h4", relation:"CONTAINS_HERB" },
      { source:"f3", target:"h2", relation:"CONTAINS_HERB" },
      { source:"f1", target:"h5", relation:"CONTAINS_HERB" },
      { source:"f1", target:"t1", relation:"MENTIONED_IN" },
      { source:"f2", target:"t1", relation:"MENTIONED_IN" },
      { source:"f1", target:"s1", relation:"GOVERNED_BY" },
      { source:"f1", target:"sec1", relation:"BARRED_BY" },
      { source:"pb1", target:"sec1", relation:"TRIGGERED_BY" },
      { source:"sec1", target:"s1", relation:"PART_OF" },
      { source:"tr1", target:"s2", relation:"IMPLEMENTED_BY" },
    ],
    node_type_meta: {
      Herb:             { color:"#3f9152", description:"Medicinal plant ingredient" },
      Formulation:      { color:"#0e4a52", description:"Ayurvedic product or extract" },
      AuthoritativeText:{ color:"#8b5cf6", description:"Classical Ayurvedic text" },
      Statute:          { color:"#dd8a3e", description:"Indian or international law" },
      Section:          { color:"#c2732a", description:"Specific statutory provision" },
      TreatyArticle:    { color:"#0ea5e9", description:"International treaty clause" },
      PatentBar:        { color:"#ef4444", description:"Patent exclusion ground" },
    },
    relation_meta: {
      CONTAINS_HERB:    { label:"Contains Herb",    color:"#3f9152" },
      MENTIONED_IN:     { label:"Mentioned In",     color:"#8b5cf6" },
      GOVERNED_BY:      { label:"Governed By",      color:"#dd8a3e" },
      BARRED_BY:        { label:"Barred By",        color:"#ef4444" },
      PART_OF:          { label:"Part Of",          color:"#94a3b8" },
      TRIGGERED_BY:     { label:"Triggered By",     color:"#ef4444" },
      IMPLEMENTED_BY:   { label:"Implemented By",   color:"#0ea5e9" },
    },
    stats: { total_nodes:14, total_edges:12, node_types:["Herb","Formulation","AuthoritativeText","Statute","Section","TreatyArticle","PatentBar"] },
  }
}
