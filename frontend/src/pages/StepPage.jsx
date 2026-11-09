import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { IconChevronLeft } from '@tabler/icons-react';
import { api } from '../api/client';
import AdminCommentsSection from '../components/step/AdminCommentsSection';
import DiscussionSection from '../components/step/DiscussionSection';
import StatusNotesSection from '../components/step/StatusNotesSection';
import StepNav from '../components/step/StepNav';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import { useHorizontalSwipe } from '../hooks/useHorizontalSwipe';
import { getScenarioIcon } from '../scenarioIcons';
import { daysSinceLabel } from '../utils/date';

function indexAnswersByStep(object) {
  const byStep = {};
  for (const answer of object.answers || []) byStep[answer.step_id] = answer;
  return byStep;
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
  const showLoadingText = useDelayedLoadingText(loading);
  const bindSwipe = useHorizontalSwipe();

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [obj, me] = await Promise.all([api.getObject(objectId), api.getMe()]);
      const scen = await api.getScenario(obj.scenario_id);
      setUser(me);
      setObject(obj);
      setScenario(scen);
      setSavedAnswers(indexAnswersByStep(obj));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [objectId]);

  useEffect(() => { loadData(); }, [loadData]);

  const allSteps = scenario ? [...scenario.steps].sort((a, b) => a.step_number - b.step_number) : [];
  const totalSteps = allSteps.length;
  const currentIndex = Math.min(Math.max(1, Number(stepNumber)), totalSteps);
  const step = allSteps[currentIndex - 1];
  const stepId = step?.id;

  useEffect(() => {
    if (!stepId) return;
    api.getStatusNotes(objectId, stepId).then(setStatusNotes).catch(() => setStatusNotes([]));
  }, [objectId, stepId]);

  if (loading) return <div className="loading">{showLoadingText ? 'Завантаження...' : ''}</div>;
  if (!scenario) return <div className="error">Сценарій не знайдено</div>;

  const answeredCount = allSteps.filter(s => savedAnswers[s.id]).length;
  const progressPct = totalSteps > 0 ? Math.round((answeredCount / totalSteps) * 100) : 0;
  const isLastStep = currentIndex >= totalSteps;

  const isResponsible = user?.role === 'admin' || (object?.workers || []).some(w => w.user_id === user?.id);
  const adminComments = savedAnswers[step.id]?.comments || [];
  // A responsible worker must leave at least one status note before moving on.
  const canAdvance = !isResponsible || statusNotes.length > 0;

  async function postStatusNote(noteText) {
    const created = await api.addStatusNote(objectId, step.id, { note_text: noteText });
    setStatusNotes(prev => [...prev, created]);
    // The first note auto-creates the ObjectAnswer, so saved answers must be refreshed.
    if (statusNotes.length === 0) {
      setSavedAnswers(indexAnswersByStep(await api.getObject(objectId)));
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
    if (isLastStep) navigate('/');
    else goTo(currentIndex + 1);
  }

  const { icon: ScenIcon, cls: scenIconCls } = getScenarioIcon(scenario?.name);

  return (
    <div className="page" {...bindSwipe(goPrev, goNext)}>
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
              {scenario?.name} · в роботі {daysSinceLabel(object?.created_at)}
            </div>
          </div>
        </div>

        <div className="qprog-bar">
          <div className="qprog-fill" style={{ width: `${progressPct}%` }} />
        </div>
        <div className="qhdr-step">
          Крок {currentIndex} з {totalSteps} · {progressPct}%
        </div>
      </div>

      <div className="sc" style={{ paddingTop: 8, paddingBottom: 16 }}>
        <div className="qcard">
          <div className="qtitle">{step.question_text}</div>
          {step.description && <div className="qhint">{step.description}</div>}
          <StatusNotesSection stepId={step.id} notes={statusNotes} canPost={isResponsible} onPost={postStatusNote} />
        </div>

        <AdminCommentsSection comments={adminComments} />
        <DiscussionSection objectId={objectId} stepId={step.id} />
      </div>

      <StepNav
        currentIndex={currentIndex}
        totalSteps={totalSteps}
        canAdvance={canAdvance}
        onPrev={goPrev}
        onNext={goNext}
      />
    </div>
  );
}
