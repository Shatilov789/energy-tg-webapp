import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import {
  IconArrowLeft,
  IconArrowRight,
  IconCheck,
} from '@tabler/icons-react';

export default function HistoryPage() {
  const navigate = useNavigate();
  const { objectId } = useParams();
  const [object, setObject] = useState(null);
  const [scenario, setScenario] = useState(null);
  const [loading, setLoading] = useState(true);
  const showLoadingText = useDelayedLoadingText(loading);

  useEffect(() => { loadHistory(); }, [objectId]);

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

  if (loading) return <div className="loading">{showLoadingText ? 'Загрузка...' : ''}</div>;
  if (!object) return <div className="error">Объект не найден</div>;

  const answeredSteps = object.answers || [];
  const totalSteps = scenario?.steps?.length || 0;
  const pct = totalSteps > 0 ? Math.round((answeredSteps.length / totalSteps) * 100) : 0;

  return (
    <div className="page">
      <div className="tbar">
        <button className="btn-bk" onClick={() => navigate('/')}>
          <IconArrowLeft size={18} />
        </button>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: 16 }}>История</h1>
          <div className="tbar-s">{object.name}</div>
        </div>
      </div>

      <div className="sc">
        <div className="card" style={{ cursor: 'default' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: 13, color: 'var(--mu)' }}>Прогресс</span>
            <span className={`bdg ${pct >= 100 ? 'bdg-ok' : 'bdg-pend'}`}>{pct}%</span>
          </div>
          <div className="obj-progress-bar">
            <div className="obj-progress-fill" style={{ width: `${pct}%`, background: pct >= 100 ? 'var(--ok)' : 'var(--acc)' }} />
          </div>
          <div style={{ fontSize: 12, color: 'var(--mu)', marginTop: 8 }}>
            {answeredSteps.length} из {totalSteps} вопросов · Создан {new Date(object.created_at).toLocaleDateString('ru-RU')}
          </div>
        </div>

        <div className="slbl">Журнал ответов</div>

        {answeredSteps
          .sort((a, b) => new Date(b.answered_at) - new Date(a.answered_at))
          .map(ans => {
            const step = scenario?.steps?.find(s => s.id === ans.step_id);
            return (
              <div key={ans.id} className="notif-item">
                <div className="ni-icon" style={{ background: 'rgba(46,204,113,.12)', color: 'var(--ok)' }}>
                  <IconCheck size={18} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="ni-t">Вопрос {step?.step_number}</div>
                  <div className="ni-tx">{step?.question_text}</div>
                  <div className="ni-time">{new Date(ans.answered_at).toLocaleString('ru-RU')}</div>
                </div>
              </div>
            );
          })}

        {answeredSteps.length < totalSteps && (
          <button
            className="btn-p"
            style={{ marginTop: 12 }}
            onClick={() => navigate(`/objects/${objectId}/steps/${answeredSteps.length + 1}`)}
          >
            Продолжить заполнение <IconArrowRight size={18} />
          </button>
        )}
      </div>
    </div>
  );
}
