export function getInitials(firstName, lastName) {
  const initials = `${(firstName || '').charAt(0)}${(lastName || '').charAt(0)}`.toUpperCase();
  return initials || '?';
}
