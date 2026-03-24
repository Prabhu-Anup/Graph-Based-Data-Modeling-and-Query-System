import { useEffect, useState } from "react";
import ReactFlow, { Background, Controls, Handle, Position } from "reactflow";
import "reactflow/dist/style.css";
import axios from "axios";

const DotNode = ({ data }) => (
  <div style={{
    width: 6,
    height: 6,
    borderRadius: "50%",
    backgroundColor: data.isPayment ? "transparent" : data.themeColor,
    border: data.isPayment ? `2px solid ${data.themeColor}` : "none",
    boxShadow: `0 0 6px ${data.themeColor}`,
    position: "relative"
  }}>
    <Handle type="target" position={Position.Top} style={{ visibility: "hidden" }} />
    <Handle type="source" position={Position.Bottom} style={{ visibility: "hidden" }} />
  </div>
);

const nodeTypes = { dot: DotNode };

const getColor = (type) => {
  switch (type) {
    case "Customer": return "#ef4444"; // Red
    case "Order": return "#3b82f6"; // Blue
    case "OrderItem": return "#60a5fa"; // Light Blue
    case "Product": return "#f59e0b"; // Orange
    case "Delivery": return "#8b5cf6"; // Purple
    case "Invoice": return "#10b981"; // Emerald Green
    case "Payment": return "#eab308"; // Yellow
    case "AccountingDocument": return "#64748b"; // Slate
    default: return "#9ca3af"; // Gray
  }
};

export default function GraphView() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [connectedCount, setConnectedCount] = useState(0);

  const onNodeClick = (event, node) => {
    setSelectedNode(node);
    let count = 0;
    edges.forEach(e => {
      if (e.source === node.id || e.target === node.id) count++;
    });
    setConnectedCount(count);
  };

  useEffect(() => {
    axios.get(`${import.meta.env.VITE_API_URL}/graph`)
      .then(res => {
        const { nodes: backendNodes, edges: backendEdges } = res.data;

        const rfNodes = backendNodes.map((n) => {
          const themeColor = getColor(n.type);

          return {
            id: n.id,
            type: "dot",
            data: {
              originalType: n.type,
              metadata: n.metadata,
              themeColor: themeColor,
              isPayment: n.type === "Payment"
            },
            position: { x: Math.random() * 1200, y: Math.random() * 800 }
          }
        });

        const rfEdges = backendEdges.map((e, i) => ({
          id: "e" + i,
          source: e.source,
          target: e.target,
          type: "straight", // Razor sharp straight trajectories
          animated: false,
          style: {
            stroke: "#bae6fd", // crisp light blue lines
            strokeWidth: 1.2,
            opacity: 0.6
          },
        }));

        setNodes(rfNodes);
        setEdges(rfEdges);
      });
  }, []);

  return (
    <div style={{ height: "100%", width: "100%", background: "#ffffff", position: "relative" }}>

      {/* Dynamic Legend */}
      <div style={{
        position: "absolute",
        bottom: 24,
        left: 24,
        zIndex: 10,
        background: "#ffffff",
        padding: "16px 20px",
        borderRadius: "12px",
        border: "1px solid #e5e7eb",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05)",
        fontFamily: "system-ui, -apple-system, sans-serif"
      }}>
        <h4 style={{ margin: "0 0 12px 0", fontSize: "11px", fontWeight: "700", color: "#9ca3af", textTransform: "uppercase", letterSpacing: "1px" }}>Node Legend</h4>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px 24px" }}>
          {["Customer", "Order", "OrderItem", "Product", "Delivery", "Invoice", "Payment", "AccountingDocument"].map(type => (
            <div key={type} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{
                width: 8, height: 8, borderRadius: "50%",
                background: type === "Payment" ? "transparent" : getColor(type),
                border: type === "Payment" ? `2px solid ${getColor(type)}` : "none"
              }} />
              <span style={{ fontSize: "12px", color: "#374151", fontWeight: "500" }}>{type === "AccountingDocument" ? "Journal Entry" : type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Top-left Overlay Buttons */}
      <div style={{ position: "absolute", top: 16, left: 16, zIndex: 10, display: "flex", gap: "10px", fontFamily: "system-ui, -apple-system, sans-serif" }}>
        <button style={{
          display: "flex", alignItems: "center", gap: "8px",
          padding: "8px 14px", background: "#ffffff", border: "1px solid #e5e7eb", borderRadius: "8px", fontSize: "12px", fontWeight: "600", cursor: "pointer", boxShadow: "0 1px 2px rgba(0,0,0,0.05)", color: "#374151"
        }}>
          <span style={{ fontSize: "14px", transform: "rotate(45deg)", display: "inline-block" }}>⤢</span> Minimize
        </button>
        <button style={{
          display: "flex", alignItems: "center", gap: "8px",
          padding: "8px 14px", background: "#111827", color: "#ffffff", border: "none", borderRadius: "8px", fontSize: "12px", fontWeight: "600", cursor: "pointer", boxShadow: "0 1px 2px rgba(0,0,0,0.1)"
        }}>
          <span style={{ fontSize: "14px", display: "inline-block" }}>❖</span> Hide Granular Overlay
        </button>
      </div>

      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} onNodeClick={onNodeClick} fitView>
        <Controls showInteractive={false} showZoom={false} style={{ border: "none", boxShadow: "none" }} />
      </ReactFlow>

      {/* Selected Node Tooltip Card */}
      {selectedNode && (
        <div style={{
          position: "absolute",
          top: 70,
          left: 16,
          zIndex: 20,
          background: "#ffffff",
          padding: "16px",
          borderRadius: "12px",
          border: "1px solid #e5e7eb",
          boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)",
          width: "300px",
          fontFamily: "system-ui, -apple-system, sans-serif",
          color: "#374151"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "700", color: "#111827" }}>
              {selectedNode.data?.originalType || "Details"}
            </h3>
            <button onClick={() => setSelectedNode(null)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "18px", color: "#9ca3af", padding: 0 }}>&times;</button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "13px" }}>
            <div style={{ display: "flex", wordBreak: "break-word" }}>
              <span style={{ fontWeight: "600", marginRight: "6px", minWidth: "120px" }}>Entity:</span>
              <span>{selectedNode.data?.originalType}</span>
            </div>

            {selectedNode.data?.metadata && Object.entries(selectedNode.data.metadata).map(([key, value]) => {
              if (value === null || value === undefined) return null;

              const formattedKey = key.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join('');
              return (
                <div key={key} style={{ display: "flex", wordBreak: "break-word" }}>
                  <span style={{ fontWeight: "600", marginRight: "6px", minWidth: "120px" }}>{formattedKey}:</span>
                  <span>{String(value)}</span>
                </div>
              );
            })}

            <div style={{ fontSize: "11px", color: "#9ca3af", fontStyle: "italic", marginTop: "12px", borderTop: "1px solid #f3f4f6", paddingTop: "8px" }}>
              Additional fields hidden for readability
            </div>
            <div style={{ display: "flex", wordBreak: "break-word", marginTop: "4px" }}>
              <span style={{ fontWeight: "600", marginRight: "6px" }}>Connections:</span>
              <span>{connectedCount}</span>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}