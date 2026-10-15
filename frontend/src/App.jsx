import { useEffect, useState } from "react";
import { createMemory, createWorkspace, listAgents, listMemories } from "./lib/api";

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
  const [organizationName, setOrganizationName] = useState("");
  const [creatingWorkspace, setCreatingWorkspace] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [copyStatus, setCopyStatus] = useState("");
  const [memoryForm, setMemoryForm] = useState({
    agentId: "test-agent",
    task: "",
    decision: "",
    reason: "",
    outcome: "success",
  });
  const [savingMemory, setSavingMemory] = useState(false);
  const [memoryMessage, setMemoryMessage] = useState("");

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

    if (!apiKey.trim()) {
      setMemories([]);
      setAgents([]);
      setError("Add your API key in Settings to load memory data.");
      setPage("settings");
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
  }, [apiKey]);

  const visibleMemories = memories.slice(0, 8);

  async function handleCreateWorkspace(event) {
    event.preventDefault();
    setCreatingWorkspace(true);
    setError("");
    try {
      const result = await createWorkspace(organizationName);
      setApiKey(result.api_key);
      setOrganizationName("");
      setPage("dashboard");
    } catch (err) {
      setError(err.message || "Failed to create workspace.");
    } finally {
      setCreatingWorkspace(false);
    }
  }

  async function handleCopyApiKey() {
    try {
      await navigator.clipboard.writeText(apiKey);
      setCopyStatus("Copied");
      window.setTimeout(() => setCopyStatus(""), 2000);
    } catch {
      setCopyStatus("Select and copy the key manually");
    }

    async function handleCreateMemory(event) {
      event.preventDefault();
      setSavingMemory(true);
      setMemoryMessage("");
      try {
        await createMemory({
          agent_id: memoryForm.agentId,
          input: { task: memoryForm.task },
          output: { decision: memoryForm.decision, reason: memoryForm.reason },
          outcome: memoryForm.outcome,
        });
        setMemoryForm((current) => ({ ...current, task: "", decision: "", reason: "" }));
        setMemoryMessage("Memory saved.");
        const [memoryData, agentData] = await Promise.all([
          listMemories({ limit: 20 }),
          listAgents(),
        ]);
        setMemories(memoryData || []);
        setAgents(agentData || []);
      } catch (err) {
        setMemoryMessage(err.message || "Failed to save memory.");
      } finally {
        setSavingMemory(false);
      }
    }
  }

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
            {!apiKey && (
              <form onSubmit={handleCreateWorkspace} style={{ marginBottom: 24, paddingBottom: 20, borderBottom: "1px solid #eee" }}>
                <h2 style={{ fontSize: 16, fontWeight: 500, margin: "0 0 8px" }}>Create a workspace</h2>
                <p style={{ fontSize: 12, color: "#666", margin: "0 0 12px" }}>
                  Create a workspace to get an API key for this dashboard.
                </p>
                <input
                  required
                  value={organizationName}
                  onChange={(e) => setOrganizationName(e.target.value)}
                  placeholder="Your organization name"
                  style={{ width: "100%", padding: "10px 12px", borderRadius: 8, border: "1px solid #ddd", marginBottom: 8 }}
                />
                <button type="submit" disabled={creatingWorkspace} style={{ padding: "9px 12px", border: 0, borderRadius: 8, background: "#0A0A0B", color: "#fff", cursor: "pointer" }}>
                  {creatingWorkspace ? "Creating..." : "Create workspace"}
                </button>
              </form>
            )}
            <label style={{ display: "block", fontSize: 12, color: "#666", marginBottom: 8 }}>API key</label>
            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
              <input
                type={showApiKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="mem_api_key"
                style={{ flex: 1, minWidth: 0, padding: "10px 12px", borderRadius: 8, border: "1px solid #ddd" }}
              />
              <button
                type="button"
                onClick={() => setShowApiKey((visible) => !visible)}
                disabled={!apiKey}
                style={{ padding: "0 12px", border: "1px solid #ddd", borderRadius: 8, background: "#fff", cursor: apiKey ? "pointer" : "default" }}
              >
                {showApiKey ? "Hide" : "Show"}
              </button>
              <button
                type="button"
                onClick={handleCopyApiKey}
                disabled={!apiKey}
                style={{ padding: "0 12px", border: "1px solid #ddd", borderRadius: 8, background: "#fff", cursor: apiKey ? "pointer" : "default" }}
              >
                Copy
              </button>
            </div>
            {copyStatus && <p style={{ margin: "-4px 0 12px", fontSize: 12, color: "#085041" }}>{copyStatus}</p>}
            <p style={{ margin: 0, fontSize: 12, color: "#666" }}>
              Stored in localStorage as <strong>mem_api_key</strong>. Keep it private.
            </p>
          </div>
        ) : (
          <>
          {page === "dashboard" && (
            <form onSubmit={handleCreateMemory} style={{ background: "#fff", border: "0.5px solid #E8E8E4", borderRadius: 12, padding: 16, marginBottom: 16, maxWidth: 640 }}>
              <h2 style={{ fontSize: 16, fontWeight: 500, margin: "0 0 12px" }}>Add a memory</h2>
              <div style={{ display: "grid", gap: 8 }}>
                <input
                  required
                  value={memoryForm.agentId}
                  onChange={(e) => setMemoryForm({ ...memoryForm, agentId: e.target.value })}
                  placeholder="Agent name"
                  style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #ddd" }}
                />
                <input
                  required
                  value={memoryForm.task}
                  onChange={(e) => setMemoryForm({ ...memoryForm, task: e.target.value })}
                  placeholder="What decision was made?"
                  style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #ddd" }}
                />
                <input
                  required
                  value={memoryForm.decision}
                  onChange={(e) => setMemoryForm({ ...memoryForm, decision: e.target.value })}
                  placeholder="Decision"
                  style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #ddd" }}
                />
                <textarea
                  value={memoryForm.reason}
                  onChange={(e) => setMemoryForm({ ...memoryForm, reason: e.target.value })}
                  placeholder="Reason (optional)"
                  rows={2}
                  style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #ddd", resize: "vertical" }}
                />
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <select
                    value={memoryForm.outcome}
                    onChange={(e) => setMemoryForm({ ...memoryForm, outcome: e.target.value })}
                    style={{ padding: "9px 12px", borderRadius: 8, border: "1px solid #ddd" }}
                  >
                    <option value="success">Success</option>
                    <option value="failure">Failure</option>
                    <option value="pending">Pending</option>
                    <option value="escalated">Escalated</option>
                  </select>
                  <button type="submit" disabled={savingMemory} style={{ padding: "9px 12px", border: 0, borderRadius: 8, background: "#0A0A0B", color: "#fff", cursor: "pointer" }}>
                    {savingMemory ? "Saving..." : "Save memory"}
                  </button>
                  {memoryMessage && <span style={{ fontSize: 12, color: memoryMessage === "Memory saved." ? "#085041" : "#b42318" }}>{memoryMessage}</span>}
                </div>
              </div>
            </form>
          )}
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
          </>
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
