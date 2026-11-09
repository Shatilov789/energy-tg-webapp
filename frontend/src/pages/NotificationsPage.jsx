import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import {
  IconAlertCircle,
  IconAlertTriangle,
  IconMessage,
  IconShare,
  IconBell,
  IconBellOff,
  IconChecks,
  IconList,
  IconPlus,
  IconLayoutDashboard,
  IconMessageCircle,
} from '@tabler/icons-react';

const TYPE_CONFIG = {
  reminder: {
    icon: IconAlertCircle,
    bgColor: 'rgba(231,76,60,.12)',
    color: 'var(--err)',
    actionLabel: 'Заповнити зараз',
    actionColor: 'var(--err)',
    unreadCls: 'ni-unread-error',
    dotColor: 'var(--err)',
  },
  admin_comment: {
    icon: IconMessage,
    bgColor: 'rgba(59,139,235,.12)',
    color: 'var(--acc2)',
    actionLabel: 'Переглянути',
    actionColor: 'var(--acc2)',
    unreadCls: 'ni-unread-info',
    dotColor: 'var(--acc2)',
  },
  object_shared: {
    icon: IconShare,
    bgColor: 'rgba(46,204,113,.12)',
    color: 'var(--ok)',
    actionLabel: null,
    actionColor: null,
    unreadCls: 'ni-unread-success',
    dotColor: 'var(--ok)',
  },
  step_comment: {
    icon: IconMessageCircle,
    bgColor: 'rgba(59,139,235,.12)',
    color: 'var(--acc2)',
    actionLabel: 'Переглянути',
    actionColor: 'var(--acc2)',
    unreadCls: 'ni-unread-info',
    dotColor: 'var(--acc2)',
  },
  worker_assigned: {
    icon: IconShare,
    bgColor: 'rgba(61,190,122,.12)',
    color: 'var(--ok)',
    actionLabel: 'Відкрити',
    actionColor: 'var(--ok)',
    unreadCls: 'ni-unread-success',
    dotColor: 'var(--ok)',
  },
  worker_removed: {
    icon: IconAlertTriangle,
    bgColor: 'rgba(232,168,56,.12)',
    color: 'var(--warn)',
    actionLabel: null,
    actionColor: null,
    unreadCls: '',
    dotColor: 'var(--mu)',
  },
  object_completed: {
    icon: IconChecks,
    bgColor: 'rgba(61,190,122,.12)',
    color: 'var(--ok)',
    actionLabel: 'Переглянути',
    actionColor: 'var(--ok)',
    unreadCls: 'ni-unread-success',
    dotColor: 'var(--ok)',
  },
};

const DEFAULT_TYPE = {
  icon: IconBell,
  bgColor: 'var(--s2)',
  color: 'var(--mu)',
  actionLabel: null,
  actionColor: null,
  unreadCls: '',
  dotColor: 'var(--mu)',
};

let notificationsCache = null;
let notifUserCache = null;

export default function NotificationsPage() {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState(notificationsCache ?? []);
  const [user, setUser] = useState(notifUserCache ?? null);
  const [loading, setLoading] = useState(!notificationsCache);
  const showLoadingText = useDelayedLoadingText(loading);
  const isAdmin = user?.role === 'admin';

  useEffect(() => { load(); }, []);

  async function load() {
    try {
      const [data, me] = await Promise.all([api.getNotifications(), api.getMe().catch(() => null)]);
      setNotifications(data);
      notificationsCache = data;
      setUser(me);
      notifUserCache = me;
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function markAllRead() {
    try {
      await api.markAllRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch {}
  }

  async function markRead(id) {
    try {
      await api.markRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch {}
  }

  function formatTime(dateStr) {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now - d;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return `Сьогодні о ${d.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })}`;
    }
    if (diffDays === 1) {
      return `Вчора о ${d.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' })}`;
    }
    if (diffDays < 7) {
      return `${diffDays} дн. тому`;
    }
    return d.toLocaleDateString('uk-UA');
  }

  if (loading) return <div className="loading">{showLoadingText ? 'Завантаження...' : ''}</div>;

  const unread = notifications.filter(n => !n.is_read).length;

  return (
    <div className="page">
      <div className="tbar">
        <div style={{ flex: 1 }}>
          <h1>Сповіщення</h1>
          {unread > 0 && (
            <div className="tbar-s">{unread} непрочитаних</div>
          )}
        </div>
        {unread > 0 && (
          <button className="ib" onClick={markAllRead} title="Прочитати всі">
            <IconChecks size={18} />
          </button>
        )}
      </div>

      <div className="sc">
        {notifications.length === 0 ? (
          <div className="empty-state">
            <IconBellOff size={40} />
            Сповіщень поки немає
          </div>
        ) : (
          notifications.map(n => {
            const cfg = TYPE_CONFIG[n.type] || DEFAULT_TYPE;
            const IconComp = cfg.icon;
            return (
              <div
                key={n.id}
                className={`notif-item ${!n.is_read ? cfg.unreadCls : ''}`}
              >
                <div className="ni-icon" style={{ background: cfg.bgColor, color: cfg.color }}>
                  <IconComp size={18} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="ni-t">
                    {n.title || 'Сповіщення'}
                    {!n.is_read && (
                      <span className="ni-dot" style={{ background: cfg.dotColor }} />
                    )}
                  </div>
                  <div className="ni-tx">{n.message}</div>
                  {(cfg.actionLabel || !n.is_read) && (
                    <div className="ni-actions">
                      {cfg.actionLabel && (
                        <button
                          className="ni-action"
                          style={{ background: cfg.actionColor }}
                          onClick={e => {
                            e.stopPropagation();
                            if (n.object_id && n.step_number) {
                              navigate(`/objects/${n.object_id}/steps/${n.step_number}`);
                            } else {
                              navigate('/');
                            }
                          }}
                        >
                          {cfg.actionLabel}
                        </button>
                      )}
                      {!n.is_read && (
                        <button
                          className="ni-mark-read"
                          onClick={() => markRead(n.id)}
                        >
                          Прочитано
                        </button>
                      )}
                    </div>
                  )}
                  <div className="ni-time">{formatTime(n.created_at)}</div>
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="tabbar">
        <button className="tab" onClick={() => navigate('/')}>
          <IconList size={22} />
          <span>Обʼєкти</span>
        </button>
        <button className="tab" onClick={() => navigate('/objects')}>
          <IconPlus size={22} />
          <span>Створити</span>
        </button>
        <button className="tab on">
          <IconBell size={22} />
          <span>Сповіщення</span>
          <div className="tab-indicator" />
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
}
