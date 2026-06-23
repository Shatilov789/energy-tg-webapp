import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import { daysSinceLabel } from '../utils/date';
import { getScenarioIcon } from '../scenarioIcons';
import {
  IconChevronLeft,
  IconArrowLeft,
  IconArrowRight,
  IconSend,
  IconLock,
  IconDeviceFloppy,
  IconMessageCircle,
  IconAt,
  IconSpeakerphone,
} from '@tabler/icons-react';

function getInitials(firstName, lastName) {
  return `${(firstName || '?')[0]}${(lastName || '')[0] || ''}`.toUpperCase();
}

function formatCommentTime(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

export default function StepPage() {
  const navigate = useNavigate();
  const { objectId, stepNumber } = useParams();

  const [object, setObject] = useState(null);
  const [scenario, setScenario] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [answers, setAnswers] = useState({});
  const [savedAnswers, setSavedAnswers] = useState({});
  const [comments, setComments] = useState([]);
  const [commentText, setCommentText] = useState('');
  const [postingComment, setPostingComment] = useState(false);
  const showLoadingText = useDelayedLoadingText(loading);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const obj = await api.getObject(objectId);
      const scen = await api.getScenario(obj.scenario_id);
      setObject(obj);
      setScenario(scen);

      const ans = {};
      const saved = {};
      for (const a of obj.answers || []) {
        ans[a.step_id] = a.answer_text;
        saved[a.step_id] = a;
      }
      setAnswers(ans);
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
    api.getStepComments(objectId, currentStepId).then(setComments).catch(() => setComments([]));
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

  const saved = !!savedAnswers[step.id];
  const locked = !!savedAnswers[step.id]?.is_locked;
  const text = answers[step.id] || '';
  const savedRecord = savedAnswers[step.id];
  const adminComments = savedRecord?.comments || [];
  const dirty = saved ? text.trim() !== savedRecord.answer_text : text.trim().length > 0;
  const canAdvance = locked || (saved && !dirty);

  function setAnswer(text) {
    setAnswers(prev => ({ ...prev, [step.id]: text }));
  }

  async function saveAnswer() {
    const value = text.trim();
    if (!value) return;

    setSaving(true);
    try {
      if (saved) {
        await api.updateAnswer(objectId, step.id, { answer_text: value });
      } else {
        await api.submitAnswer(objectId, step.id, { answer_text: value });
      }

      const freshObj = await api.getObject(objectId);
      setObject(freshObj);
      const newSaved = {};
      for (const a of freshObj.answers || []) {
        newSaved[a.step_id] = a;
      }
      setSavedAnswers(newSaved);
    } catch (err) {
      alert(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function postComment() {
    const value = commentText.trim();
    if (!value) return;

    setPostingComment(true);
    try {
      const created = await api.addStepComment(objectId, step.id, {
        comment_text: value,
      });
      setComments(prev => [...prev, created]);
      setCommentText('');
    } catch (err) {
      alert(err.message);
    } finally {
      setPostingComment(false);
    }
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

  return (
    <div className="page">
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

          <textarea
            className={`qtextarea ${locked ? 'locked' : ''} ${saved && !dirty ? 'answered' : ''}`}
            placeholder="Введите ответ..."
            value={text}
            onChange={e => setAnswer(e.target.value)}
            rows={5}
            disabled={locked}
          />

          {adminComments.length > 0 && (
            <div className="admin-comment-box">
              <div className="admin-comment-hdr">
                <IconSpeakerphone size={14} />
                Комментарий администратора
              </div>
              {adminComments.map(c => (
                <div className="admin-comment-item" key={c.id}>
                  <div className="admin-comment-text">{c.comment_text}</div>
                  <div className="admin-comment-time">{formatCommentTime(c.created_at)}</div>
                </div>
              ))}
            </div>
          )}

          {locked && (
            <div className="lock-tag">
              <IconLock size={14} />
              Заблокировано — только администратор может разблокировать
            </div>
          )}

          {!locked && saved && !dirty && (
            <div className="saved-tag">
              <IconDeviceFloppy size={13} /> Сохранено
            </div>
          )}

          {!locked && dirty && (
            <button
              className="btn-p"
              style={{ marginTop: 12, height: 40, fontSize: 13, borderRadius: 12 }}
              onClick={saveAnswer}
              disabled={saving || !text.trim()}
            >
              {saving ? 'Сохранение...' : 'Сохранить ответ'}
            </button>
          )}
        </div>

        {/* Обсуждение шага */}
        <div className="discuss-block">
          <div className="discuss-hdr">
            <IconMessageCircle size={16} />
            Обсуждение шага {comments.length > 0 && `(${comments.length})`}
          </div>

          {comments.length > 0 && (
            <div className="discuss-list">
              {comments.map(c => (
                <div className="discuss-msg" key={c.id}>
                  <div className="discuss-avatar">{getInitials(c.author.first_name, c.author.last_name)}</div>
                  <div className="discuss-body">
                    <div className="discuss-meta">
                      <span className="discuss-author">{c.author.first_name} {c.author.last_name || ''}</span>
                      {c.recipient && (
                        <span className="discuss-to">
                          <IconAt size={11} /> {c.recipient.first_name} {c.recipient.last_name || ''}
                        </span>
                      )}
                      <span className="discuss-time">{formatCommentTime(c.created_at)}</span>
                    </div>
                    <div className="discuss-text">{c.comment_text}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="discuss-form">
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
        </div>
      </div>

      {/* Навигация */}
      <div className="step-nav">
        {currentIndex > 1 ? (
          <button className="btn-bk" onClick={goPrev}>
            <IconArrowLeft size={20} />
          </button>
        ) : (
          <div style={{ width: 44 }} />
        )}
        <button
          className={`btn-p ${isLastStep ? 'green' : ''}`}
          onClick={goNext}
          disabled={!canAdvance}
        >
          {isLastStep ? (
            <><IconSend size={18} /> Отправить отчёт</>
          ) : (
            <>Далее <IconArrowRight size={18} /></>
          )}
        </button>
      </div>
    </div>
  );
}
