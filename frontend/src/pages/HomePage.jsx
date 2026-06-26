import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import { formatDate, daysSinceLabel } from '../utils/date';
import {
  IconPlus,
  IconBolt,
  IconBell,
  IconList,
  IconLayoutDashboard,
  IconAlertCircle,
  IconClipboardOff,
  IconClock,
  IconX,
} from '@tabler/icons-react';
import { getScenarioIcon } from '../scenarioIcons';

const CRIT_ORDER = { critical: 0, high: 1, normal: 2 };
const CRIT_LABELS = { normal: 'Норма', high: 'Высокий', critical: 'Критический' };

// Кэш последнего успешного снимка — повторный заход на главную рисует
// сразу без спиннера, пока в фоне идёт тихий рефетч.
let homeCache = null;

export default function HomePage() {
  const navigate = useNavigate();
  const [objects, setObjects] = useState(homeCache?.objects ?? []);
  const [unreadCount, setUnreadCount] = useState(homeCache?.unreadCount ?? 0);
  const [user, setUser] = useState(homeCache?.user ?? null);
  const [loading, setLoading] = useState(!homeCache);
  const [error, setError] = useState(null);
  const [critModal, setCritModal] = useState(null); // объект для смены критичности
  const showLoadingText = useDelayedLoadingText(loading);

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    try {
      const [objectsData, unread, me] = await Promise.all([
        api.getMyObjects(),
        api.getUnreadCount().catch(() => ({ count: 0 })),
        api.getMe().catch(() => null),
      ]);
      const unreadCountVal = unread.count || unread.unread_count || 0;
      setObjects(objectsData);
      setUnreadCount(unreadCountVal);
      setUser(me);
      homeCache = { objects: objectsData, unreadCount: unreadCountVal, user: me };
    } catch (err) {
      if (!homeCache) setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function openObject(obj) {
    navigate(`/objects/${obj.id}/steps/${obj.next_step || 1}`);
  }

  async function handleCriticality(obj, level) {
    setCritModal(null);
    try {
      await api.updateCriticality(obj.id, level);
      const updated = objects.map(o => o.id === obj.id ? { ...o, criticality: level } : o);
      setObjects(updated);
      homeCache = { ...homeCache, objects: updated };
    } catch (err) {
      alert(err.message);
    }
  }

  if (loading) return <div className="loading">{showLoadingText ? 'Загрузка...' : ''}</div>;
  if (error) return <div className="error">{error}</div>;

  function sortByCrit(arr) {
    return [...arr].sort((a, b) => {
      const ca = CRIT_ORDER[a.criticality] ?? 2;
      const cb = CRIT_ORDER[b.criticality] ?? 2;
      if (ca !== cb) return ca - cb;
      return new Date(b.updated_at) - new Date(a.updated_at);
    });
  }

  const sorted = sortByCrit(objects);
  const inProgress = sorted.filter(o => o.total_steps > 0 && o.answered_steps < o.total_steps && o.answered_steps > 0);
  const notStarted = sorted.filter(o => o.total_steps > 0 && o.answered_steps === 0);
  const completed = sorted.filter(o => o.total_steps > 0 && o.answered_steps >= o.total_steps);

  const isAdmin = user?.role === 'admin';

  return (
    <div className="page">
      <div className="tbar">
        <div style={{ flex: 1 }}>
          <h1>Мои объекты</h1>
          <div className="tbar-s">
            {objects.filter(o => o.total_steps > 0 && o.answered_steps < o.total_steps).length} активных
          </div>
        </div>
        <button className="fab-create" onClick={() => navigate('/objects')}>
          <IconBolt size={22} strokeWidth={2.5} />
        </button>
      </div>

      <div className="sc">
        {inProgress.length > 0 && (
          <>
            <div className="slbl">В работе</div>
            {inProgress.map(obj => renderObjectCard(obj))}
          </>
        )}

        {completed.length > 0 && (
          <>
            <div className="slbl">Завершённые</div>
            {completed.map(obj => renderObjectCard(obj, true))}
          </>
        )}

        {notStarted.length > 0 && (
          <>
            <div className="slbl">Новые</div>
            {notStarted.map(obj => renderObjectCard(obj))}
          </>
        )}

        {objects.length === 0 && (
          <div className="empty-state">
            <IconClipboardOff size={40} />
            Объектов пока нет. Создайте первый!
          </div>
        )}
      </div>

      {critModal && (
        <div className="modal-overlay" onClick={() => setCritModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
              <div className="modal-title" style={{ margin: 0 }}>Критичность</div>
              <button className="ib" onClick={() => setCritModal(null)}><IconX size={18} /></button>
            </div>
            <div className="modal-subtitle" style={{ marginBottom: 16 }}>{critModal.name}</div>
            {['normal', 'high', 'critical'].map(level => (
              <button
                key={level}
                className={`crit-option${critModal.criticality === level ? ' sel' : ''}`}
                onClick={() => handleCriticality(critModal, level)}
              >
                <span className={`crit-option-dot ${level}`} />
                {CRIT_LABELS[level]}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="tabbar">
        <button className="tab on">
          <IconList size={22} />
          <span>Объекты</span>
          <div className="tab-indicator" />
        </button>
        <button className="tab" onClick={() => navigate('/objects')}>
          <IconBolt size={22} />
          <span>Создать</span>
        </button>
        <button className="tab" onClick={() => navigate('/notifications')} style={{ position: 'relative' }}>
          <IconBell size={22} />
          <span>Оповещения</span>
          {unreadCount > 0 && <span className="tab-notif-badge">{unreadCount}</span>}
        </button>
        {isAdmin && (
          <button className="tab" onClick={() => navigate('/admin')}>
            <IconLayoutDashboard size={22} />
            <span>Админ</span>
          </button>
        )}
      </div>
    </div>
  );

  function renderObjectCard(obj, isComplete = false) {
    const pct = obj.total_steps > 0 ? Math.round((obj.answered_steps / obj.total_steps) * 100) : 0;
    const { icon: IconComp, cls } = getScenarioIcon(obj.scenario_name);
    const isOverdue = pct === 0 && !isComplete;

    let progressColor = 'var(--acc)';
    let badgeCls = 'bdg-pend';
    if (isComplete) { progressColor = 'var(--ok)'; badgeCls = 'bdg-ok'; }
    else if (isOverdue) { progressColor = 'var(--err)'; badgeCls = 'bdg-err'; }

    const crit = obj.criticality || 'normal';

    return (
      <div className="obj-card" key={obj.id} onClick={() => openObject(obj)}>
        <div className="obj-row">
          <div className={`ci ${cls}`}>
            <IconComp size={20} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
              <span style={{ fontSize: 14, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flex: 1 }}>
                {obj.name}
              </span>
              <span
                className={`crit-badge crit-${crit}`}
                onClick={e => { e.stopPropagation(); setCritModal(obj); }}
              >
                {CRIT_LABELS[crit]}
              </span>
              <span className={`bdg ${badgeCls}`}>{pct}%</span>
            </div>
            <div className="obj-meta">
              {obj.scenario_name} · {formatDate(obj.created_at)} · {daysSinceLabel(obj.created_at)}
              {' · '}
              <span
                className="obj-log-link"
                onClick={e => { e.stopPropagation(); navigate(`/objects/${obj.id}/log`); }}
              >
                <IconClock size={11} style={{ verticalAlign: 'middle', marginRight: 2 }} />
                История
              </span>
            </div>
            <div className="obj-progress-bar">
              <div className="obj-progress-fill" style={{ width: `${pct}%`, background: progressColor }} />
            </div>
            {isOverdue && (
              <div className="obj-overdue">
                <IconAlertCircle size={12} /> Просрочено
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }
}
