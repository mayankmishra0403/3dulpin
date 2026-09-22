const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function api<T = unknown>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "content-type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const winUrl = (path: string) => `${BASE}${path}`;

export interface Stats {
  total_parcels?: number;
  building_count?: number;
  open_conflicts?: number;
  total_volume_m3?: number;
  total_built_up_area_m2?: number;
  utility_km?: number;
  by_category?: Record<string, number>;
}

export interface Conflict {
  id: number;
  conflict_type: string;
  parcel_a: string;
  parcel_b: string | null;
  volume_m3: number | null;
  severity: string;
  description: string;
  status: string;
}

export interface PipelineRun {
  run_id: number | null;
  metrics?: Record<string, unknown>;
  started_at?: string;
  finished_at?: string;
  building_matches?: Array<Record<string, unknown>>;
  source_note?: string;
}