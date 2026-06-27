/** Сколько полных дней прошло с даты создания объекта. */
export function daysSince(dateStr) {
  const created = new Date(dateStr);
  const diffMs = Date.now() - created.getTime();
  return Math.max(0, Math.floor(diffMs / (1000 * 60 * 60 * 24)));
}

export function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

export function formatDateTime(dateStr) {
  return new Date(dateStr).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function pluralDays(n) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod100 >= 11 && mod100 <= 14) return 'дней';
  if (mod10 === 1) return 'день';
  if (mod10 >= 2 && mod10 <= 4) return 'дня';
  return 'дней';
}

/** "сегодня" / "3 дня" / "12 дней" — для отображения возраста объекта. */
export function daysSinceLabel(dateStr) {
  const n = daysSince(dateStr);
  if (n === 0) return 'сегодня';
  return `${n} ${pluralDays(n)}`;
}
