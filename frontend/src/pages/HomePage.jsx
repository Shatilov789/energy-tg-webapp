import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import {
  IconBuildingFactory,
  IconLineDashed,
  IconBolt,
  IconTool,
  IconClipboardCheck,
  IconPlus,
  IconBell,
  IconList,
  IconLayoutDashboard,
  IconAlertCircle,
  IconFileText,
  IconClipboardOff,
} from '@tabler/icons-react';

const SCENARIO_ICONS = {
  'Подстанция': { icon: IconBuildingFactory, cls: 'ci-a' },
  'КЛ линия': { icon: IconLineDashed, cls: 'ci-b' },
  'Трансформатор': { icon: IconBolt, cls: 'ci-r' },
  'Ремонт': { icon: IconTool, cls: 'ci-g' },
  'Проверка оборудования': { icon: IconClipboardCheck, cls: 'ci-p' },
};

export default function HomePage() {
  const navigate = useNavigate();
  const [objects, setObjects] = useState([]);
  const [objectMeta, setObjectMeta] = useState({});
  const [unreadCount, setUnreadCount] = useState(0);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    try {
      const [objectsData, unread, me] = await Promise.all([
        api.getMyObjects(),
        api.getUnreadCount().catch(() => ({ count: 0 })),
        api.getMe().catch(() => null),
      ]);
      setObjects(objectsData);
      setUnreadCount(unread.count || unread.unread_count || 0);
      setUser(me);

      const meta = {};
      for (const obj of objectsData) {
        try {
          const detail = await api.getObject(obj.id);
          const scenarioFull = await api.getScenario(obj.scenario_id);
          const answeredIds = new Set((detail.answers || []).map(a => a.step_id));
          const sorted = [...scenarioFull.steps].sort((a, b) => a.step_number - b.step_number);
          const first = sorted.find(s => !answeredIds.has(s.id));
          meta[obj.id] = {
            answered: answeredIds.size,
            total: scenarioFull.steps.length,
            nextStep: first ? first.step_number : sorted[sorted.length - 1]?.step_number || 1,
            scenarioName: scenarioFull.name,
          };
        } catch {
          meta[obj.id] = { answered: 0, total: 0, nextStep: 1, scenarioName: '' };
        }
      }
      setObjectMeta(meta);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function openObject(id) {
    const m = objectMeta[id];
    navigate(`/objects/${id}/steps/${m?.nextStep || 1}`);
  }

  function getIcon(name) {
    return SCENARIO_ICONS[name] || { icon: IconFileText, cls: 'ci-a' };
  }

  if (loading) return <div className="loading">Загрузка...</div>;
  if (error) return <div className="error">{error}</div>;

  const inProgress = objects.filter(o => {
    const m = objectMeta[o.id];
    return m && m.total > 0 && m.answered < m.total && m.answered > 0;
  });
  const notStarted = objects.filter(o => {
    const m = objectMeta[o.id];
    return m && m.total > 0 && m.answered === 0;
  });
  const completed = objects.filter(o => {
    const m = objectMeta[o.id];
    return m && m.total > 0 && m.answered >= m.total;
  });

  const isAdmin = user?.role === 'admin';

  return (
    <div className="page">
      <div className="tbar">
        <div style={{ flex: 1 }}>
          <h1>Мои объекты</h1>
          <div className="tbar-s">
            {objects.filter(o => {
              const m = objectMeta[o.id];
              return m && m.total > 0 && m.answered < m.total;
            }).length} активных
          </div>
        </div>
        <button className="fab-create" onClick={() => navigate('/objects')}>
          <IconPlus size={22} strokeWidth={2.5} />
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

      <div className="tabbar">
        <button className="tab on">
          <IconList size={22} />
          <span>Объекты</span>
          <div className="tab-indicator" />
        </button>
        <button className="tab" onClick={() => navigate('/objects')}>
          <IconPlus size={22} />
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
    const m = objectMeta[obj.id] || {};
    const pct = m.total > 0 ? Math.round((m.answered / m.total) * 100) : 0;
    const { icon: IconComp, cls } = getIcon(m.scenarioName);
    const isOverdue = pct === 0 && !isComplete;

    let progressColor = 'var(--acc)';
    let badgeCls = 'bdg-pend';
    if (isComplete) { progressColor = 'var(--ok)'; badgeCls = 'bdg-ok'; }
    else if (isOverdue) { progressColor = 'var(--err)'; badgeCls = 'bdg-err'; }

    return (
      <div className="obj-card" key={obj.id} onClick={() => openObject(obj.id)}>
        <div className="obj-row">
          <div className={`ci ${cls}`}>
            <IconComp size={20} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
              <span style={{ fontSize: 14, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {obj.name}
              </span>
              <span className={`bdg ${badgeCls}`}>{pct}%</span>
            </div>
            <div className="obj-meta">{m.scenarioName}</div>
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
