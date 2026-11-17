import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import { IconBell, IconChartBar, IconList, IconUserPlus } from '@tabler/icons-react';
import CreateUserModal from '../components/admin/CreateUserModal';
import UsersTab from '../components/admin/UsersTab';

let adminCache = null;

export default function AdminPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState(adminCache?.users ?? []);
  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(!adminCache);
  const [error, setError] = useState(null);
  const showLoadingText = useDelayedLoadingText(loading);
  const [userModalOpen, setUserModalOpen] = useState(false);

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    try {
      const [usrs, meData] = await Promise.all([api.getAdminUsers(), api.getMe()]);
      setUsers(usrs);
      setMe(meData);
      adminCache = { users: usrs };
    } catch (err) {
      if (!adminCache) setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleActive(userId) {
    try {
      await api.toggleUserActive(userId);
      await loadData();
    } catch (err) {
      alert(err.message);
    }
  }

  async function handleCreateUser(payload) {
    await api.createUser(payload);
    setUserModalOpen(false);
    await loadData();
  }

  if (loading) return <div className="loading">{showLoadingText ? 'Завантаження...' : ''}</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="page">
      <div className="tbar">
        <div style={{ flex: 1 }}>
          <h1>Адміністрування</h1>
          <div className="tbar-s">Керування користувачами</div>
        </div>
        <button className="ib" title="Додати користувача" onClick={() => setUserModalOpen(true)}>
          <IconUserPlus size={18} />
        </button>
      </div>

      <div className="sc">
        <UsersTab users={users} currentUserId={me?.id} onToggleActive={handleToggleActive} />
      </div>

      <div className="tabbar">
        <button className="tab on">
          <IconChartBar size={22} />
          <span>Огляд</span>
          <div className="tab-indicator" />
        </button>
        <button className="tab" onClick={() => navigate('/')}>
          <IconList size={22} />
          <span>Обʼєкти</span>
        </button>
        <button className="tab" onClick={() => navigate('/notifications')} style={{ position: 'relative' }}>
          <IconBell size={22} />
          <span>Сповіщення</span>
        </button>
      </div>

      {userModalOpen && (
        <CreateUserModal onCreate={handleCreateUser} onClose={() => setUserModalOpen(false)} />
      )}
    </div>
  );
}
