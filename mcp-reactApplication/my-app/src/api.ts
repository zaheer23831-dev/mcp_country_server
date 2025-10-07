export type ReportResponse = {
  markdown: string;
};

export type AgentError = {
  error: string;
};

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; status: number; error: string };

export type RequestMode = 'GET' | 'POST';

export interface GetReportOptions {
  mode?: RequestMode;          // default 'GET'
  signal?: AbortSignal;        // optional AbortController support
  baseUrlOverride?: string;    // override base url if needed
}

export function getAgentBaseUrl(): string {
  // If proxy is enabled, call /report directly
  if (import.meta.env.VITE_USE_PROXY === '1') return '';
  return import.meta.env.VITE_AGENT_BASE_URL || 'http://localhost:5050';
}

/**
 * Fetch report from the DeepSeek agent service.
 * Returns ApiResult<ReportResponse> with { ok, data|error } instead of throwing.
 */
export async function getReport(
  country: string,
  opts: GetReportOptions = {}
): Promise<ApiResult<ReportResponse>> {
  const { mode = 'GET', signal, baseUrlOverride } = opts;
  const baseUrl = baseUrlOverride ?? getAgentBaseUrl();

  try {
    let res: Response;

    if (mode === 'POST') {
      res = await fetch(`${baseUrl}/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ country }),
        signal,
      });
    } else {
      const url = `${baseUrl}/report?country=${encodeURIComponent(country)}`;
      res = await fetch(url, { signal });
    }

    const text = await res.text();

    if (!res.ok) {
      // Try to parse error JSON; fall back to text
      try {
        const err = JSON.parse(text) as AgentError;
        return { ok: false, status: res.status, error: err.error || text };
      } catch {
        return { ok: false, status: res.status, error: text };
      }
    }

    // Parse success payload
    const data = JSON.parse(text) as ReportResponse;
    return { ok: true, data };
  } catch (e: unknown) {
    return { ok: false, status: 0, error: e instanceof Error ? e.message : String(e) };
  }
}
