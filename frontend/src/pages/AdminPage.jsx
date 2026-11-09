import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import {
  IconBell,
  IconChartBar,
  IconCircleCheck,
  IconDownload,
  IconList,
  IconUserPlus,
  IconUsers,
} from '@tabler/icons-react';
import CommentModal from '../components/admin/CommentModal';
import CompletedTab from '../components/admin/CompletedTab';
import CreateUserModal from '../components/admin/CreateUserModal';
import ObjectsTab from '../components/admin/ObjectsTab';
import UsersTab from '../components/admin/UsersTab';
import WorkerModal from '../components/admin/WorkerModal';
import { buildMetrics, groupByWorker, isFullyAnswered } from '../components/admin/objectStats';

let adminCache = null;

function withToggled(set, id) {
  const next = new Set(set);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  return next;
}

export default function AdminPage() {
  const navigate = useNavigate();
  const [objects, setObjects] = useState(adminCache?.objects ?? []);
  const [users, setUsers] = useState(adminCache?.users ?? []);
  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(!adminCache);
  const [error, setError] = useState(null);
  const showLoadingText = useDelayedLoadingText(loading);
  const [tab, setTab] = useState('objects'); // 'objects' | 'completed' | 'users'
  const [commentModal, setCommentModal] = useState(null);
  const [workerModal, setWorkerModal] = useState(null);
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [expandedWorkers, setExpandedWorkers] = useState(new Set());
  const [expandedObjects, setExpandedObjects] = useState(new Set());
  const [objectNotes, setObjectNotes] = useState({}); // { objectId: { stepId: notes[] } }

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    try {
      const [objs, usrs, meData] = await Promise.all([
        api.getAdminObjects(),
        api.getAdminUsers(),
        api.getMe(),
      ]);
      setObjects(objs);
      setUsers(usrs);
      setMe(meData);
      adminCache = { objects: objs, users: usrs };
      setObjectNotes({});
    } catch (err) {
      if (!adminCache) setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function toggleObject(obj) {
    const isOpening = !expandedObjects.has(obj.id);
    setExpandedObjects(prev => withToggled(prev, obj.id));
    if (!isOpening || objectNotes[obj.id]) return;

    const notesByStep = {};
    await Promise.all((obj.answers || []).map(async ({ step_id: stepId }) => {
      try { notesByStep[stepId] = await api.getStatusNotes(obj.id, stepId); }
      catch { notesByStep[stepId] = []; }
    }));
    setObjectNotes(prev => ({ ...prev, [obj.id]: notesByStep }));
  }

  async function handleAddWorker(userId) {
    await api.addWorker(workerModal.objectId, userId);
    await loadData();
  }

  async function handleRemoveWorker(objectId, userId) {
    try {
      await api.removeWorker(objectId, userId);
      await loadData();
    } catch (err) {
      alert(err.message);
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

  async function handleComment(text) {
    await api.addComment(commentModal.answerId, { comment_text: text });
    setCommentModal(null);
    await loadData();
  }

  if (loading) return <div className="loading">{showLoadingText ? 'Завантаження...' : ''}</div>;
  if (error) return <div className="error">{error}</div>;

  const completedObjects = objects.filter(isFullyAnswered);
  const activeObjects = objects.filter(o => !isFullyAnswered(o));
  const { byWorker, unassigned } = groupByWorker(activeObjects);
  const workersWithObjects = users.filter(u => byWorker[u.id]?.length > 0);

  return (
    <div className="page">
      <div className="tbar">
        <div style={{ flex: 1 }}>
          <h1>Адміністрування</h1>
          <div className="tbar-s">{tab === 'objects' ? 'Загальний огляд інспекцій' : 'Керування користувачами'}</div>
        </div>
        {tab === 'users' && (
          <button className="ib" title="Додати користувача" onClick={() => setUserModalOpen(true)}>
            <IconUserPlus size={18} />
          </button>
        )}
        {tab === 'objects' && (
          <button className="ib" title="Експорт">
            <IconDownload size={18} />
          </button>
        )}
      </div>

      <div className="adm-tabs">
        <button className={`adm-tab${tab === 'objects' ? ' on' : ''}`} onClick={() => setTab('objects')}>
          <IconChartBar size={15} /> В роботі
          {activeObjects.length > 0 && <span className="adm-tab-badge">{activeObjects.length}</span>}
        </button>
        <button className={`adm-tab${tab === 'completed' ? ' on' : ''}`} onClick={() => setTab('completed')}>
          <IconCircleCheck size={15} /> Завершені
          {completedObjects.length > 0 && (
            <span className="adm-tab-badge" style={{ background: 'var(--ok)' }}>{completedObjects.length}</span>
          )}
        </button>
        <button className={`adm-tab${tab === 'users' ? ' on' : ''}`} onClick={() => setTab('users')}>
          <IconUsers size={15} /> Люди
          <span className="adm-tab-badge">{users.length}</span>
        </button>
      </div>

      <div className="sc">
        {tab === 'users' && (
          <UsersTab users={users} currentUserId={me?.id} onToggleActive={handleToggleActive} />
        )}
        {tab === 'completed' && <CompletedTab objects={completedObjects} />}
        {tab === 'objects' && (
          <ObjectsTab
            metrics={buildMetrics(objects)}
            workers={workersWithObjects}
            objectsByWorker={byWorker}
            unassignedObjects={unassigned}
            expandedWorkers={expandedWorkers}
            expandedObjects={expandedObjects}
            objectNotes={objectNotes}
            onToggleWorker={id => setExpandedWorkers(prev => withToggled(prev, id))}
            onToggleObject={toggleObject}
            onRemoveWorker={handleRemoveWorker}
            onOpenWorkerModal={setWorkerModal}
            onOpenComment={setCommentModal}
          />
        )}
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

      {workerModal && (
        <WorkerModal
          users={users}
          currentWorkerIds={workerModal.currentWorkerIds}
          onAdd={handleAddWorker}
          onClose={() => setWorkerModal(null)}
        />
      )}
      {commentModal && (
        <CommentModal
          stepText={commentModal.stepText}
          onSubmit={handleComment}
          onClose={() => setCommentModal(null)}
        />
      )}
      {userModalOpen && (
        <CreateUserModal onCreate={handleCreateUser} onClose={() => setUserModalOpen(false)} />
      )}
    </div>
  );
}
