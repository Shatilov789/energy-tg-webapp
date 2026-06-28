import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import { daysSinceLabel, formatDate, formatDateTime } from '../utils/date';
import {
  IconChartBar,
  IconList,
  IconBell,
  IconDownload,
  IconLock,
  IconLockOpen,
  IconMessagePlus,
  IconChecks,
  IconUserPlus,
  IconUserMinus,
  IconUsers,
  IconShield,
  IconTool,
  IconChevronDown,
  IconChevronRight,
  IconCircleCheck,
} from '@tabler/icons-react';

const AVA_COLORS = ['ava-a', 'ava-b', 'ava-c', 'ava-d'];

function getInitials(firstName, lastName) {
  const f = (firstName || '').charAt(0).toUpperCase();
  const l = (lastName || '').charAt(0).toUpperCase();
  return f + l || '??';
}

let adminCache = null;

export default function AdminPage() {
  const navigate = useNavigate();
  const [objects, setObjects] = useState(adminCache?.objects ?? []);
  const [users, setUsers] = useState(adminCache?.users ?? []);
  const [loading, setLoading] = useState(!adminCache);
  const [error, setError] = useState(null);
  const showLoadingText = useDelayedLoadingText(loading);
  const [tab, setTab] = useState('objects'); // 'objects' | 'completed' | 'users'
  const [commentModal, setCommentModal] = useState(null);
  const [commentText, setCommentText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [workerModal, setWorkerModal] = useState(null);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [userModal, setUserModal] = useState(false);
  const [newUser, setNewUser] = useState({ telegram_id: '', first_name: '', last_name: '', username: '', role: 'worker' });
  const [creatingUser, setCreatingUser] = useState(false);
  const [me, setMe] = useState(null);
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

  function toggleWorker(id) {
    setExpandedWorkers(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  async function toggleObject(obj) {
    const id = obj.id;
    const isOpening = !expandedObjects.has(id);
    setExpandedObjects(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
    if (isOpening && !objectNotes[id]) {
      const stepIds = (obj.answers || []).map(a => a.step_id);
      const notesMap = {};
      await Promise.all(stepIds.map(async stepId => {
        try { notesMap[stepId] = await api.getStatusNotes(id, stepId); }
        catch { notesMap[stepId] = []; }
      }));
      setObjectNotes(prev => ({ ...prev, [id]: notesMap }));
    }
  }

  async function handleAddWorker() {
    if (!workerModal || !selectedUserId) return;
    try {
      await api.addWorker(workerModal.objectId, Number(selectedUserId));
      setSelectedUserId('');
      await loadData();
    } catch (err) {
      alert(err.message);
    }
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

  async function handleCreateUser() {
    if (!newUser.telegram_id || !newUser.first_name) return;
    setCreatingUser(true);
    try {
      await api.createUser({ ...newUser, telegram_id: Number(newUser.telegram_id) });
      setUserModal(false);
      setNewUser({ telegram_id: '', first_name: '', last_name: '', username: '', role: 'worker' });
      await loadData();
    } catch (err) {
      alert(err.message);
    } finally {
      setCreatingUser(false);
    }
  }

  async function handleComment() {
    if (!commentModal || !commentText.trim()) return;
    setSubmitting(true);
    try {
      await api.addComment(commentModal.answerId, { comment_text: commentText.trim() });
      setCommentModal(null);
      setCommentText('');
      await loadData();
    } catch (err) {
      alert(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="loading">{showLoadingText ? 'Загрузка...' : ''}</div>;
  if (error) return <div className="error">{error}</div>;

  const userMap = {};
  users.forEach(u => { userMap[u.id] = u; });

  // Metrics
  const totalObjects = objects.length;
  const completedObjects = objects.filter(o => o.status === 'completed').length;
  const inProgressObjects = totalObjects - completedObjects;

  let totalAnswered = 0;
  let totalQuestions = 0;
  objects.forEach(obj => {
    const stepsCount = obj.scenario?.steps?.length || 0;
    const answersCount = obj.answers?.length || 0;
    totalAnswered += answersCount;
    totalQuestions += stepsCount;
  });
  const overallPct = totalQuestions > 0 ? Math.round((totalAnswered / totalQuestions) * 100) : 0;
  const overdueCount = objects.filter(o => {
    const pct = o.scenario?.steps?.length > 0
      ? Math.round(((o.answers?.length || 0) / o.scenario.steps.length) * 100)
      : 0;
    return pct === 0 && o.status !== 'completed';
  }).length;

  const metrics = [
    { label: 'Выполнено', value: `${overallPct}%`, sub: 'средний прогресс', color: 'var(--acc)' },
    { label: 'Объектов', value: inProgressObjects, sub: 'в работе', color: 'var(--acc2)' },
    { label: 'Просрочено', value: overdueCount, sub: 'требуют внимания', color: 'var(--err)' },
    { label: 'Завершено', value: completedObjects, sub: 'инспекций', color: 'var(--ok)' },
  ];

  // Разделяем активные и завершённые
  const activeObjects = objects.filter(o => {
    const stepsCount = o.scenario?.steps?.length || 0;
    const answersCount = o.answers?.length || 0;
    return stepsCount === 0 || answersCount < stepsCount;
  });
  const completedObjectsList = objects.filter(o => {
    const stepsCount = o.scenario?.steps?.length || 0;
    const answersCount = o.answers?.length || 0;
    return stepsCount > 0 && answersCount >= stepsCount;
  });

  // Group active objects by worker userId
  const workerObjectsMap = {};
  const unassignedObjects = [];
  for (const obj of activeObjects) {
    if (!obj.workers || obj.workers.length === 0) {
      unassignedObjects.push(obj);
    } else {
      for (const w of obj.workers) {
        if (!workerObjectsMap[w.user_id]) workerObjectsMap[w.user_id] = [];
        if (!workerObjectsMap[w.user_id].find(o => o.id === obj.id)) {
          workerObjectsMap[w.user_id].push(obj);
        }
      }
    }
  }

  // Workers that have at least one active object
  const workersWithObjects = users.filter(u => workerObjectsMap[u.id]?.length > 0);

  function renderObjectExpanded(obj) {
    const stepsCount = obj.scenario?.steps?.length || 0;
    const answersCount = obj.answers?.length || 0;
    const pct = stepsCount > 0 ? Math.round((answersCount / stepsCount) * 100) : 0;
    const notesLoaded = !!objectNotes[obj.id];

    const answeredItems = (obj.answers || []).map(a => ({
      answer: a,
      step: obj.scenario?.steps?.find(s => s.id === a.step_id),
      notes: objectNotes[obj.id]?.[a.step_id] || [],
    })).filter(x => x.step).sort((a, b) => a.step.step_number - b.step.step_number);

    return (
      <div className="obj-body">
        {/* Ответственные */}
        <div className="adm-workers-row">
          <IconUsers size={12} style={{ color: 'var(--mu)', flexShrink: 0 }} />
          <div className="adm-workers-list">
            {(obj.workers || []).map(w => (
              <span className="adm-worker-tag" key={w.user_id}>
                {w.user?.first_name} {(w.user?.last_name || '').charAt(0)}.
                <button
                  className="adm-worker-remove"
                  onClick={() => handleRemoveWorker(obj.id, w.user_id)}
                  title="Убрать ответственного"
                >×</button>
              </span>
            ))}
            <button
              className="adm-worker-add"
              onClick={() => setWorkerModal({ objectId: obj.id, currentWorkerIds: (obj.workers || []).map(w => w.user_id) })}
              title="Добавить ответственного"
            >
              <IconUserPlus size={12} />
            </button>
          </div>
        </div>

        {/* Прогресс */}
        <div className="obj-progress-bar" style={{ marginTop: 8 }}>
          <div className="obj-progress-fill" style={{
            width: `${pct}%`,
            background: pct === 100 ? 'var(--ok)' : pct === 0 ? 'var(--err)' : 'var(--acc)',
          }} />
        </div>
        <div style={{ fontSize: 11, color: 'var(--mu)', marginTop: 4, marginBottom: 8 }}>
          {answersCount} из {stepsCount} этапов заполнено
        </div>

        {!notesLoaded && (
          <div style={{ fontSize: 12, color: 'var(--mu)', fontStyle: 'italic' }}>Загрузка...</div>
        )}

        {notesLoaded && answeredItems.length === 0 && (
          <div style={{ fontSize: 12, color: 'var(--mu)', fontStyle: 'italic', padding: '4px 0' }}>
            Записей пока нет
          </div>
        )}

        {notesLoaded && answeredItems.map(({ answer, step, notes }) => (
          <div className="adm-detail" key={answer.id}>
            <div style={{ fontSize: 11, color: 'var(--mu)', marginBottom: 4 }}>
              Этап {step.step_number} · {step.question_text}
            </div>

            {notes.length === 0 && (
              <div style={{ fontSize: 12, color: 'var(--mu)', fontStyle: 'italic', marginBottom: 8 }}>
                Нет записей
              </div>
            )}

            {notes.map(note => (
              <div key={note.id} style={{
                fontSize: 13,
                color: 'var(--tx)',
                background: 'var(--bg)',
                border: '1px solid var(--br)',
                borderRadius: 'var(--rs)',
                padding: '9px 12px',
                lineHeight: 1.45,
                marginBottom: 6,
                whiteSpace: 'pre-wrap',
              }}>
                <div>{note.note_text}</div>
                <div style={{ fontSize: 11, color: 'var(--mu)', marginTop: 5 }}>
                  {note.author?.first_name} {note.author?.last_name || ''} · {formatDateTime(note.created_at)}
                </div>
              </div>
            ))}

            <div className="adm-actions">
              <button className="comment-btn" onClick={() => setCommentModal({ answerId: answer.id, stepText: step.question_text })}>
                <IconMessagePlus size={13} /> Комментарий
              </button>
            </div>
          </div>
        ))}
      </div>
    );
  }

  function renderObjectRow(obj, idx) {
    const stepsCount = obj.scenario?.steps?.length || 0;
    const answersCount = obj.answers?.length || 0;
    const pct = stepsCount > 0 ? Math.round((answersCount / stepsCount) * 100) : 0;
    const isOpen = expandedObjects.has(obj.id);

    let badgeCls = 'bdg-pend';
    if (pct === 0) badgeCls = 'bdg-err';
    if (pct === 100) badgeCls = 'bdg-ok';

    return (
      <div className="obj-accordion" key={obj.id}>
        <div className="obj-row" onClick={() => toggleObject(obj)}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {obj.name}
            </div>
            <div style={{ fontSize: 11, color: 'var(--mu)', marginTop: 2 }}>
              {obj.scenario?.name || '—'} · {formatDate(obj.created_at)}
            </div>
          </div>
          <span className={`bdg ${badgeCls}`}>{pct}%</span>
          <span className="obj-caret">
            {isOpen ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}
          </span>
        </div>
        {isOpen && renderObjectExpanded(obj)}
      </div>
    );
  }

  return (
    <div className="page">
      <div className="tbar">
        <div style={{ flex: 1 }}>
          <h1>Администрирование</h1>
          <div className="tbar-s">{tab === 'objects' ? 'Общий обзор инспекций' : 'Управление пользователями'}</div>
        </div>
        {tab === 'users' && (
          <button className="ib" title="Добавить пользователя" onClick={() => setUserModal(true)}>
            <IconUserPlus size={18} />
          </button>
        )}
        {tab === 'objects' && (
          <button className="ib" title="Экспорт">
            <IconDownload size={18} />
          </button>
        )}
      </div>

      {/* Внутренние табы */}
      <div className="adm-tabs">
        <button className={`adm-tab${tab === 'objects' ? ' on' : ''}`} onClick={() => setTab('objects')}>
          <IconChartBar size={15} /> В работе
          {activeObjects.length > 0 && <span className="adm-tab-badge">{activeObjects.length}</span>}
        </button>
        <button className={`adm-tab${tab === 'completed' ? ' on' : ''}`} onClick={() => setTab('completed')}>
          <IconCircleCheck size={15} /> Завершённые
          {completedObjectsList.length > 0 && (
            <span className="adm-tab-badge" style={{ background: 'var(--ok)' }}>{completedObjectsList.length}</span>
          )}
        </button>
        <button className={`adm-tab${tab === 'users' ? ' on' : ''}`} onClick={() => setTab('users')}>
          <IconUsers size={15} /> Люди
          <span className="adm-tab-badge">{users.length}</span>
        </button>
      </div>

      <div className="sc">
        {/* ===== TAB: USERS ===== */}
        {tab === 'users' && (
          <>
            {users.length === 0 && (
              <div className="empty-state"><IconUsers size={40} />Пользователей нет</div>
            )}
            {users.map(u => {
              const isSelf = me?.id === u.id;
              return (
                <div className={`user-card${u.is_active ? '' : ' inactive'}`} key={u.id}>
                  <div className={`ava ${u.role === 'admin' ? 'ava-a' : 'ava-b'}`}>
                    {getInitials(u.first_name, u.last_name)}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>
                      {u.first_name} {u.last_name || ''}
                      {isSelf && <span style={{ fontSize: 11, color: 'var(--acc)', marginLeft: 6 }}>это вы</span>}
                      {u.username && <span style={{ fontSize: 11, color: 'var(--mu)', marginLeft: 6 }}>@{u.username}</span>}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 3 }}>
                      <span className={`bdg ${u.role === 'admin' ? 'bdg-pend' : 'bdg-ok'}`}>
                        {u.role === 'admin' ? 'Администратор' : 'Сотрудник'}
                      </span>
                      <span className={`user-status${u.is_active ? ' active' : ' inactive'}`}>
                        {u.is_active ? <IconLockOpen size={11} /> : <IconLock size={11} />}
                        {u.is_active ? 'Активен' : 'Деактивирован'}
                      </span>
                    </div>
                  </div>
                  <button
                    className={`user-toggle-btn${u.is_active ? '' : ' locked'}`}
                    title={isSelf ? 'Нельзя деактивировать себя' : u.is_active ? 'Деактивировать' : 'Активировать'}
                    onClick={() => !isSelf && handleToggleActive(u.id)}
                    disabled={isSelf}
                  >
                    {u.is_active ? <IconLockOpen size={18} /> : <IconLock size={18} />}
                  </button>
                </div>
              );
            })}
            <div style={{ height: 20 }} />
          </>
        )}

        {/* ===== TAB: COMPLETED ===== */}
        {tab === 'completed' && <>
          {completedObjectsList.length === 0 ? (
            <div className="empty-state">
              <IconCircleCheck size={40} />
              Завершённых объектов пока нет
            </div>
          ) : (
            <>
              <div className="slbl" style={{ marginTop: 4 }}>
                {completedObjectsList.length} {completedObjectsList.length === 1 ? 'объект' : completedObjectsList.length < 5 ? 'объекта' : 'объектов'} завершено
              </div>
              {completedObjectsList.map(obj => {
                const workers = obj.workers || [];
                return (
                  <div className="obj-accordion" key={obj.id}>
                    <div className="obj-row" style={{ cursor: 'default' }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {obj.name}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--mu)', marginTop: 2 }}>
                          {obj.scenario?.name || '—'} · {formatDate(obj.created_at)}
                        </div>
                        {workers.length > 0 && (
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 5 }}>
                            {workers.map(w => (
                              <span className="adm-worker-tag" key={w.user_id} style={{ cursor: 'default' }}>
                                {w.user?.first_name} {(w.user?.last_name || '').charAt(0)}{w.user?.last_name ? '.' : ''}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <span className="bdg bdg-ok">100%</span>
                    </div>
                  </div>
                );
              })}
            </>
          )}
          <div style={{ height: 20 }} />
        </>}

        {/* ===== TAB: OBJECTS ===== */}
        {tab === 'objects' && <>
          {/* Metric grid */}
          <div className="dash-grid" style={{ marginTop: 4 }}>
            {metrics.map(m => (
              <div className="mc" key={m.label}>
                <div className="mc-label">{m.label}</div>
                <div className="mv" style={{ color: m.color }}>{m.value}</div>
                <div className="ml">{m.sub}</div>
              </div>
            ))}
          </div>

          <div className="slbl">Сотрудники</div>

          {workersWithObjects.length === 0 && unassignedObjects.length === 0 && (
            <div className="empty-state">
              <IconChecks size={40} />
              Объектов нет
            </div>
          )}

          {/* Worker accordion */}
          {workersWithObjects.map((worker, idx) => {
            const workerObjs = workerObjectsMap[worker.id] || [];
            const isOpen = expandedWorkers.has(worker.id);
            return (
              <div className="wkr-accordion" key={worker.id}>
                <div className="wkr-row" onClick={() => toggleWorker(worker.id)}>
                  <div className={`ava ${AVA_COLORS[idx % AVA_COLORS.length]}`}>
                    {getInitials(worker.first_name, worker.last_name)}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>
                      {worker.first_name} {worker.last_name || ''}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--mu)', marginTop: 2 }}>
                      {workerObjs.length} {workerObjs.length === 1 ? 'объект' : workerObjs.length < 5 ? 'объекта' : 'объектов'}
                    </div>
                  </div>
                  <span style={{ color: 'var(--mu)', display: 'flex' }}>
                    {isOpen ? <IconChevronDown size={16} /> : <IconChevronRight size={16} />}
                  </span>
                </div>
                {isOpen && (
                  <div className="wkr-body">
                    {workerObjs.map((obj, i) => renderObjectRow(obj, i))}
                  </div>
                )}
              </div>
            );
          })}

          {/* Unassigned objects */}
          {unassignedObjects.length > 0 && (
            <>
              <div className="slbl" style={{ marginTop: 8 }}>Без ответственных</div>
              {unassignedObjects.map((obj, i) => renderObjectRow(obj, i))}
            </>
          )}

          <div style={{ height: 20 }} />
        </>}
      </div>

      <div className="tabbar">
        <button className="tab on">
          <IconChartBar size={22} />
          <span>Обзор</span>
          <div className="tab-indicator" />
        </button>
        <button className="tab" onClick={() => navigate('/')}>
          <IconList size={22} />
          <span>Объекты</span>
        </button>
        <button className="tab" onClick={() => navigate('/notifications')} style={{ position: 'relative' }}>
          <IconBell size={22} />
          <span>Оповещения</span>
        </button>
      </div>

      {/* Модалка управления ответственными */}
      {workerModal && (
        <div className="comment-overlay" onClick={() => { setWorkerModal(null); setSelectedUserId(''); }}>
          <div className="comment-modal" onClick={e => e.stopPropagation()}>
            <h3>Ответственные за объект</h3>
            <div style={{ fontSize: 12, color: 'var(--mu)', marginBottom: 12 }}>
              Выберите сотрудника для добавления
            </div>
            <select
              className="scen-select-native"
              value={selectedUserId}
              onChange={e => setSelectedUserId(e.target.value)}
            >
              <option value="">— выбрать сотрудника —</option>
              {users
                .filter(u => u.role === 'worker' && !workerModal.currentWorkerIds.includes(u.id))
                .map(u => (
                  <option key={u.id} value={u.id}>
                    {u.first_name} {u.last_name || ''}
                  </option>
                ))
              }
            </select>
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <button className="btn-s" style={{ flex: 1 }} onClick={() => { setWorkerModal(null); setSelectedUserId(''); }}>
                Отмена
              </button>
              <button
                className="btn-p"
                style={{ flex: 1 }}
                onClick={handleAddWorker}
                disabled={!selectedUserId}
              >
                <IconUserPlus size={14} /> Добавить
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модалка комментария */}
      {commentModal && (
        <div className="comment-overlay" onClick={() => setCommentModal(null)}>
          <div className="comment-modal" onClick={e => e.stopPropagation()}>
            <h3>Комментарий к ответу</h3>
            <div style={{ fontSize: 12, color: 'var(--mu)', marginBottom: 10 }}>
              {commentModal.stepText}
            </div>
            <textarea
              className="qtextarea"
              placeholder="Введите комментарий..."
              value={commentText}
              onChange={e => setCommentText(e.target.value)}
              rows={3}
              autoFocus
            />
            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <button className="btn-s" style={{ flex: 1 }} onClick={() => setCommentModal(null)}>
                Отмена
              </button>
              <button
                className="btn-p"
                style={{ flex: 1 }}
                onClick={handleComment}
                disabled={submitting || !commentText.trim()}
              >
                {submitting ? 'Отправка...' : 'Отправить'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модалка создания пользователя */}
      {userModal && (
        <div className="comment-overlay" onClick={() => setUserModal(false)}>
          <div className="comment-modal" onClick={e => e.stopPropagation()}>
            <h3>Новый пользователь</h3>
            <div className="fgrp" style={{ marginTop: 8 }}>
              <label className="flbl">Telegram ID *</label>
              <input className="finp" type="number" placeholder="123456789"
                value={newUser.telegram_id}
                onChange={e => setNewUser(p => ({ ...p, telegram_id: e.target.value }))} />
            </div>
            <div className="fgrp">
              <label className="flbl">Имя *</label>
              <input className="finp" type="text" placeholder="Иван"
                value={newUser.first_name}
                onChange={e => setNewUser(p => ({ ...p, first_name: e.target.value }))} />
            </div>
            <div className="fgrp">
              <label className="flbl">Фамилия</label>
              <input className="finp" type="text" placeholder="Петров"
                value={newUser.last_name}
                onChange={e => setNewUser(p => ({ ...p, last_name: e.target.value }))} />
            </div>
            <div className="fgrp">
              <label className="flbl">Username</label>
              <input className="finp" type="text" placeholder="ivanpetrov"
                value={newUser.username}
                onChange={e => setNewUser(p => ({ ...p, username: e.target.value }))} />
            </div>
            <div className="fgrp">
              <label className="flbl">Роль</label>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  className={`role-btn${newUser.role === 'worker' ? ' on' : ''}`}
                  onClick={() => setNewUser(p => ({ ...p, role: 'worker' }))}
                >
                  <IconTool size={14} /> Сотрудник
                </button>
                <button
                  className={`role-btn${newUser.role === 'admin' ? ' on' : ''}`}
                  onClick={() => setNewUser(p => ({ ...p, role: 'admin' }))}
                >
                  <IconShield size={14} /> Администратор
                </button>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
              <button className="btn-s" style={{ flex: 1 }} onClick={() => setUserModal(false)}>Отмена</button>
              <button
                className="btn-p" style={{ flex: 1 }}
                onClick={handleCreateUser}
                disabled={creatingUser || !newUser.telegram_id || !newUser.first_name}
              >
                {creatingUser ? 'Создание...' : <><IconUserPlus size={14} /> Создать</>}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
