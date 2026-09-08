const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export async function createAgent(data: any) {
  const res = await fetch(`${API_BASE}/agents/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
export async function screenAgent(agentId: number, identifiers?: any[]) {
  const res = await fetch(`${API_BASE}/screen/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ agent_id: agentId, identifiers }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function getCases() {
  const res = await fetch(`${API_BASE}/cases/`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function getCase(id: number) {
  const res = await fetch(`${API_BASE}/cases/${id}/`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function getNetwork(id: number) {
  const res = await fetch(`${API_BASE}/cases/${id}/network/`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}