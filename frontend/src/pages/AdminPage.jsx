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
  IconLockOpen,
  IconMessagePlus,
  IconChecks,
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
  const [commentModal, setCommentModal] = useState(null);
  const [commentText, setCommentText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    try {
      const [objs, usrs] = await Promise.all([
        api.getAdminObjects(),
        api.getAdminUsers(),
      ]);
      setObjects(objs);
      setUsers(usrs);

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

  async function handleUnlock(answerId) {
    try {
      await api.unlockAnswer(answerId);
      await loadData();
    } catch (err) {
      alert(err.message);
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
          <div className="tbar-s">Общий обзор инспекций</div>
        </div>
        <button className="ib" title="Экспорт">
          <IconDownload size={18} />
        </button>
      </div>

      <div className="sc">
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

          const lockedAnswers = (obj.answers || []).filter(a => a.is_locked);
          const firstLocked = lockedAnswers[0];
          const lockedStep = firstLocked && obj.scen
            ? obj.scen.steps.find(s => s.id === firstLocked.step_id)
            : null;

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

              {firstLocked && lockedStep && (
                <div className="adm-detail">
                  <div style={{ fontSize: 11, color: 'var(--mu)', marginBottom: 6 }}>
                    Вопрос №{lockedStep.step_number} — заблокирован:
                  </div>
                  <div className="adm-answer-box">
                    «{lockedStep.question_text}»
                    <br />
                    <span style={{ color: 'var(--mu)', fontSize: 11 }}>
                      Ответ: {firstLocked.answer_text}
                    </span>
                  </div>
                  <div className="adm-actions">
                    <button className="unlock-btn" onClick={() => handleUnlock(firstLocked.id)}>
                      <IconLockOpen size={13} /> Разблокировать
                    </button>
                    <button className="comment-btn" onClick={() => setCommentModal({ answerId: firstLocked.id, stepText: lockedStep.question_text })}>
                      <IconMessagePlus size={13} /> Комментарий
                    </button>
                  </div>
                </div>
              )}

              {!firstLocked && (
                <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                  <button className="comment-btn">
                    <IconMessagePlus size={13} /> Комментарий
                  </button>
                </div>
              )}
            </div>
          );
        })}

        <div style={{ height: 20 }} />
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
    </div>
  );
}
