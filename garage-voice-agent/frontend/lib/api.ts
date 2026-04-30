import type { Scenario, SessionCreateResponse, Voice } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `API error ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function createSession(input: {
  garage_id: string;
  scenario: Scenario;
  voice: Voice;
}): Promise<SessionCreateResponse> {
  return request<SessionCreateResponse>("/sessions", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
