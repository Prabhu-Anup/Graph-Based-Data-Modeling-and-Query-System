import GraphView from "./components/GraphView";
import ChatPanel from "./components/ChatPanel";

function App() {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", fontFamily: "system-ui, -apple-system, sans-serif", backgroundColor: "#ffffff" }}>
      
      {/* Top Navigation Bar */}
      <div style={{ height: "60px", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 24px", borderBottom: "1px solid #e5e7eb" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "16px", color: "#374151" }}>
          {/* Sidebar Menu Icon Placeholder */}
          <div style={{ display: "flex", alignItems: "center", padding: "6px", cursor: "pointer" }}>
            <div style={{ width: 14, height: 12, borderTop: "2px solid #6b7280", borderBottom: "2px solid #6b7280", position: "relative" }}>
              <div style={{ position: "absolute", top: "3px", width: "100%", borderTop: "2px solid #6b7280" }}></div>
            </div>
          </div>
          <div style={{ fontSize: "15px", marginLeft: "-4px" }}>
            <span style={{ color: "#9ca3af" }}>Mapping / </span>
            <span style={{ fontWeight: "600", color: "#111827" }}>Order to Cash</span>
          </div>
        </div>
        
        {/* Right Menu Button */}
        <div style={{ padding: "6px 14px", backgroundColor: "#1f2937", color: "#ffffff", borderRadius: "8px", fontWeight: "bold", letterSpacing: "2px", display: "flex", alignItems: "center", cursor: "pointer", fontSize: "14px" }}>
          ...
        </div>
      </div>

      {/* Main Content */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <div style={{ flex: 1, position: "relative" }}>
          <GraphView />
        </div>
        <div style={{ width: "380px", borderLeft: "1px solid #e5e7eb", backgroundColor: "#ffffff" }}>
          <ChatPanel />
        </div>
      </div>
    </div>
  );
}

export default App;