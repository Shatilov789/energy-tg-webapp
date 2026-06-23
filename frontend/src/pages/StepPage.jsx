import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';
import {
  IconChevronLeft,
  IconArrowLeft,
  IconArrowRight,
  IconSend,
  IconLock,
  IconDeviceFloppy,
} from '@tabler/icons-react';

export default function StepPage() {
  const navigate = useNavigate();
  const { objectId, stepNumber } = useParams();

  const [object, setObject] = useState(null);
  const [scenario, setScenario] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [answers, setAnswers] = useState({});
  const [savedAnswers, setSavedAnswers] = useState({});

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

  if (loading) return <div className="loading">Загрузка...</div>;
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

  return (
    <div className="page">
      {/* Шапка */}
      <div className="qstep-hdr">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <button className="btn-bk" onClick={() => navigate('/')}>
            <IconChevronLeft size={18} />
          </button>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {object?.name}
            </div>
            <div style={{ fontSize: 12, color: 'var(--mu)' }}>
              {scenario?.name}
            </div>
          </div>
          <span className="bdg bdg-pend">
            Вопрос {currentIndex}/{totalSteps}
          </span>
        </div>

        {/* Pips — клик доступен только назад, по истории */}
        <div className="pips">
          {allSteps.map((s, i) => {
            const idx = i + 1;
            const isDone = !!savedAnswers[s.id];
            const isCurrent = idx === currentIndex;
            const canJump = idx <= currentIndex;
            return (
              <div
                key={s.id}
                className={`pip ${isDone ? 'done' : isCurrent ? 'cur' : 'empty'}`}
                style={{ width: isCurrent ? 20 : 8, cursor: canJump ? 'pointer' : 'default' }}
                onClick={() => canJump && goTo(idx)}
              />
            );
          })}
        </div>

        <div className="qprog">
          <div className="qprog-bar">
            <div className="qprog-fill" style={{ width: `${progressPct}%` }} />
          </div>
          <div className="qprog-lbl">{answeredCount} / {totalSteps} вопросов</div>
        </div>
      </div>

      {/* Вопрос */}
      <div className="sc" style={{ paddingTop: 16, paddingBottom: 16 }}>
        <div className={`qblock ${saved ? 'answered' : ''} ${locked ? 'locked' : ''}`}>
          <div className="qnum">
            <span className={`qnum-n ${locked ? 'locked' : saved ? 'answered' : ''}`}>
              {step.step_number}
            </span>
            <span className="qtitle">{step.question_text}</span>
          </div>

          {step.description && <div className="qhint">{step.description}</div>}

          <textarea
            className="qtextarea"
            placeholder="Введите ответ..."
            value={text}
            onChange={e => setAnswer(e.target.value)}
            rows={4}
            disabled={locked}
          />

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
              style={{ marginTop: 10, height: 36, fontSize: 12, borderRadius: 10 }}
              onClick={saveAnswer}
              disabled={saving || !text.trim()}
            >
              {saving ? 'Сохранение...' : 'Сохранить ответ'}
            </button>
          )}
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
