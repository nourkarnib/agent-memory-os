// In production (Azure Static Web Apps), VITE_API_URL points to the
// Container Apps backend FQDN, injected at build time via GitHub Actions.
// Locally, Vite's dev proxy (vite.config.js) forwards /api to localhost:8000.
const API_URL = import.meta.env.VITE_API_URL || "";

function headers() {
  const apiKey = localStorage.getItem("mem_api_key") || "";
  return { "Content-Type": "application/json", "X-Api-Key": apiKey };
}

export async function listMemories(params = {}) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${API_URL}/api/v1/memories/?${qs}`, { headers: headers() });
  if (!res.ok) throw new Error(`listMemories failed: ${res.status}`);
  return res.json();
}

export async function getMemory(id) {
  const res = await fetch(`${API_URL}/api/v1/memories/${id}`, { headers: headers() });
  if (!res.ok) throw new Error(`getMemory failed: ${res.status}`);
  return res.json();
}

export async function searchMemories(body) {
  const res = await fetch(`${API_URL}/api/v1/search/`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`searchMemories failed: ${res.status}`);
  return res.json();
}

export async function listAgents() {
  const res = await fetch(`${API_URL}/api/v1/agents/`, { headers: headers() });
  if (!res.ok) throw new Error(`listAgents failed: ${res.status}`);
  return res.json();
}

export async function getAnalyticsSummary() {
  const res = await fetch(`${API_URL}/api/v1/analytics/summary`, { headers: headers() });
  if (!res.ok) throw new Error(`getAnalyticsSummary failed: ${res.status}`);
  return res.json();
}
