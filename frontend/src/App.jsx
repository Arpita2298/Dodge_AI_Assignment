import { useState, useEffect } from "react"
import GraphView from "./GraphView"
import ChatPanel from "./ChatPanel"

export default function App() {
  const [selectedNode, setSelectedNode] = useState(null)
  const [backendStatus, setBackendStatus] = useState("checking...")

  useEffect(() => {
    fetch("http://localhost:8000/")
      .then(r => r.json())
      .then(() => setBackendStatus("🟢 Connected"))
      .catch(() => setBackendStatus("🔴 Backend Offline"))
  }, [])

  return (
    <div style={{ display: "flex", height: "100vh", background: "#0f1117" }}>

      {/* Header */}
      <div style={{
        position: "fixed", top: 0, left: 0, right: 0, height: "48px",
        background: "#1a1d2e", borderBottom: "1px solid #2d3748",
        display: "flex", alignItems: "center", padding: "0 20px",
        zIndex: 100, gap: "12px"
      }}>
        <div style={{
          width: "28px", height: "28px", background: "#6366f1",
          borderRadius: "8px", display: "flex", alignItems: "center",
          justifyContent: "center", fontSize: "16px"
        }}>⬡</div>
        <span style={{ fontWeight: "700", fontSize: "15px", color: "#e2e8f0" }}>
          Order-to-Cash
        </span>
        <span style={{
          fontSize: "12px", color: "#718096", background: "#2d3748",
          padding: "2px 10px", borderRadius: "12px"
        }}>Graph Agent</span>

        {/* Backend Status - Header mein right side */}
        <div style={{ marginLeft: "auto", fontSize: "12px", color: "#a0aec0" }}>
          Backend: {backendStatus}
        </div>
      </div>

      {/* Graph Left */}
      <div style={{ flex: 1, marginTop: "48px" }}>
        <GraphView onNodeSelect={setSelectedNode} />
      </div>

      {/* Chat Right */}
      <div style={{
        width: "380px", marginTop: "48px",
        borderLeft: "1px solid #2d3748",
        background: "#1a1d2e", display: "flex", flexDirection: "column"
      }}>
        <ChatPanel selectedNode={selectedNode} />
      </div>

    </div>
  )
}