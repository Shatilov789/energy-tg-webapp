import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';

export default function HomePage() {
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState([]);
  const [objects, setObjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [scenariosData, objectsData] = await Promise.all([
        api.getScenarios(),
        api.getMyObjects(),
      ]);
      setScenarios(scenariosData);
      setObjects(objectsData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function getProgress(obj) {
    // Will be calculated from answers count / total steps
    return { answered: 0, total: 0, percent: 0 };
  }

  if (loading) return <div className="loading">Loading...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="page home-page">
      <header className="header">
        <h1>Energy CRM</h1>
        <span className="badge">{objects.length} objects</span>
      </header>

      <section className="section">
        <h2>Select scenario</h2>
        <div className="scenario-grid">
          {scenarios.map((s) => (
            <button
              key={s.id}
              className="scenario-card"
              onClick={() => navigate(`/objects?scenario=${s.id}`)}
            >
              <span className="scenario-name">{s.name}</span>
            </button>
          ))}
        </div>
      </section>

      {objects.length > 0 && (
        <section className="section">
          <h2>Active objects</h2>
          <div className="object-list">
            {objects.map((obj) => {
              const progress = getProgress(obj);
              return (
                <button
                  key={obj.id}
                  className="object-card"
                  onClick={() => navigate(`/objects/${obj.id}/steps/1`)}
                >
                  <span className="object-name">{obj.name}</span>
                  <span className="object-progress">{progress.percent}%</span>
                </button>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
