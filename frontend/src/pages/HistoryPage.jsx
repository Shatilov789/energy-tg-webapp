import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';

export default function HistoryPage() {
  const navigate = useNavigate();
  const { objectId } = useParams();
  const [object, setObject] = useState(null);
  const [scenario, setScenario] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
  }, [objectId]);

  async function loadHistory() {
    try {
      const obj = await api.getObject(objectId);
      setObject(obj);
      const scenarioData = await api.getScenario(obj.scenario_id);
      setScenario(scenarioData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="loading">Loading...</div>;
  if (!object) return <div className="error">Object not found</div>;

  const answeredSteps = object.answers || [];
  const totalSteps = scenario?.steps?.length || 0;
  const percent = totalSteps > 0 ? Math.round((answeredSteps.length / totalSteps) * 100) : 0;

  return (
    <div className="page history-page">
      <header className="header">
        <button className="back-btn" onClick={() => navigate('/')}>←</button>
        <h1>History · {object.name}</h1>
      </header>

      <div className="object-summary">
        <p><strong>Status:</strong> {object.status}</p>
        <p><strong>Progress:</strong> {answeredSteps.length} / {totalSteps} ({percent}%)</p>
        <p><strong>Created:</strong> {new Date(object.created_at).toLocaleDateString('ru-RU')}</p>
      </div>

      <div className="history-list">
        <h2>Action log</h2>
        {answeredSteps
          .sort((a, b) => new Date(b.answered_at) - new Date(a.answered_at))
          .map((ans) => {
            const step = scenario?.steps?.find((s) => s.id === ans.step_id);
            return (
              <div key={ans.id} className="history-item">
                <span className="history-date">
                  {new Date(ans.answered_at).toLocaleString('ru-RU')}
                </span>
                <span className="history-text">
                  Step {step?.step_number} — {step?.question_text} — filled
                </span>
              </div>
            );
          })}
      </div>

      {answeredSteps.length < totalSteps && (
        <button
          className="submit-btn"
          onClick={() => navigate(`/objects/${objectId}/steps/${answeredSteps.length + 1}`)}
        >
          Continue filling →
        </button>
      )}
    </div>
  );
}
