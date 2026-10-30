// Vrisko — API client

import type { ComparisonResult } from './types';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export interface CompareRequest {
  query: string;
  country?: string;
  currency?: string;
  include_used?: boolean;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function fetchHealth(): Promise<Record<string, unknown>> {
  const res = await fetch(`${BASE_URL}/api/health`);
  return handleResponse(res);
}

export async function fetchDemo(): Promise<ComparisonResult> {
  const res = await fetch(`${BASE_URL}/api/demo`);
  return handleResponse(res);
}

export async function compareProducts(request: CompareRequest): Promise<ComparisonResult> {
  const res = await fetch(`${BASE_URL}/api/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  return handleResponse(res);
}
