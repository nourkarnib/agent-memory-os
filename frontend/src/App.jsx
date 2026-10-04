import { useState } from "react";

const MOCK_MEMORIES = [
  { id: "m1", agent_id: "pricing-agent", memory_type: "episodic", outcome: "success", input: { task: "Should we approve a 25% discount for Acme Corp?", customer_arr: 120000 }, output: { decision: "approve", reasoning: "Customer ARR > $100k threshold. Strategic account.", discount: 0.25 }, latency_ms: 1240, tokens_used: 890, created_at: "2026-05-23T10:32:00Z", relevance_score: null },
  { id: "m2", agent_id: "support-agent", memory_type: "semantic", outcome: "success", input: { task: "Customer reports API timeout after 30s", error_code: "TIMEOUT_503" }, output: { decision: "escalate", reasoning: "Known issue with EU region. Escalate to infra team.", ticket: "INF-2291" }, latency_ms: 890, tokens_used: 540, created_at: "2026-05-23T09:18:00Z", relevance_score: null },
  { id: "m3", agent_id: "onboarding-agent", memory_type: "procedural", outcome: "success", input: { task: "New enterprise customer Stripe setup", plan: "enterprise" }, output: { steps_completed: ["SSO config", "API key provisioning", "Webhook setup"], time_minutes: 12 }, latency_ms: 4200, tokens_used: 1200, created_at: "2026-05-22T15:44:00Z", relevance_score: null },
  { id: "m4", agent_id: "pricing-agent", memory_type: "episodic", outcome: "failure", input: { task: "Approve 40% discount for startup", customer_arr: 8000 }, output: { decision: "reject", reasoning: "Discount exceeds policy limit for ARR < $10k" }, latency_ms: 760, tokens_used: 420, created_at: "2026-05-22T11:05:00Z", relevance_score: null },
];

const AGENTS = [
  { id: "pricing-agent", name: "Pricing Agent", framework: "LangChain", memory_count: 142 },
  { id: "support-agent", name: "Support Agent", framework: "CrewAI", memory_count: 891 },
  { id: "onboarding-agent", name: "Onboarding Agent", framework: "Custom", memory_count: 67 },
];

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

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#F8F8F6", fontFamily: "system-ui, sans-serif" }}>
      <aside style={{ width: 200, background: "#0A0A0B", padding: "20px 12px", flexShrink: 0 }}>
        <div style={{ color: "#fff", fontWeight: 500, marginBottom: 24, fontFamily: "monospace" }}>MemoryOS</div>
        {["dashboard", "memories", "search", "agents", "settings"].map(p => (
          <button key={p} onClick={() => setPage(p)} style={{
            display: "block", width: "100%", textAlign: "left", padding: "8px 10px", marginBottom: 2,
            background: page === p ? "#1A1A1C" : "transparent", color: page === p ? "#fff" : "#888",
            border: "none", borderRadius: 8, cursor: "pointer", fontSize: 13, textTransform: "capitalize"
          }}>{p}</button>
        ))}
      </aside>
      <main style={{ flex: 1, padding: "2rem" }}>
        <h1 style={{ fontSize: 22, fontWeight: 500, marginBottom: 4 }}>{page}</h1>
        <p style={{ color: "#888", marginBottom: 20, fontSize: 14 }}>
          {import.meta.env.VITE_API_URL ? `Connected to ${import.meta.env.VITE_API_URL}` : "Dev mode — mock data"}
        </p>
        <div style={{ background: "#fff", border: "0.5px solid #E8E8E4", borderRadius: 12 }}>
          {MOCK_MEMORIES.map(m => (
            <div key={m.id} style={{ padding: "12px 16px", borderBottom: "0.5px solid #F0F0EC", display: "flex", justifyContent: "space-between" }}>
              <div>
                <p style={{ fontSize: 13, fontWeight: 500, margin: 0 }}>{m.input.task}</p>
                <p style={{ fontSize: 12, color: "#888", margin: 0 }}>{m.agent_id}</p>
              </div>
              <Badge label={m.outcome} bg="#E1F5EE" color="#085041" dot="#1D9E75" />
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
