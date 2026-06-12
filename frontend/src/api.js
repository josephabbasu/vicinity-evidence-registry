const configuredBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_BASE = (configuredBase.includes("://") ? configuredBase : `https://${configuredBase}`).replace(
  /\/$/,
  "",
);

async function request(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail || `Request failed with status ${response.status}`);
  }
  return response.json();
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
