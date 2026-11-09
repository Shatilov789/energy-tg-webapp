/** Whole days elapsed since the given date. */
export function daysSince(dateStr) {
  const created = new Date(dateStr);
  const diffMs = Date.now() - created.getTime();
  return Math.max(0, Math.floor(diffMs / (1000 * 60 * 60 * 24)));
}

export function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('uk-UA', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

export function formatDateTime(dateStr) {
  return new Date(dateStr).toLocaleString('uk-UA', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function pluralDays(n) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod100 >= 11 && mod100 <= 14) return 'днів';
  if (mod10 === 1) return 'день';
  if (mod10 >= 2 && mod10 <= 4) return 'дні';
  return 'днів';
}

/** Human-readable age of an object, e.g. today, 3 days, 12 days. */
export function daysSinceLabel(dateStr) {
  const n = daysSince(dateStr);
  if (n === 0) return 'сьогодні';
  return `${n} ${pluralDays(n)}`;
}

export function formatShortDateTime(dateStr) {
  return new Date(dateStr).toLocaleString('uk-UA', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}
