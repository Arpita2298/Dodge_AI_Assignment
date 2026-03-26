import { useEffect, useRef, useState } from "react"
import * as d3 from "d3"

const NODE_COLORS = {
  SalesOrder: "#6366f1",
  SalesOrderItem: "#8b5cf6",
  Delivery: "#06b6d4",
  DeliveryItem: "#0891b2",
  Billing: "#f59e0b",
  BillingItem: "#d97706",
  Payment: "#10b981",
  JournalEntry: "#34d399",
  BusinessPartner: "#f43f5e",
  Product: "#fb923c",
}

export default function GraphView({ onNodeSelect }) {
  const containerRef = useRef(null)
  const [tooltip, setTooltip] = useState(null)
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch("https://dodge-ai-assignment-v520.onrender.com/api/graph")
      .then(r => r.json())
      .then(data => {
        setStats(data.stats)
        setLoading(false)
        drawGraph(data.nodes, data.edges)
      })
      .catch(() => setLoading(false))
  }, [])

  function drawGraph(nodes, edges) {
    const container = containerRef.current
    if (!container) return
    const width = container.clientWidth
    const height = container.clientHeight

    d3.select(container).selectAll("*").remove()

    const svg = d3.select(container)
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .style("background", "#0f1117")

    const g = svg.append("g")

    svg.call(
      d3.zoom()
        .scaleExtent([0.05, 4])
        .on("zoom", (e) => g.attr("transform", e.transform))
    )

    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(edges).id(d => d.id).distance(60))
      .force("charge", d3.forceManyBody().strength(-80))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(15))

    const link = g.append("g")
      .selectAll("line")
      .data(edges)
      .join("line")
      .attr("stroke", "#2d3748")
      .attr("stroke-width", 1)
      .attr("stroke-opacity", 0.5)

    const node = g.append("g")
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", d => ({
        SalesOrder: 10, Billing: 9, Delivery: 9,
        BusinessPartner: 13, Product: 8
      }[d.type] || 6))
      .attr("fill", d => NODE_COLORS[d.type] || "#718096")
      .attr("stroke", "#0f1117")
      .attr("stroke-width", 1.5)
      .style("cursor", "pointer")
      .call(
        d3.drag()
          .on("start", (e, d) => {
            if (!e.active) simulation.alphaTarget(0.3).restart()
            d.fx = d.x; d.fy = d.y
          })
          .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y })
          .on("end", (e, d) => {
            if (!e.active) simulation.alphaTarget(0)
            d.fx = null; d.fy = null
          })
      )
      .on("mouseover", (e, d) => {
        setTooltip({ x: e.offsetX, y: e.offsetY, node: d })
        d3.select(e.currentTarget).attr("stroke", "#fff").attr("stroke-width", 2.5)
      })
      .on("mouseout", (e) => {
        setTooltip(null)
        d3.select(e.currentTarget).attr("stroke", "#0f1117").attr("stroke-width", 1.5)
      })
      .on("click", (e, d) => onNodeSelect(d))

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x).attr("y2", d => d.target.y)
      node
        .attr("cx", d => d.x).attr("cy", d => d.y)
    })
  }

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>

      {/* Loading */}
      {loading && (
        <div style={{
          position: "absolute", inset: 0, display: "flex",
          alignItems: "center", justifyContent: "center",
          color: "#718096", fontSize: "14px", background: "#0f1117"
        }}>
          Loading graph...
        </div>
      )}

      {/* Legend */}
      <div style={{
        position: "absolute", bottom: "16px", left: "16px",
        display: "flex", flexWrap: "wrap", gap: "6px",
        zIndex: 10, maxWidth: "600px"
      }}>
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <div key={type} style={{
            background: "#1a1d2e", border: "1px solid #2d3748",
            borderRadius: "6px", padding: "3px 10px",
            fontSize: "11px", display: "flex", alignItems: "center", gap: "5px"
          }}>
            <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: color }} />
            {type}
          </div>
        ))}
      </div>

      {/* Stats */}
      {stats && (
        <div style={{
          position: "absolute", top: "12px", right: "12px",
          background: "#1a1d2e", border: "1px solid #2d3748",
          borderRadius: "8px", padding: "8px 14px",
          fontSize: "12px", color: "#a0aec0", zIndex: 10
        }}>
          {stats.total_nodes} nodes · {stats.total_edges} edges
        </div>
      )}

      {/* Graph Canvas */}
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />

      {/* Tooltip */}
      {tooltip && (
        <div style={{
          position: "absolute",
          left: Math.min(tooltip.x + 12, window.innerWidth - 250),
          top: Math.max(tooltip.y - 10, 10),
          background: "#1a1d2e", border: "1px solid #4a5568",
          borderRadius: "8px", padding: "10px 14px",
          fontSize: "12px", zIndex: 50, maxWidth: "230px",
          pointerEvents: "none", boxShadow: "0 4px 20px rgba(0,0,0,0.5)"
        }}>
          <div style={{
            fontWeight: "700", marginBottom: "6px",
            color: NODE_COLORS[tooltip.node.type] || "#fff", fontSize: "13px"
          }}>
            {tooltip.node.type}
          </div>
          <div style={{ color: "#e2e8f0", marginBottom: "6px" }}>
            {tooltip.node.label}
          </div>
          {Object.entries(tooltip.node.properties || {})
            .filter(([, v]) => v)
            .slice(0, 5)
            .map(([k, v]) => (
              <div key={k} style={{ marginTop: "3px", color: "#718096", fontSize: "11px" }}>
                <span style={{ color: "#a0aec0" }}>{k}:</span> {String(v).slice(0, 30)}
              </div>
            ))}
          <div style={{ marginTop: "8px", fontSize: "11px", color: "#6366f1" }}>
            Click to query →
          </div>
        </div>
      )}
    </div>
  )
}