import { IconLock, IconLockOpen, IconUsers } from '@tabler/icons-react';
import { getInitials } from '../../utils/person';

function UserCard({ user, isSelf, onToggleActive }) {
  return (
    <div className={`user-card${user.is_active ? '' : ' inactive'}`}>
      <div className={`ava ${user.role === 'admin' ? 'ava-a' : 'ava-b'}`}>
        {getInitials(user.first_name, user.last_name)}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 600 }}>
          {user.first_name} {user.last_name || ''}
          {isSelf && <span style={{ fontSize: 11, color: 'var(--acc)', marginLeft: 6 }}>це ви</span>}
          {user.username && <span style={{ fontSize: 11, color: 'var(--mu)', marginLeft: 6 }}>@{user.username}</span>}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 3 }}>
          <span className={`bdg ${user.role === 'admin' ? 'bdg-pend' : 'bdg-ok'}`}>
            {user.role === 'admin' ? 'Адміністратор' : 'Співробітник'}
          </span>
          <span className={`user-status${user.is_active ? ' active' : ' inactive'}`}>
            {user.is_active ? <IconLockOpen size={11} /> : <IconLock size={11} />}
            {user.is_active ? 'Активний' : 'Деактивовано'}
          </span>
        </div>
      </div>
      <button
        className={`user-toggle-btn${user.is_active ? '' : ' locked'}`}
        title={isSelf ? 'Не можна деактивувати себе' : user.is_active ? 'Деактивувати' : 'Активувати'}
        onClick={() => !isSelf && onToggleActive(user.id)}
        disabled={isSelf}
      >
        {user.is_active ? <IconLockOpen size={18} /> : <IconLock size={18} />}
      </button>
    </div>
  );
}

export default function UsersTab({ users, currentUserId, onToggleActive }) {
  return (
    <>
      {users.length === 0 && (
        <div className="empty-state"><IconUsers size={40} />Користувачів немає</div>
      )}
      {users.map(user => (
        <UserCard key={user.id} user={user} isSelf={currentUserId === user.id} onToggleActive={onToggleActive} />
      ))}
      <div style={{ height: 20 }} />
    </>
  );
}
