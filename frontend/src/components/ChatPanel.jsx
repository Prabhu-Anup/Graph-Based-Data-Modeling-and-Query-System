import { useState } from "react";
import axios from "axios";

export default function ChatPanel() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!query.trim()) return;

    const userMessage = { sender: "user", text: query };
    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setLoading(true);

    try {
      const res = await axios.post("http://127.0.0.1:8000/query", { user_query: userMessage.text });

      const botMessage = {
        sender: "bot",
        text: res.data.answer || (res.data.error ? `Error: ${res.data.error}` : "No answer received.")
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      setMessages((prev) => [...prev, { sender: "bot", text: "Error communicating with backend." }]);
    }

    setLoading(false);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", boxSizing: "border-box", fontFamily: "system-ui, -apple-system, sans-serif" }}>

      {/* Header */}
      <div style={{ padding: "16px 24px", borderBottom: "1px solid #f3f4f6" }}>
        <h3 style={{ margin: 0, fontSize: "13px", fontWeight: "700", color: "#111827" }}>Chat with Graph</h3>
        <p style={{ margin: "4px 0 0 0", fontSize: "11px", color: "#6b7280" }}>Order to Cash</p>
      </div>

      {/* Chat History */}
      <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>

        {/* Default Greeting */}
        <div style={{ display: "flex", gap: "12px", marginBottom: "28px" }}>
          <div style={{ width: 36, height: 36, minWidth: 36, background: "#111827", color: "#ffffff", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: "bold", fontSize: "16px" }}>
            D
          </div>
          <div style={{ marginTop: "2px" }}>
            <div style={{ fontSize: "13px", color: "#111827" }}>
              <span style={{ fontWeight: "700" }}>Dodge AI</span> <span style={{ color: "#9ca3af", marginLeft: "4px", fontWeight: "500" }}>Graph Agent</span>
            </div>
            <div style={{ fontSize: "13px", marginTop: "8px", lineHeight: "1.5", color: "#374151" }}>
              Hi! I can help you analyze the <strong>Order to Cash</strong> process.
            </div>
          </div>
        </div>

        {/* User & AI Messages */}
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            display: "flex",
            gap: "12px",
            marginBottom: "24px",
            flexDirection: msg.sender === "user" ? "row-reverse" : "row"
          }}>
            {msg.sender === "bot" && (
              <div style={{ width: 36, height: 36, minWidth: 36, background: "#111827", color: "#ffffff", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: "bold", fontSize: "16px" }}>
                D
              </div>
            )}
            <div style={{
              background: msg.sender === "user" ? "#f8fafc" : "transparent",
              padding: msg.sender === "user" ? "12px 16px" : "0",
              borderRadius: "12px",
              fontSize: "13px",
              lineHeight: "1.5",
              color: "#374151",
              maxWidth: "85%",
              marginTop: msg.sender === "bot" ? "2px" : "0",
            }}>
              {msg.text}
            </div>
          </div>
        ))}
      </div>

      {/* Input Area container */}
      <div style={{ padding: "0 24px 24px 24px" }}>
        <div style={{
          border: "1px solid #e5e7eb",
          borderRadius: "8px",
          padding: "16px",
          background: "#ffffff",
          boxShadow: "0 1px 3px rgba(0,0,0,0.05)"
        }}>
          {/* Status Indicator */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "12px", paddingLeft: "2px" }}>
            <div style={{ width: 6, height: 6, background: "#10b981", borderRadius: "50%" }}></div>
            <span style={{ fontSize: "11px", fontWeight: "600", color: "#4b5563" }}>
              {loading ? "Dodge AI is thinking..." : "Dodge AI is awaiting instructions"}
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "flex-end" }}>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Analyze anything"
              style={{
                flex: 1,
                border: "none",
                outline: "none",
                resize: "none",
                padding: "8px 0px",
                fontSize: "13px",
                fontFamily: "inherit",
                minHeight: "44px"
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <button
              onClick={handleSend}
              disabled={loading || !query.trim()}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                border: "none",
                background: "#8f96a3",
                color: "white",
                cursor: (loading || !query.trim()) ? "not-allowed" : "pointer",
                fontWeight: "600",
                fontSize: "12px",
                marginLeft: "12px"
              }}
            >
              Send
            </button>
          </div>
        </div>
      </div>

    </div>
  );
}