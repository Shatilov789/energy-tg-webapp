import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import { formatDate, daysSinceLabel } from '../utils/date';
import {
  IconBolt,
  IconBell,
  IconList,
  IconLayoutDashboard,
  IconClipboardOff,
  IconGitBranch,
} from '@tabler/icons-react';
import { DEAL_STATUS_LABELS, getProcessIcon } from '../processes';

// Last successful snapshot: returning to the page renders it at once,
// without a spinner, while a quiet refetch runs in the background.
let homeCache = null;

export default function HomePage() {
  const navigate = useNavigate();
  const [deals, setDeals] = useState(homeCache?.deals ?? []);
  const [unreadCount, setUnreadCount] = useState(homeCache?.unreadCount ?? 0);
  const [user, setUser] = useState(homeCache?.user ?? null);
  const [loading, setLoading] = useState(!homeCache);
  const [error, setError] = useState(null);
  const [homeTab, setHomeTab] = useState('active'); // 'active' | 'completed'
  const showLoadingText = useDelayedLoadingText(loading);

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    try {
      const [dealsData, unread, me] = await Promise.all([
        api.getDeals(),
        api.getUnreadCount().catch(() => ({ count: 0 })),
        api.getMe().catch(() => null),
      ]);
      const unreadCountVal = unread.count || unread.unread_count || 0;
      setDeals(dealsData);
      setUnreadCount(unreadCountVal);
      setUser(me);
      homeCache = { deals: dealsData, unreadCount: unreadCountVal, user: me };
    } catch (err) {
      if (!homeCache) setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function openDeal(deal) {
    navigate(`/deals/${deal.id}`);
  }

  if (loading) return <div className="loading">{showLoadingText ? 'Завантаження...' : ''}</div>;
  if (error) return <div className="error">{error}</div>;

  const sorted = [...deals].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  const active = sorted.filter(d => d.status === 'active');
  const completed = sorted.filter(d => d.status !== 'active');

  const isAdmin = user?.role === 'admin';

  return (
    <div className="page">
      <div className="tbar">
        <div style={{ flex: 1 }}>
          <h1>Мої угоди</h1>
          <div className="tbar-s">{active.length} активних</div>
        </div>
        <button className="fab-create" onClick={() => navigate('/deals/new')}>
          <IconBolt size={22} strokeWidth={2.5} />
        </button>
      </div>

      <div className="adm-tabs">
        <button
          className={`adm-tab${homeTab === 'active' ? ' on' : ''}`}
          onClick={() => setHomeTab('active')}
        >
          В роботі
          {active.length > 0 && <span className="adm-tab-badge">{active.length}</span>}
        </button>
        <button
          className={`adm-tab${homeTab === 'completed' ? ' on' : ''}`}
          onClick={() => setHomeTab('completed')}
        >
          Завершені
          {completed.length > 0 && (
            <span className="adm-tab-badge" style={{ background: 'var(--ok)' }}>{completed.length}</span>
          )}
        </button>
      </div>

      <div className="sc">
        {homeTab === 'active' && (
          active.length > 0
            ? active.map(d => renderDealCard(d))
            : (
              <div className="empty-state">
                <IconClipboardOff size={40} />
                Угод поки немає. Створіть першу!
              </div>
            )
        )}

        {homeTab === 'completed' && (
          completed.length > 0
            ? completed.map(d => renderDealCard(d, true))
            : (
              <div className="empty-state">
                <IconClipboardOff size={40} />
                Завершених угод поки немає
              </div>
            )
        )}
      </div>

      <div className="tabbar">
        <button className="tab on">
          <IconList size={22} />
          <span>Угоди</span>
          <div className="tab-indicator" />
        </button>
        <button className="tab" onClick={() => navigate('/deals/new')}>
          <IconBolt size={22} />
          <span>Створити</span>
        </button>
        <button className="tab" onClick={() => navigate('/notifications')} style={{ position: 'relative' }}>
          <IconBell size={22} />
          <span>Сповіщення</span>
          {unreadCount > 0 && <span className="tab-notif-badge">{unreadCount}</span>}
        </button>
        {isAdmin && (
          <button className="tab" onClick={() => navigate('/admin')}>
            <IconLayoutDashboard size={22} />
            <span>Адмін</span>
          </button>
        )}
      </div>
    </div>
  );

  function renderDealCard(deal, isComplete = false) {
    const badgeCls = isComplete ? 'bdg-ok' : 'bdg-pend';
    const ProcessIcon = getProcessIcon(deal.process_type);
    return (
      <div className="obj-card" key={deal.id} onClick={() => openDeal(deal)}>
        <div className="obj-row">
          <div className="ci ci-a">
            <ProcessIcon size={20} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
              <span style={{ fontSize: 14, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flex: 1 }}>
                {deal.client_name}
              </span>
              <span className={`bdg ${badgeCls}`}>{DEAL_STATUS_LABELS[deal.status] || deal.status}</span>
            </div>
            <div className="obj-meta">
              {deal.process_type} · {deal.client_phone} · {formatDate(deal.created_at)} · {daysSinceLabel(deal.created_at)}
            </div>
            {!isComplete && deal.current_stage_name && (
              <div className="obj-meta" style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
                <IconGitBranch size={11} />
                {deal.current_stage_code}: {deal.current_stage_name}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }
}
