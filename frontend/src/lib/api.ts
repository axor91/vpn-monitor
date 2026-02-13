const BASE = "/vpn-monitor/api";

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export interface GeoInfo {
  country: string;
  code: string;
  isp: string;
  ip: string;
}

export interface ConfigEntry {
  link: string;
  name: string;
  protocol: string;
  address: string;
  status: string;
  latency: number | null;
  geo: GeoInfo | null;
  error?: string;
  checked_at: string | null;
}

export interface SourceData {
  info: { label: string; description: string; category: string };
  configs: ConfigEntry[];
  total_links: number;
  fetched_at: string | null;
  _checking?: boolean;
}

export interface SourceSummary {
  id: string;
  label: string;
  description: string;
  category: string;
  total_links: number;
  checked: number;
  alive: number;
  dead: number;
  unsupported: number;
  avg_latency: number;
  fetched_at: string | null;
}

export interface ProgressEntry {
  current: number;
  total: number;
  source: string;
}

export interface SummaryData {
  black: SourceSummary[];
  white: SourceSummary[];
  last_update: string | null;
  is_checking: boolean;
  check_progress: Record<string, ProgressEntry>;
}

export interface StatusData {
  last_update: string | null;
  is_checking: boolean;
  check_progress: Record<string, ProgressEntry>;
  sources_count: number;
}

export interface TestResult {
  status: string;
  latency?: number;
  geo?: GeoInfo;
  msg?: string;
}

export const api = {
  getSummary: () => fetchJSON<SummaryData>("/summary"),
  getStatus: () => fetchJSON<StatusData>("/status"),
  getResults: () => fetchJSON<Record<string, SourceData>>("/results"),
  getSource: (id: string) => fetchJSON<SourceData>(`/results/${id}`),
  startCheck: () => fetchJSON<{ status: string; msg: string }>("/start_check", { method: "POST" }),
  stopCheck: () => fetchJSON<{ status: string; msg: string }>("/stop_check", { method: "POST" }),
  checkSource: (id: string) => fetchJSON<{ status: string; msg: string }>(`/check_source/${id}`, { method: "POST" }),
  testLink: (link: string) =>
    fetchJSON<TestResult>("/test_link", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ link }),
    }),
};
