const configuredBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_BASE = (configuredBase.includes("://") ? configuredBase : `https://${configuredBase}`).replace(/\/$/, "");

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail || `Request failed with status ${response.status}`);
  }
  return response.json();
}

function authHeaders(token) {
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

export function getStats() {
  return request("/api/stats");
}

export function getStudies(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined && value !== false) {
      search.set(key, value);
    }
  });
  return request(`/api/studies?${search.toString()}`);
}

export function getStudy(slug) {
  return request(`/api/studies/${encodeURIComponent(slug)}`);
}

export function submitStudy(payload) {
  return request("/api/submissions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getUpdates() {
  return request("/api/updates");
}

export function getChangelog() {
  return request("/api/changelog");
}

export function getGaps() {
  return request("/api/gaps");
}

export function askEvidence(query) {
  return request("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(query),
  });
}

export function reviewerLogin(token) {
  return request("/api/reviewer/auth", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
}

export function getDashboard(token) {
  return request("/api/reviewer/dashboard", { headers: authHeaders(token) });
}

export function getCandidates(token, statusFilter) {
  const params = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";
  return request(`/api/reviewer/candidates${params}`, { headers: authHeaders(token) });
}

export function recordDecision(token, id, stage, decision, reason, reviewerName) {
  return request(`/api/reviewer/candidates/${id}/decisions`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({
      stage,
      decision,
      reason,
      reviewer_name: reviewerName,
    }),
  });
}

export function triggerSearch(token) {
  return request("/api/reviewer/search/trigger", {
    method: "POST",
    headers: authHeaders(token),
  });
}

export function exportUrl(format) {
  return `${API_BASE}/api/export/studies.${format}`;
}

export function getReleases() {
  return request("/api/releases");
}

export function createRelease(token, version, notes) {
  const params = new URLSearchParams({ version });
  if (notes) params.set("notes", notes);
  return request(`/api/reviewer/releases?${params}`, {
    method: "POST",
    headers: authHeaders(token),
  });
}

export function rescoreCandidates(token) {
  return request("/api/reviewer/candidates/rescore", {
    method: "POST",
    headers: authHeaders(token),
  });
}

export function getIngestionStatus(token) {
  return request("/admin/status/ingestion", { headers: authHeaders(token) });
}

export function getAutomationCandidates(token, decision = "review") {
  const params = decision ? `?decision=${encodeURIComponent(decision)}` : "";
  return request(`/admin/ingestion/candidates${params}`, {
    headers: authHeaders(token),
  });
}

export function runLivingIngestion(token) {
  return request("/admin/ingestion/run", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ triggered_by: "reviewer-dashboard" }),
  });
}

export function decideAutomationCandidate(token, id, decision, reason, reviewer) {
  return request(`/admin/ingestion/candidates/${id}/decision`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ decision, reason, reviewer }),
  });
}

export function releaseDownloadUrl(version) {
  return `${API_BASE}/api/releases/${encodeURIComponent(version)}/download`;
}

export const API_DOCS_URL = `${API_BASE}/docs`;
export const API_REDOC_URL = `${API_BASE}/redoc`;
