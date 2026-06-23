import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';
import {
  IconChevronLeft,
  IconArrowLeft,
  IconArrowRight,
  IconSend,
  IconCheck,
  IconLock,
  IconDeviceFloppy,
} from '@tabler/icons-react';

const PER_PAGE = 5;

export default function StepPage() {
  const navigate = useNavigate();
  const { objectId, stepNumber } = useParams();

  const [object, setObject] = useState(null);
  const [scenario, setScenario] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState({});
  const [answers, setAnswers] = useState({});
  const [savedAnswers, setSavedAnswers] = useState({});

  const page = Math.max(1, Math.ceil(Number(stepNumber) / PER_PAGE));

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
  const totalPages = Math.ceil(totalSteps / PER_PAGE);
  const pageSteps = allSteps.slice((page - 1) * PER_PAGE, page * PER_PAGE);
  const answeredCount = allSteps.filter(s => savedAnswers[s.id]).length;
  const progressPct = totalSteps > 0 ? Math.round((answeredCount / totalSteps) * 100) : 0;

  function setAnswer(stepId, text) {
    setAnswers(prev => ({ ...prev, [stepId]: text }));
  }

  async function saveAnswer(step) {
    const text = (answers[step.id] || '').trim();
    if (!text) return;

    setSaving(prev => ({ ...prev, [step.id]: true }));
    try {
      const existing = savedAnswers[step.id];
      if (existing && !existing.is_locked) {
        await api.updateAnswer(objectId, step.id, { answer_text: text });
      } else if (!existing) {
        await api.submitAnswer(objectId, step.id, { answer_text: text });
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
      setSaving(prev => ({ ...prev, [step.id]: false }));
    }
  }

  async function saveAllAndNext() {
    for (const step of pageSteps) {
      const text = (answers[step.id] || '').trim();
      const existing = savedAnswers[step.id];
      if (text && !existing) {
        await saveAnswer(step);
      } else if (text && existing && !existing.is_locked && text !== existing.answer_text) {
        await saveAnswer(step);
      }
    }
    if (page < totalPages) {
      const nextStep = page * PER_PAGE + 1;
      navigate(`/objects/${objectId}/steps/${nextStep}`);
    } else {
      navigate('/');
    }
  }

  function goPrev() {
    if (page > 1) {
      const prevStep = (page - 2) * PER_PAGE + 1;
      navigate(`/objects/${objectId}/steps/${prevStep}`);
    }
  }

  function isStepSaved(stepId) { return !!savedAnswers[stepId]; }

  function isStepDirty(step) {
    const text = (answers[step.id] || '').trim();
    const saved = savedAnswers[step.id];
    if (!saved && text) return true;
    if (saved && text !== saved.answer_text) return true;
    return false;
  }

  function isStepLocked(stepId) { return savedAnswers[stepId]?.is_locked; }

  const isLastPage = page >= totalPages;

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
            Этап {page}/{totalPages}
          </span>
        </div>

        {/* Step pips */}
        <div className="pips">
          {Array.from({ length: totalPages }, (_, i) => {
            const slice = allSteps.slice(i * PER_PAGE, (i + 1) * PER_PAGE);
            const allDone = slice.every(s => isStepSaved(s.id));
            const isCurrent = i + 1 === page;
            return (
              <div
                key={i}
                className={`pip ${allDone ? 'done' : isCurrent ? 'cur' : 'empty'}`}
                style={{ width: isCurrent ? 20 : 8 }}
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

      {/* Вопросы */}
      <div className="sc" style={{ paddingTop: 16, paddingBottom: 16 }}>
        {pageSteps.map(step => {
          const saved = isStepSaved(step.id);
          const locked = isStepLocked(step.id);
          const dirty = isStepDirty(step);
          const isSaving = saving[step.id];

          return (
            <div key={step.id} className={`qblock ${saved ? 'answered' : ''} ${locked ? 'locked' : ''}`}>
              <div className="qnum">
                <span className={`qnum-n ${locked ? 'locked' : saved ? 'answered' : ''}`}>
                  {step.step_number}
                </span>
                <span className="qtitle">{step.question_text}</span>
              </div>

              {step.description && <div className="qhint">{step.description}</div>}

              {locked ? (
                <div className="lock-tag">
                  <IconLock size={14} />
                  Заблокировано — только администратор может разблокировать
                </div>
              ) : (
                <>
                  <textarea
                    className="qtextarea"
                    placeholder="Введите ответ..."
                    value={answers[step.id] || ''}
                    onChange={e => setAnswer(step.id, e.target.value)}
                    rows={3}
                  />

                  {saved && !dirty && (
                    <div className="saved-tag">
                      <IconDeviceFloppy size={13} /> Сохранено
                    </div>
                  )}

                  {dirty && (
                    <button
                      className="btn-p"
                      style={{ marginTop: 10, height: 36, fontSize: 12, borderRadius: 10 }}
                      onClick={() => saveAnswer(step)}
                      disabled={isSaving || !(answers[step.id] || '').trim()}
                    >
                      {isSaving ? 'Сохранение...' : 'Сохранить ответ'}
                    </button>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>

      {/* Навигация */}
      <div className="step-nav">
        {page > 1 ? (
          <button className="btn-bk" onClick={goPrev}>
            <IconArrowLeft size={20} />
          </button>
        ) : (
          <div style={{ width: 44 }} />
        )}
        <button
          className={`btn-p ${isLastPage ? 'green' : ''}`}
          onClick={saveAllAndNext}
        >
          {isLastPage ? (
            <><IconSend size={18} /> Отправить отчёт</>
          ) : (
            <>Далее</>
          )}
        </button>
      </div>
    </div>
  );
}
