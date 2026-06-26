import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import { daysSinceLabel } from '../utils/date';
import { getScenarioIcon } from '../scenarioIcons';
import {
  IconChevronLeft,
  IconChevronDown,
  IconSend,
  IconDeviceFloppy,
  IconMessageCircle,
  IconAt,
  IconSpeakerphone,
  IconCornerUpLeft,
  IconX,
  IconMessage2,
} from '@tabler/icons-react';

function getInitials(firstName, lastName) {
  return `${(firstName || '?')[0]}${(lastName || '')[0] || ''}`.toUpperCase();
}

function formatCommentTime(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function autoGrow(e) {
  e.target.style.height = 'auto';
  e.target.style.height = e.target.scrollHeight + 'px';
}


export default function StepPage() {
  const navigate = useNavigate();
  const { objectId, stepNumber } = useParams();

  const [user, setUser] = useState(null);
  const [object, setObject] = useState(null);
  const [scenario, setScenario] = useState(null);
  const [loading, setLoading] = useState(true);
  const [savedAnswers, setSavedAnswers] = useState({});
  const [statusNotes, setStatusNotes] = useState([]);
  const [noteText, setNoteText] = useState('');
  const [postingNote, setPostingNote] = useState(false);
  const [notesOpen, setNotesOpen] = useState(true);
  const [adminOpen, setAdminOpen] = useState(true);
  const [discussOpen, setDiscussOpen] = useState(false);
  const [comments, setComments] = useState([]);
  const [commentText, setCommentText] = useState('');
  const [postingComment, setPostingComment] = useState(false);
  const [replyTo, setReplyTo] = useState(null); // { id, author, comment_text }
  const [highlightedId, setHighlightedId] = useState(null);
  const showLoadingText = useDelayedLoadingText(loading);
  const touchStartX = useRef(null);
  const touchStartY = useRef(null);
  const discussListRef = useRef(null);

  const scrollToComment = (id) => {
    const el = document.getElementById(`comment-${id}`);
    if (!el) return;
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setHighlightedId(id);
    setTimeout(() => setHighlightedId(null), 1500);
  };

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [obj, me] = await Promise.all([api.getObject(objectId), api.getMe()]);
      const scen = await api.getScenario(obj.scenario_id);
      setUser(me);
      setObject(obj);
      setScenario(scen);

      const saved = {};
      for (const a of obj.answers || []) {
        saved[a.step_id] = a;
      }
      setSavedAnswers(saved);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [objectId]);

  useEffect(() => { loadData(); }, [loadData]);

  const currentStepId = scenario
    ? [...scenario.steps].sort((a, b) => a.step_number - b.step_number)[
        Math.min(Math.max(1, Number(stepNumber)), scenario.steps.length) - 1
      ]?.id
    : null;

  useEffect(() => {
    if (!currentStepId) return;
    setCommentText('');
    setNoteText('');
    setReplyTo(null);
    api.getStatusNotes(objectId, currentStepId).then(setStatusNotes).catch(() => setStatusNotes([]));
    api.getStepComments(objectId, currentStepId).then(data => {
      setComments(data);
      if (data.length > 0) {
        setDiscussOpen(true);
        // скроллим к последнему сообщению после рендера
        setTimeout(() => {
          if (discussListRef.current) {
            discussListRef.current.scrollTop = discussListRef.current.scrollHeight;
          }
        }, 100);
      }
    }).catch(() => setComments([]));
  }, [objectId, currentStepId]);

  if (loading) return <div className="loading">{showLoadingText ? 'Загрузка...' : ''}</div>;
  if (!scenario) return <div className="error">Сценарий не найден</div>;

  const allSteps = [...scenario.steps].sort((a, b) => a.step_number - b.step_number);
  const totalSteps = allSteps.length;
  const currentIndex = Math.min(Math.max(1, Number(stepNumber)), totalSteps);
  const step = allSteps[currentIndex - 1];
  const answeredCount = allSteps.filter(s => savedAnswers[s.id]).length;
  const progressPct = totalSteps > 0 ? Math.round((answeredCount / totalSteps) * 100) : 0;
  const isLastStep = currentIndex >= totalSteps;

  // Ответственный = в списке workers объекта ИЛИ admin
  const isAdmin = user?.role === 'admin';
  const isResponsible = isAdmin || (object?.workers || []).some(w => w.user_id === user?.id);
  const savedRecord = savedAnswers[step.id];
  const adminComments = savedRecord?.comments || [];
  // Администратор листает шаги без ограничений; сотруднику нужно добавить хотя бы одну запись
  const canAdvance = !isResponsible || statusNotes.length > 0;

  async function postStatusNote() {
    const value = noteText.trim();
    if (!value) return;
    setPostingNote(true);
    try {
      const created = await api.addStatusNote(objectId, step.id, { note_text: value });
      setStatusNotes(prev => [...prev, created]);
      setNoteText('');
      // Refresh savedAnswers so locked state is up-to-date (ObjectAnswer auto-created on first note)
      if (statusNotes.length === 0) {
        const freshObj = await api.getObject(objectId);
        const newSaved = {};
        for (const a of freshObj.answers || []) newSaved[a.step_id] = a;
        setSavedAnswers(newSaved);
      }
    } catch (err) {
      alert(err.message);
    } finally {
      setPostingNote(false);
    }
  }

  async function postComment() {
    const value = commentText.trim();
    if (!value) return;

    setPostingComment(true);
    try {
      const created = await api.addStepComment(objectId, step.id, {
        comment_text: value,
        reply_to_id: replyTo?.id ?? null,
      });
      const updated = await api.getStepComments(objectId, currentStepId);
      setComments(updated);
      setCommentText('');
      setReplyTo(null);
      // скроллим к новому сообщению (оно стоит после родителя, не в конце)
      setTimeout(() => scrollToComment(created.id), 100);
    } catch (err) {
      alert(err.message);
    } finally {
      setPostingComment(false);
    }
  }

  function getSystemEventIcon(eventType) {
    if (eventType === 'admin_comment') return <IconMessage2 size={13} />;
    return <IconSpeakerphone size={13} />;
  }

  function goTo(index) {
    navigate(`/objects/${objectId}/steps/${index}`);
  }

  function goPrev() {
    if (currentIndex > 1) goTo(currentIndex - 1);
  }

  function goNext() {
    if (!canAdvance) return;
    if (isLastStep) {
      navigate('/');
    } else {
      goTo(currentIndex + 1);
    }
  }

  const { icon: ScenIcon, cls: scenIconCls } = getScenarioIcon(scenario?.name);

  function handleTouchStart(e) {
    touchStartX.current = e.touches[0].clientX;
    touchStartY.current = e.touches[0].clientY;
  }

  function handleTouchEnd(e) {
    if (touchStartX.current === null) return;
    const dx = e.changedTouches[0].clientX - touchStartX.current;
    const dy = e.changedTouches[0].clientY - touchStartY.current;
    touchStartX.current = null;
    touchStartY.current = null;
    // горизонтальный свайп, не вертикальный скролл
    if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy)) return;
    if (dx > 0) goPrev();
    else goNext();
  }

  return (
    <div className="page" onTouchStart={handleTouchStart} onTouchEnd={handleTouchEnd}>
      {/* Шапка */}
      <div className="qhdr">
        <div className="qhdr-top">
          <button className="btn-bk" onClick={() => navigate('/')}>
            <IconChevronLeft size={18} />
          </button>
          <div className={`ci qhdr-icon ${scenIconCls}`}>
            <ScenIcon size={16} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="qhdr-title">{object?.name}</div>
            <div className="qhdr-sub">
              {scenario?.name} · в работе {daysSinceLabel(object?.created_at)}
            </div>
          </div>
        </div>

        <div className="qprog-bar">
          <div className="qprog-fill" style={{ width: `${progressPct}%` }} />
        </div>
        <div className="qhdr-step">
          Шаг {currentIndex} из {totalSteps} · {progressPct}%
        </div>
      </div>

      {/* Вопрос */}
      <div className="sc" style={{ paddingTop: 8, paddingBottom: 16 }}>
        <div className="qcard">
          <div className="qtitle">{step.question_text}</div>

          {step.description && <div className="qhint">{step.description}</div>}

          {/* Блок 1: Комментарий к этапу — лог статусов, иммутабельный */}
          <div className="step-comment-section">
            <div className="step-comment-lbl collapse-toggle" onClick={() => setNotesOpen(o => !o)}>
              <IconDeviceFloppy size={13} />
              Комментарий к этапу
              {statusNotes.length > 0 && <span className="collapse-badge">{statusNotes.length}</span>}
              <IconChevronDown size={13} className={`collapse-chev${notesOpen ? ' open' : ''}`} />
            </div>

            {notesOpen && (
              <>
                {statusNotes.length > 0 && (
                  <div className="snotes-list">
                    {statusNotes.map(n => (
                      <div className="snote" key={n.id}>
                        <div className="snote-meta">
                          <span className="snote-author">
                            {n.author?.first_name} {n.author?.last_name || ''}
                          </span>
                          <span className="snote-time">{formatCommentTime(n.created_at)}</span>
                        </div>
                        <div className="snote-text">{n.note_text}</div>
                      </div>
                    ))}
                  </div>
                )}

                {statusNotes.length === 0 && !isResponsible && (
                  <div className="snotes-empty">Нет записей статуса</div>
                )}

                {isResponsible && (
                  <div className="discuss-inputwrap" style={{ marginTop: 6 }}>
                    <textarea
                      className="discuss-textarea"
                      placeholder="Обновить статус этапа..."
                      value={noteText}
                      onChange={e => setNoteText(e.target.value)}
                      onInput={autoGrow}
                      rows={1}
                    />
                    <button
                      className="discuss-send"
                      onClick={postStatusNote}
                      disabled={postingNote || !noteText.trim()}
                      aria-label="Добавить запись"
                    >
                      <IconSend size={16} />
                    </button>
                  </div>
                )}

              </>
            )}
          </div>
        </div>

        {/* Блок 2: Комментарии администратора (только если есть) */}
        {adminComments.length > 0 && (
          <div className="discuss-block">
            <div className="discuss-hdr collapse-toggle" style={!adminOpen ? { marginBottom: 0 } : undefined} onClick={() => setAdminOpen(o => !o)}>
              <IconSpeakerphone size={15} />
              Комментарий администратора
              <span className="collapse-badge" style={{ marginLeft: 4 }}>{adminComments.length}</span>
              <IconChevronDown size={13} className={`collapse-chev${adminOpen ? ' open' : ''}`} />
            </div>
            {adminOpen && (
              <div style={{ marginTop: 8 }}>
                {adminComments.map(c => (
                  <div className="admin-comment-item" key={c.id}>
                    <div className="admin-comment-text">{c.comment_text}</div>
                    <div className="admin-comment-time">{formatCommentTime(c.created_at)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Блок 3: Обсуждение шага */}
        <div className="discuss-block">
          <div className="discuss-hdr collapse-toggle" style={!discussOpen ? { marginBottom: 0 } : undefined} onClick={() => setDiscussOpen(o => !o)}>
            <IconMessageCircle size={16} />
            Обсуждение шага
            {comments.length > 0 && <span className="collapse-badge" style={{ marginLeft: 4 }}>{comments.length}</span>}
            <IconChevronDown size={13} className={`collapse-chev${discussOpen ? ' open' : ''}`} />
          </div>

          {discussOpen && (
            <>
              {comments.length > 0 && (
                <div className="discuss-list" ref={discussListRef}>
                  {comments.map(c => {
                    if (c.is_system_event) {
                      return (
                        <div className="discuss-event" key={c.id}>
                          {getSystemEventIcon(c.event_type)}
                          {c.comment_text}
                          <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--mu2)' }}>
                            {formatCommentTime(c.created_at)}
                          </span>
                        </div>
                      );
                    }
                    return (
                      <div
                        className={`discuss-msg${highlightedId === c.id ? ' discuss-msg--highlight' : ''}`}
                        key={c.id}
                        id={`comment-${c.id}`}
                      >
                        <div className="discuss-avatar">
                          {getInitials(c.author?.first_name, c.author?.last_name)}
                        </div>
                        <div className="discuss-body">
                          <div className="discuss-meta">
                            <span className="discuss-author">
                              {c.author?.first_name} {c.author?.last_name || ''}
                            </span>
                            {c.recipient && (
                              <span className="discuss-to">
                                <IconAt size={11} /> {c.recipient.first_name} {c.recipient.last_name || ''}
                              </span>
                            )}
                            <span className="discuss-time">{formatCommentTime(c.created_at)}</span>
                            <button
                              className="discuss-reply-btn"
                              onClick={() => setReplyTo(c)}
                              title="Ответить"
                            >
                              <IconCornerUpLeft size={13} />
                            </button>
                          </div>
                          {c.reply_to && (
                            <div
                              className="discuss-quoted"
                              onClick={() => scrollToComment(c.reply_to.id)}
                              title="Перейти к сообщению"
                            >
                              <span className="discuss-quoted-author">
                                {c.reply_to.is_system_event
                                  ? 'Система'
                                  : `${c.reply_to.author?.first_name || ''} ${c.reply_to.author?.last_name || ''}`.trim()}
                              </span>
                              {c.reply_to.comment_text}
                            </div>
                          )}
                          <div className="discuss-text">{c.comment_text}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              <div className="discuss-form">
                {replyTo && (
                  <div className="discuss-reply-bar">
                    <div className="discuss-reply-bar-content">
                      <span className="discuss-reply-bar-author">
                        {replyTo.is_system_event
                          ? 'Система'
                          : `${replyTo.author?.first_name || ''} ${replyTo.author?.last_name || ''}`.trim()}
                      </span>
                      {replyTo.comment_text}
                    </div>
                    <button className="discuss-reply-cancel" onClick={() => setReplyTo(null)}>
                      <IconX size={14} />
                    </button>
                  </div>
                )}
                <div className="discuss-inputwrap">
                  <textarea
                    className="discuss-textarea"
                    placeholder="Написать сообщение..."
                    value={commentText}
                    onChange={e => setCommentText(e.target.value)}
                    rows={1}
                  />
                  <button
                    className="discuss-send"
                    onClick={postComment}
                    disabled={postingComment || !commentText.trim()}
                    aria-label="Отправить"
                  >
                    <IconSend size={16} />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Навигация */}
      <div className="step-nav-mini">
        {isLastStep ? (
          <button className="btn-p green" onClick={goNext} disabled={!canAdvance} style={{ flex: 1 }}>
            <IconSend size={18} /> Отправить отчёт
          </button>
        ) : (
          <>
            <button
              className="step-nav-circle"
              onClick={goPrev}
              disabled={currentIndex <= 1}
            >
              ‹
            </button>
            <span className="step-nav-counter">{currentIndex} / {totalSteps}</span>
            <button
              className="step-nav-circle accent"
              onClick={goNext}
              disabled={!canAdvance}
            >
              ›
            </button>
          </>
        )}
      </div>
    </div>
  );
}
