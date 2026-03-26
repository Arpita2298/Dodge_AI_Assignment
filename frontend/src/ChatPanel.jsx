import { useState, useRef, useEffect } from "react"

export default function ChatPanel({ selectedNode }) {
  const [messages, setMessages] = useState([{
    role: "assistant",
    text: "Hi! I can help you analyze the Order-to-Cash process. Ask me anything about sales orders, deliveries, billing, or payments!"
  }])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    if (selectedNode) {
      setInput(`Tell me about ${selectedNode.type}: ${selectedNode.label}`)
    }
  }, [selectedNode])

  async function sendMessage() {
    if (!input.trim() || loading) return
    const question = input.trim()
    setInput("")
    setMessages(prev => [...prev, { role: "user", text: question }])
    setLoading(true)

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question })
      })
      const data = await res.json()
      setMessages(prev => [...prev, {
        role: "assistant",
        text: data.answer,
        sql: data.sql
      }])
    } catch {
      setMessages(prev => [...prev, {
        role: "assistant",
        text: "Error connecting to backend. Make sure backend is running."
      }])
    }
    setLoading(false)
  }

  const suggestions = [
    "How many sales orders?",
    "Which products have most billing?",
    "Show incomplete order flows",
    "Total payment amount"
  ]

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>

      {/* Header */}
      <div style={{
        padding: "14px 16px", borderBottom: "1px solid #2d3748"
      }}>
        <div style={{ fontSize: "13px", fontWeight: "600", color: "#e2e8f0" }}>
          Chat with Graph
        </div>
        <div style={{ fontSize: "11px", color: "#718096", marginTop: "2px" }}>
          Order-to-Cash Assistant
        </div>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1, overflowY: "auto", padding: "16px",
        display: "flex", flexDirection: "column", gap: "10px"
      }}>
        {messages.map((msg, i) => (
          <div key={i} style={{
            display: "flex", flexDirection: "column",
            alignItems: msg.role === "user" ? "flex-end" : "flex-start"
          }}>
            <div style={{
              maxWidth: "92%",
              background: msg.role === "user" ? "#6366f1" : "#2d3748",
              color: "#e2e8f0",
              borderRadius: msg.role === "user"
                ? "16px 16px 4px 16px"
                : "16px 16px 16px 4px",
              padding: "10px 14px",
              fontSize: "13px", lineHeight: "1.6"
            }}>
              {msg.text}
            </div>
            {msg.sql && (
              <div style={{
                marginTop: "4px", maxWidth: "92%",
                background: "#0f1117", border: "1px solid #2d3748",
                borderRadius: "6px", padding: "6px 10px",
                fontSize: "11px", color: "#68d391",
                fontFamily: "monospace", wordBreak: "break-all"
              }}>
                {msg.sql}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <div style={{
              background: "#2d3748", borderRadius: "16px 16px 16px 4px",
              padding: "10px 14px", fontSize: "13px", color: "#718096"
            }}>
              Analyzing...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div style={{
          padding: "0 16px 12px",
          display: "flex", flexWrap: "wrap", gap: "6px"
        }}>
          {suggestions.map((s, i) => (
            <button key={i} onClick={() => setInput(s)} style={{
              background: "#2d3748", border: "1px solid #4a5568",
              borderRadius: "16px", padding: "5px 12px",
              color: "#a0aec0", fontSize: "11px", cursor: "pointer"
            }}>
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{
        padding: "12px 16px", borderTop: "1px solid #2d3748",
        display: "flex", gap: "8px"
      }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && sendMessage()}
          placeholder="Ask about orders, billing, payments..."
          style={{
            flex: 1, background: "#0f1117",
            border: "1px solid #2d3748", borderRadius: "8px",
            padding: "10px 14px", color: "#e2e8f0",
            fontSize: "13px", outline: "none"
          }}
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          style={{
            background: loading ? "#4a5568" : "#6366f1",
            border: "none", borderRadius: "8px",
            padding: "10px 16px", color: "white",
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: "13px", fontWeight: "600"
          }}
        >
          Send
        </button>
      </div>
    </div>
  )
}