const API_BASE = '/api/proxy';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "dev-key-change-in-production";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const method = (options?.method ?? "GET").toUpperCase();
  const isWriteMethod = ["POST", "PUT", "DELETE", "PATCH"].includes(method);
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(isWriteMethod ? { "X-Api-Key": API_KEY } : {}),
    },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  getGraph: () => apiFetch<import("./types").GraphResponse>("/graph/"),
  getBottlenecks: (limit = 20) => apiFetch<import("./types").BottlenecksResponse>(`/bottlenecks/?limit=${limit}`),
  ingestEvidence: (data: import("./types").EvidenceIngest) =>
    apiFetch<import("./types").EvidenceResponse>("/evidence/", { method: "POST", body: JSON.stringify(data) }),
  runThesis: (data: import("./types").ThesisRunRequest) =>
    apiFetch<import("./types").ThesisRunResponse>("/thesis/run", { method: "POST", body: JSON.stringify(data) }),
  generateMemo: (data: import("./types").MemoRequest) =>
    apiFetch<import("./types").MemoResponse>("/memo/generate", { method: "POST", body: JSON.stringify(data) }),
  updateHouseView: (data: import("./types").HouseViewUpdate) =>
    apiFetch<{ status: string }>("/house-view/", { method: "PUT", body: JSON.stringify(data) }),
};
