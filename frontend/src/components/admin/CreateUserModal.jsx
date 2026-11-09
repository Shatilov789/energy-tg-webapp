import { useState } from 'react';
import { IconShield, IconTool, IconUserPlus } from '@tabler/icons-react';

const TEXT_FIELDS = [
  { name: 'telegram_id', label: 'Telegram ID *', type: 'number', placeholder: '123456789' },
  { name: 'first_name', label: 'Імʼя *', type: 'text', placeholder: 'Іван' },
  { name: 'last_name', label: 'Прізвище', type: 'text', placeholder: 'Петренко' },
  { name: 'username', label: 'Username', type: 'text', placeholder: 'ivanpetrov' },
];

const ROLES = [
  { value: 'worker', label: 'Співробітник', icon: IconTool },
  { value: 'admin', label: 'Адміністратор', icon: IconShield },
];

export default function CreateUserModal({ onCreate, onClose }) {
  const [form, setForm] = useState({ telegram_id: '', first_name: '', last_name: '', username: '', role: 'worker' });
  const [creating, setCreating] = useState(false);

  const setField = (name, value) => setForm(prev => ({ ...prev, [name]: value }));
  const canSubmit = form.telegram_id && form.first_name;

  async function handleCreate() {
    if (!canSubmit) return;
    setCreating(true);
    try {
      await onCreate({ ...form, telegram_id: Number(form.telegram_id) });
    } catch (err) {
      alert(err.message);
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="comment-overlay" onClick={onClose}>
      <div className="comment-modal" onClick={e => e.stopPropagation()}>
        <h3>Новий користувач</h3>
        {TEXT_FIELDS.map((field, index) => (
          <div className="fgrp" key={field.name} style={index === 0 ? { marginTop: 8 } : undefined}>
            <label className="flbl">{field.label}</label>
            <input
              className="finp"
              type={field.type}
              placeholder={field.placeholder}
              value={form[field.name]}
              onChange={e => setField(field.name, e.target.value)}
            />
          </div>
        ))}
        <div className="fgrp">
          <label className="flbl">Роль</label>
          <div style={{ display: 'flex', gap: 8 }}>
            {ROLES.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                className={`role-btn${form.role === value ? ' on' : ''}`}
                onClick={() => setField('role', value)}
              >
                <Icon size={14} /> {label}
              </button>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
          <button className="btn-s" style={{ flex: 1 }} onClick={onClose}>Скасувати</button>
          <button className="btn-p" style={{ flex: 1 }} onClick={handleCreate} disabled={creating || !canSubmit}>
            {creating ? 'Створення...' : <><IconUserPlus size={14} /> Створити</>}
          </button>
        </div>
      </div>
    </div>
  );
}
