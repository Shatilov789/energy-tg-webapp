import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';

export default function StepPage() {
  const navigate = useNavigate();
  const { objectId, stepNumber } = useParams();

  const [object, setObject] = useState(null);
  const [scenario, setScenario] = useState(null);
  const [currentStep, setCurrentStep] = useState(null);
  const [answer, setAnswer] = useState('');
  const [existingAnswer, setExistingAnswer] = useState(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStep();
  }, [objectId, stepNumber]);

  async function loadStep() {
    setLoading(true);
    try {
      const obj = await api.getObject(objectId);
      setObject(obj);

      const scenarioData = await api.getScenario(obj.scenario_id);
      setScenario(scenarioData);

      const step = scenarioData.steps.find((s) => s.step_number === Number(stepNumber));
      setCurrentStep(step);

      const existing = obj.answers?.find((a) => a.step_id === step?.id);
      if (existing) {
        setExistingAnswer(existing);
        setAnswer(existing.answer_text);
      } else {
        setExistingAnswer(null);
        setAnswer('');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    if (!answer.trim() || !currentStep) return;
    setSaving(true);
    try {
      if (existingAnswer && !existingAnswer.is_locked) {
        await api.updateAnswer(objectId, currentStep.id, { answer_text: answer.trim() });
      } else if (!existingAnswer) {
        await api.submitAnswer(objectId, currentStep.id, { answer_text: answer.trim() });
      }
      goNext();
    } catch (err) {
      alert(err.message);
    } finally {
      setSaving(false);
    }
  }

  function goNext() {
    const nextStep = Number(stepNumber) + 1;
    const maxStep = scenario?.steps?.length || 0;
    if (nextStep <= maxStep) {
      navigate(`/objects/${objectId}/steps/${nextStep}`);
    } else {
      navigate(`/objects/${objectId}/history`);
    }
  }

  function goPrev() {
    const prev = Number(stepNumber) - 1;
    if (prev >= 1) {
      navigate(`/objects/${objectId}/steps/${prev}`);
    }
  }

  if (loading) return <div className="loading">Loading...</div>;
  if (!currentStep) return <div className="error">Step not found</div>;

  const totalSteps = scenario?.steps?.length || 0;
  const answeredCount = object?.answers?.length || 0;
  const isLocked = existingAnswer?.is_locked;

  return (
    <div className="page step-page">
      <header className="header">
        <button className="back-btn" onClick={() => navigate('/')}>←</button>
        <h1>Step {stepNumber} · {object?.name}</h1>
      </header>

      <div className="progress-bar">
        <span className="progress-label">
          Question {stepNumber} of {totalSteps}
        </span>
        <span className="progress-label">
          {answeredCount} / {totalSteps} steps
        </span>
      </div>

      <div className="step-content">
        <p className="question">{currentStep.question_text}</p>

        {currentStep.description && (
          <p className="description">{currentStep.description}</p>
        )}

        <textarea
          className="input textarea answer-input"
          placeholder="Your answer..."
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          disabled={isLocked}
          rows={4}
        />

        {isLocked && (
          <p className="locked-notice">Read-only — request admin unlock to edit</p>
        )}
      </div>

      <div className="step-actions">
        {Number(stepNumber) > 1 && (
          <button className="nav-btn" onClick={goPrev}>← Previous</button>
        )}

        <button
          className="submit-btn"
          onClick={handleSave}
          disabled={saving || isLocked || !answer.trim()}
        >
          {saving ? 'Saving...' : existingAnswer ? 'Next →' : 'Save & Next →'}
        </button>
      </div>

      <p className="autosave-hint">Auto-saved</p>
    </div>
  );
}
