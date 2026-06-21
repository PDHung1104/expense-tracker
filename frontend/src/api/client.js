const BASE = '/api';

/**
 * Core fetch wrapper — every API call in the app flows through this function.
 *
 * What it does:
 * - Prepends /api to all paths so callers just pass "/expenses"
 * - Sets credentials: 'include' for future session-cookie auth
 * - Auto-serializes objects to JSON and sets Content-Type
 * - Handles 204 No Content (returns null instead of parsing empty body)
 * - On non-JSON responses (server error HTML, proxy failure), catches the
 *   SyntaxError and throws a readable error instead of leaking "Unexpected
 *   token" to the user
 * - On non-ok JSON responses, extracts detail and throws
 */
async function request(path, options = {}) {
  const url = `${BASE}${path}`;
  const config = {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };

  // Auto-stringify objects — callers pass plain JS objects for body
  if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
    config.body = JSON.stringify(config.body);
  }

  const resp = await fetch(url, config);

  if (resp.status === 204) return null;

  let data;
  try {
    data = await resp.json();
  } catch {
    // Server returned non-JSON (e.g. HTML error page, proxy failure)
    const preview = await resp.text().then(t => t.slice(0, 100)).catch(() => '');
    throw new Error(`Server returned ${resp.status} (non-JSON response): ${preview}`);
  }

  if (!resp.ok) {
    const message = data.detail || resp.statusText;
    throw new Error(message);
  }

  return data;
}

// ---- Expense endpoints ----------------------------------------------------

/** Fetch expenses with optional filter/sort params. Used by dashboard and expenses page. */
export function getExpenses(params = {}) {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') q.set(k, v);
  });
  const qs = q.toString();
  return request(`/expenses${qs ? '?' + qs : ''}`);
}

export function createExpense(data) {
  return request('/expenses', { method: 'POST', body: data });
}

/** Partial update — only include the fields that changed. */
export function updateExpense(id, data) {
  return request(`/expenses/${id}`, { method: 'PUT', body: data });
}

export function deleteExpense(id) {
  return request(`/expenses/${id}`, { method: 'DELETE' });
}

// ---- Category endpoints ---------------------------------------------------

/** Fetch all categories (defaults + custom). Populates dropdowns and filter bar. */
export function getCategories() {
  return request('/categories');
}

export function createCategory(data) {
  return request('/categories', { method: 'POST', body: data });
}
