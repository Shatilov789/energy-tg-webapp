import { useState } from 'react';
import { IconUserPlus } from '@tabler/icons-react';

export default function WorkerModal({ users, currentWorkerIds, onAdd, onClose }) {
  const [selectedUserId, setSelectedUserId] = useState('');

  async function handleAdd() {
    if (!selectedUserId) return;
    try {
      await onAdd(Number(selectedUserId));
      setSelectedUserId('');
    } catch (err) {
      alert(err.message);
    }
  }

  const candidates = users.filter(u => u.role === 'worker' && !currentWorkerIds.includes(u.id));

  return (
    <div className="comment-overlay" onClick={onClose}>
      <div className="comment-modal" onClick={e => e.stopPropagation()}>
        <h3>Відповідальні за обʼєкт</h3>
        <div style={{ fontSize: 12, color: 'var(--mu)', marginBottom: 12 }}>
          Оберіть співробітника для додавання
        </div>
        <select
          className="scen-select-native"
          value={selectedUserId}
          onChange={e => setSelectedUserId(e.target.value)}
        >
          <option value="">— обрати співробітника —</option>
          {candidates.map(u => (
            <option key={u.id} value={u.id}>
              {u.first_name} {u.last_name || ''}
            </option>
          ))}
        </select>
        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          <button className="btn-s" style={{ flex: 1 }} onClick={onClose}>
            Скасувати
          </button>
          <button className="btn-p" style={{ flex: 1 }} onClick={handleAdd} disabled={!selectedUserId}>
            <IconUserPlus size={14} /> Додати
          </button>
        </div>
      </div>
    </div>
  );
}
