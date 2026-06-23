/**
 * API client for Energy CRM backend.
 * In production: sends Telegram initData for auth.
 * In development: sends X-Dev-Telegram-Id header.
 */

const API_BASE = '/api';

function getAuthHeaders() {
  const tg = window.Telegram?.WebApp;
  if (tg?.initData) {
    return { 'X-Telegram-Init-Data': tg.initData };
  }
  // Dev fallback
  return { 'X-Dev-Telegram-Id': '123456789' };
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export const api = {
  // Auth
  getMe: () => request('/auth/me'),

  // Scenarios
  getScenarios: () => request('/scenarios/'),
  getScenario: (id) => request(`/scenarios/${id}`),

  // Objects
  getMyObjects: () => request('/objects/'),
  getObject: (id) => request(`/objects/${id}`),
  createObject: (data) => request('/objects/', { method: 'POST', body: JSON.stringify(data) }),
  shareObject: (objectId, userId) => request(`/objects/${objectId}/share/${userId}`, { method: 'POST' }),

  // Steps / Answers
  submitAnswer: (objectId, stepId, data) =>
    request(`/objects/${objectId}/steps/${stepId}/answer`, { method: 'POST', body: JSON.stringify(data) }),
  updateAnswer: (objectId, stepId, data) =>
    request(`/objects/${objectId}/steps/${stepId}/answer`, { method: 'PUT', body: JSON.stringify(data) }),

  // Notifications
  getNotifications: () => request('/notifications/'),
  getUnreadCount: () => request('/notifications/unread-count'),
  markRead: (id) => request(`/notifications/${id}/read`, { method: 'PATCH' }),
  markAllRead: () => request('/notifications/read-all', { method: 'PATCH' }),

  // Admin
  getAdminObjects: () => request('/admin/objects'),
  getAdminUsers: () => request('/admin/users'),
  addComment: (answerId, data) =>
    request(`/admin/answers/${answerId}/comment`, { method: 'POST', body: JSON.stringify(data) }),
  unlockAnswer: (answerId) =>
    request(`/admin/answers/${answerId}/unlock`, { method: 'PATCH' }),
};
