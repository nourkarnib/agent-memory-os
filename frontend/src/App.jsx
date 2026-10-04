import { useEffect, useState } from "react";
import { listAgents, listMemories } from "./lib/api";

function Badge({ label, bg, color, dot }) {
  return (
    <span style={{ background: bg, color, fontSize: 11, fontWeight: 500, padding: "2px 8px", borderRadius: 6, display: "inline-flex", alignItems: "center", gap: 4 }}>
      {dot && <span style={{ width: 6, height: 6, borderRadius: "50%", background: dot, flexShrink: 0 }} />}
      {label}
    </span>
  );
}

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [memories, setMemories] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [apiKey, setApiKey] = useState(localStorage.getItem("mem_api_key") || "");

  useEffect(() => {
    localStorage.setItem("mem_api_key", apiKey);
  }, [apiKey]);

  useEffect(() => {
    const apiBase = import.meta.env.VITE_API_URL;
    if (!apiBase) {
      setError("No VITE_API_URL configured. Set it to your Render backend URL.");
      setLoading(false);
      return;
    }

    async function loadData() {
      setLoading(true);
      setError("");
      try {
        const [memoryData, agentData] = await Promise.all([
          listMemories({ limit: 20 }),
          listAgents(),
        ]);
        setMemories(memoryData || []);
        setAgents(agentData || []);
      } catch (err) {
        setError(err.message || "Failed to load memory data.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const visibleMemories = memories.slice(0, 8);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#F8F8F6", fontFamily: "system-ui, sans-serif" }}>
      <aside style={{ width: 200, background: "#0A0A0B", padding: "20px 12px", flexShrink: 0 }}>
        <div style={{ color: "#fff", fontWeight: 500, marginBottom: 24, fontFamily: "monospace" }}>MemoryOS</div>
        {["dashboard", "memories", "search", "agents", "settings"].map((p) => (
          <button
            key={p}
            onClick={() => setPage(p)}
            style={{
              display: "block",
              width: "100%",
              textAlign: "left",
              padding: "8px 10px",
              marginBottom: 2,
              background: page === p ? "#1A1A1C" : "transparent",
              color: page === p ? "#fff" : "#888",
              border: "none",
              borderRadius: 8,
              cursor: "pointer",
              fontSize: 13,
              textTransform: "capitalize",
            }}
          >
            {p}
          </button>
        ))}
      </aside>

      <main style={{ flex: 1, padding: "2rem" }}>
        <h1 style={{ fontSize: 22, fontWeight: 500, marginBottom: 4 }}>{page}</h1>
        <p style={{ color: "#888", marginBottom: 20, fontSize: 14 }}>
          {import.meta.env.VITE_API_URL ? `Connected to ${import.meta.env.VITE_API_URL}` : "No backend configured"}
        </p>

        {page === "settings" ? (
          <div style={{ background: "#fff", border: "0.5px solid #E8E8E4", borderRadius: 12, padding: 16, maxWidth: 480 }}>
            <label style={{ display: "block", fontSize: 12, color: "#666", marginBottom: 8 }}>API key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="mem_api_key"
              style={{ width: "100%", padding: "10px 12px", borderRadius: 8, border: "1px solid #ddd", marginBottom: 12 }}
            />
            <p style={{ margin: 0, fontSize: 12, color: "#666" }}>
              Stored in localStorage as <strong>mem_api_key</strong>.
            </p>
          </div>
        ) : (
          <div style={{ background: "#fff", border: "0.5px solid #E8E8E4", borderRadius: 12 }}>
            {loading && <p style={{ padding: 16, color: "#666", margin: 0 }}>Loading memories...</p>}
            {!loading && error && <p style={{ padding: 16, color: "#b42318", margin: 0 }}>{error}</p>}
            {!loading && !error && visibleMemories.length === 0 && (
              <p style={{ padding: 16, color: "#666", margin: 0 }}>No memories found.</p>
            )}

            {!loading && !error && visibleMemories.map((m) => (
              <div key={m.id} style={{ padding: "12px 16px", borderBottom: "0.5px solid #F0F0EC", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <p style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>{m.input?.task || m.input?.prompt || "Memory"}</p>
                  <p style={{ fontSize: 12, color: "#888", margin: 0 }}>{m.agent_id}</p>
                </div>
                <Badge label={m.outcome || "pending"} bg="#E1F5EE" color="#085041" dot="#1D9E75" />
              </div>
            ))}
          </div>
        )}

        {page === "agents" && agents.length > 0 && (
          <div style={{ marginTop: 20, background: "#fff", border: "0.5px solid #E8E8E4", borderRadius: 12, padding: 16 }}>
            {agents.map((agent) => (
              <div key={agent.id} style={{ display: "flex", justifyContent: "space-between", padding: "10px 0", borderBottom: "1px solid #f1f1ef" }}>
                <div>
                  <div style={{ fontWeight: 500 }}>{agent.name || agent.agent_id}</div>
                  <div style={{ fontSize: 12, color: "#666" }}>{agent.framework || "Custom"}</div>
                </div>
                <div style={{ fontSize: 12, color: "#666" }}>{agent.memory_count ?? 0} memories</div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
