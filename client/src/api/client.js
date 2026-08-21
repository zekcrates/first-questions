const BASE = '';

export async function apiFetch(path, { method = 'GET', body, signal } = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
    signal,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.detail || data.message || res.statusText || 'Request failed';
    throw new Error(msg);
  }
  return data;
}

export function hello(signal) {
  return apiFetch('/api/hello', { signal });
}
