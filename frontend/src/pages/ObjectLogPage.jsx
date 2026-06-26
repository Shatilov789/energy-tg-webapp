import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import {
  IconChevronLeft,
  IconPlus,
  IconPencil,
  IconAlertTriangle,
  IconUserPlus,
  IconMessagePlus,
  IconLock,
  IconRefresh,
  IconTrash,
  IconLogin,
} from '@tabler/icons-react';

const ACTION_META = {
  create: {
    object:           { label: 'Объект создан' },
    answer:           { label: 'Ответ добавлен' },
    step_status_note: { label: 'Статус добавлен' },
    user:             { label: 'Пользователь создан' },
    _default:         { label: 'Создано' },
  },
  update: {
    answer:   { label: 'Ответ обновлён' },
    object:   { label: 'Объект обновлён' },
    _default: { label: 'Обновлено' },
  },
  criticality_change: { _default: { label: 'Критичность изменена' } },
  share:              { _default: { label: 'Ответственный изменён' } },
  comment:            { _default: { label: 'Комментарий добавлен' } },
  unlock:             { _default: { label: 'Шаг разблокирован' } },
  status_change:      { _default: { label: 'Статус изменён' } },
  delete:             { _default: { label: 'Удалено' } },
  login:              { _default: { label: 'Вход в систему' } },
};

const ACTION_CLS = {
  create:             'action-create',
  update:             'action-update',
  criticality_change: 'action-criticality_change',
  share:              'action-share',
  comment:            'action-comment',
  unlock:             'action-unlock',
  status_change:      'action-status_change',
  delete:             'action-delete',
  login:              'action-login',
};

function getMeta(action, entityType) {
  const map = ACTION_META[action] || {};
  return map[entityType] || map._default || { label: action };
}

function ActionIcon({ cls }) {
  const p = { size: 16, strokeWidth: 2 };
  switch (cls) {
    case 'action-create':             return <IconPlus {...p} />;
    case 'action-update':             return <IconPencil {...p} />;
    case 'action-criticality_change': return <IconAlertTriangle {...p} />;
    case 'action-share':              return <IconUserPlus {...p} />;
    case 'action-comment':            return <IconMessagePlus {...p} />;
    case 'action-unlock':             return <IconLock {...p} />;
    case 'action-status_change':      return <IconRefresh {...p} />;
    case 'action-delete':             return <IconTrash {...p} />;
    default:                          return <IconLogin {...p} />;
  }
}

const CRIT_LABELS = { normal: 'Норма', high: 'Высокий', critical: 'Критический' };

function parseDetails(entry) {
  if (!entry.details) return null;
  try {
    const d = JSON.parse(entry.details);
    if (entry.action === 'criticality_change') {
      return `${CRIT_LABELS[d.from] || d.from} → ${CRIT_LABELS[d.to] || d.to}`;
    }
    if (d.added_worker)   return `Добавлен ответственный #${d.added_worker}`;
    if (d.removed_worker) return `Убран ответственный #${d.removed_worker}`;
    if (d.step_id)        return `Шаг #${d.step_id}`;
    if (d.is_active !== undefined) return d.is_active ? 'Активирован' : 'Деактивирован';
    return null;
  } catch { return null; }
}

function formatTime(iso) {
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function formatDateGroup(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: '2-digit', month: 'long', year: 'numeric',
  });
}

export default function ObjectLogPage() {
  const { objectId } = useParams();
  const navigate = useNavigate();
  const [entries, setEntries] = useState([]);
  const [objectName, setObjectName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const showLoadingText = useDelayedLoadingText(loading);

  useEffect(() => { loadData(); }, [objectId]);

  async function loadData() {
    try {
      const [auditData, objData] = await Promise.all([
        api.getObjectAudit(objectId),
        api.getObject(objectId).catch(() => null),
      ]);
      setEntries(auditData);
      setObjectName(objData?.name || `Объект #${objectId}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="loading">{showLoadingText ? 'Загрузка...' : ''}</div>;
  if (error)   return <div className="error">{error}</div>;

  // Группировка по дате
  const groups = [];
  let lastKey = null;
  for (const entry of entries) {
    const key = formatDateGroup(entry.created_at);
    if (key !== lastKey) { groups.push({ key, items: [] }); lastKey = key; }
    groups[groups.length - 1].items.push(entry);
  }

  return (
    <div className="page">
      <div className="tbar">
        <button className="ib" onClick={() => navigate(-1)}>
          <IconChevronLeft size={20} />
        </button>
        <div style={{ flex: 1, marginLeft: 8 }}>
          <h1>Журнал</h1>
          <div className="tbar-s">{objectName}</div>
        </div>
      </div>

      <div className="sc">
        {entries.length === 0 && (
          <div className="empty-state">Записей пока нет</div>
        )}
        {groups.map(({ key, items }) => (
          <div key={key}>
            <div className="log-date-sep">{key}</div>
            {items.map(entry => {
              const cls = ACTION_CLS[entry.action] || 'action-update';
              const { label } = getMeta(entry.action, entry.entity_type);
              const details = parseDetails(entry);
              const userName = entry.user
                ? `${entry.user.first_name}${entry.user.last_name ? ' ' + entry.user.last_name : ''}`
                : 'Система';

              return (
                <div className="log-entry" key={entry.id}>
                  <div className={`log-icon ${cls}`}>
                    <ActionIcon cls={cls} />
                  </div>
                  <div className="log-body">
                    <div className="log-action">{label}</div>
                    <div className="log-who">{userName}</div>
                    {details && <div className="log-details">{details}</div>}
                    <div className="log-time">{formatTime(entry.created_at)}</div>
                  </div>
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
