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
  // Outside Telegram, local development signs in as the seeded admin.
  if (import.meta.env.DEV) {
    return { 'X-Dev-Telegram-Id': import.meta.env.VITE_DEV_TELEGRAM_ID ?? '123456789' };
  }
  return {};
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
    const error = await res.json().catch(() => ({ detail: 'Не вдалося виконати запит' }));
    // Validation errors (422) carry a list of field problems instead of a message.
    throw new Error(typeof error.detail === 'string' ? error.detail : 'Перевірте правильність введених даних');
  }

  return res.json();
}

export const api = {
  // Auth
  getMe: () => request('/auth/me'),

  // Colleagues
  getColleagues: () => request('/users/'),

  // Notifications
  getNotifications: () => request('/notifications/'),
  getUnreadCount: () => request('/notifications/unread-count'),
  markRead: (id) => request(`/notifications/${id}/read`, { method: 'PATCH' }),
  markAllRead: () => request('/notifications/read-all', { method: 'PATCH' }),

  // Admin
  getAdminUsers: () => request('/admin/users'),
  createUser: (data) =>
    request('/admin/users', { method: 'POST', body: JSON.stringify(data) }),
  toggleUserActive: (userId) =>
    request(`/admin/users/${userId}/toggle-active`, { method: 'PATCH' }),

  // Deals
  getStages: (processType = 'СЕС') => request(`/deals/stages?process_type=${encodeURIComponent(processType)}`),
  getDeals: () => request('/deals/'),
  getDeal: (id) => request(`/deals/${id}`),
  createDeal: (data) => request('/deals/', { method: 'POST', body: JSON.stringify(data) }),
  advanceDeal: (id, data) => request(`/deals/${id}/advance`, { method: 'POST', body: JSON.stringify(data) }),
};
