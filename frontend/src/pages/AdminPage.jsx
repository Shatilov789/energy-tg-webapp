import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import { daysSinceLabel } from '../utils/date';
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
  const [scenarios, setScenarios] = useState(adminCache?.scenarios ?? {});
  const [loading, setLoading] = useState(!adminCache);
  const [error, setError] = useState(null);
  const showLoadingText = useDelayedLoadingText(loading);
  const [tab, setTab] = useState('objects'); // 'objects' | 'users'
  const [commentModal, setCommentModal] = useState(null);
  const [commentText, setCommentText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [workerModal, setWorkerModal] = useState(null); // { objectId, currentWorkerIds }
  const [selectedUserId, setSelectedUserId] = useState('');
  const [userModal, setUserModal] = useState(false);
  const [newUser, setNewUser] = useState({ telegram_id: '', first_name: '', last_name: '', username: '', role: 'worker' });
  const [creatingUser, setCreatingUser] = useState(false);
  const [me, setMe] = useState(null);

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

      const scenMap = {};
      const scenIds = [...new Set(objs.map(o => o.scenario_id))];
      for (const sid of scenIds) {
        try {
          scenMap[sid] = await api.getScenario(sid);
        } catch {}
      }
      setScenarios(scenMap);
      adminCache = { objects: objs, users: usrs, scenarios: scenMap };
    } catch (err) {
      if (!adminCache) setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleLock(answerId) {
    try {
      await api.lockAnswer(answerId);
      await loadData();
    } catch (err) {
      alert(err.message);
    }
  }

  async function handleUnlock(answerId) {
    try {
      await api.unlockAnswer(answerId);
      await loadData();
    } catch (err) {
      alert(err.message);
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

  const totalObjects = objects.length;
  const completedObjects = objects.filter(o => o.status === 'completed').length;
  const inProgressObjects = totalObjects - completedObjects;

  let totalAnswered = 0;
  let totalQuestions = 0;
  const objectDetails = objects.map(obj => {
    const scen = scenarios[obj.scenario_id];
    const stepsCount = scen?.steps?.length || 0;
    const answersCount = obj.answers?.length || 0;
    totalAnswered += answersCount;
    totalQuestions += stepsCount;
    const pct = stepsCount > 0 ? Math.round((answersCount / stepsCount) * 100) : 0;
    const creator = userMap[obj.created_by_id];
    return { ...obj, scen, stepsCount, answersCount, pct, creator };
  });

  const overallPct = totalQuestions > 0 ? Math.round((totalAnswered / totalQuestions) * 100) : 0;
  const overdueCount = objectDetails.filter(o => o.pct === 0 && o.status !== 'completed').length;

  const needsAttention = objectDetails.filter(o => o.status !== 'completed').sort((a, b) => a.pct - b.pct);

  const metrics = [
    { label: 'Выполнено', value: `${overallPct}%`, sub: 'средний прогресс', color: 'var(--acc)' },
    { label: 'Объектов', value: inProgressObjects, sub: 'в работе', color: 'var(--acc2)' },
    { label: 'Просрочено', value: overdueCount, sub: 'требуют внимания', color: 'var(--err)' },
    { label: 'Завершено', value: completedObjects, sub: 'инспекций', color: 'var(--ok)' },
  ];

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
          <IconChartBar size={15} /> Объекты
        </button>
        <button className={`adm-tab${tab === 'users' ? ' on' : ''}`} onClick={() => setTab('users')}>
          <IconUsers size={15} /> Пользователи
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

        {/* Objects list */}
        <div className="slbl">Все объекты</div>

        {needsAttention.length === 0 && (
          <div className="empty-state">
            <IconChecks size={40} />
            Все объекты завершены
          </div>
        )}

        {needsAttention.map((obj, idx) => {
          const initials = obj.creator ? getInitials(obj.creator.first_name, obj.creator.last_name) : '??';
          const avaColor = AVA_COLORS[idx % AVA_COLORS.length];
          const creatorName = obj.creator
            ? `${obj.creator.first_name || ''} ${(obj.creator.last_name || '').charAt(0)}.`.trim()
            : 'Неизвестно';

          let badgeCls = 'bdg-pend';
          let badgeText = `${obj.pct}%`;
          if (obj.pct === 0) { badgeCls = 'bdg-err'; badgeText = 'Просрочен'; }
          if (obj.pct === 100) { badgeCls = 'bdg-ok'; badgeText = '100%'; }

          const answeredItems = (obj.answers || []).map(a => ({
            answer: a,
            step: obj.scen?.steps?.find(s => s.id === a.step_id),
          })).filter(x => x.step);

          return (
            <div className="adm-obj" key={obj.id}>
              <div className="adm-row">
                <div className={`ava ${avaColor}`}>{initials}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {obj.name}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--mu)' }}>
                    {creatorName} · {obj.answersCount}/{obj.stepsCount} вопр. · {daysSinceLabel(obj.created_at)}
                  </div>
                </div>
                <span className={`bdg ${badgeCls}`}>{badgeText}</span>
              </div>

              <div className="obj-progress-bar" style={{ marginTop: 0 }}>
                <div className="obj-progress-fill" style={{
                  width: `${obj.pct}%`,
                  background: obj.pct === 100 ? 'var(--ok)' : obj.pct === 0 ? 'var(--err)' : 'var(--acc)',
                }} />
              </div>

              {/* Ответственные за объект */}
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

              {answeredItems.map(({ answer, step }) => (
                <div className="adm-detail" key={answer.id}>
                  <div style={{ fontSize: 11, color: 'var(--mu)', marginBottom: 6 }}>
                    Вопрос №{step.step_number}{answer.is_locked ? ' — заблокирован' : ''}:
                  </div>
                  <div className="adm-answer-box">
                    «{step.question_text}»
                    <br />
                    <span style={{ color: 'var(--mu)', fontSize: 11 }}>
                      Ответ: {answer.answer_text}
                    </span>
                  </div>
                  <div className="adm-actions">
                    {answer.is_locked ? (
                      <button className="unlock-btn" onClick={() => handleUnlock(answer.id)}>
                        <IconLockOpen size={13} /> Разблокировать
                      </button>
                    ) : (
                      <button className="unlock-btn" onClick={() => handleLock(answer.id)}>
                        <IconLock size={13} /> Заблокировать
                      </button>
                    )}
                    <button className="comment-btn" onClick={() => setCommentModal({ answerId: answer.id, stepText: step.question_text })}>
                      <IconMessagePlus size={13} /> Комментарий
                    </button>
                  </div>
                </div>
              ))}
            </div>
          );
        })}

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
