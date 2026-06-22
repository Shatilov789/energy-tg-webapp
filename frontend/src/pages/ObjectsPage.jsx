import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../api/client';

export default function ObjectsPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const scenarioId = searchParams.get('scenario');

  const [objects, setObjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newComment, setNewComment] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadObjects();
  }, []);

  async function loadObjects() {
    try {
      const data = await api.getMyObjects();
      const filtered = scenarioId
        ? data.filter((o) => o.scenario_id === Number(scenarioId))
        : data;
      setObjects(filtered);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!newName.trim() || !scenarioId) return;
    setCreating(true);
    try {
      const obj = await api.createObject({
        name: newName.trim(),
        comment: newComment.trim() || null,
        scenario_id: Number(scenarioId),
      });
      navigate(`/objects/${obj.id}/steps/1`);
    } catch (err) {
      alert(err.message);
    } finally {
      setCreating(false);
    }
  }

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="page objects-page">
      <header className="header">
        <button className="back-btn" onClick={() => navigate('/')}>←</button>
        <h1>My objects</h1>
      </header>

      <div className="object-list">
        {objects.map((obj) => (
          <button
            key={obj.id}
            className="object-card"
            onClick={() => navigate(`/objects/${obj.id}/steps/1`)}
          >
            <div className="object-info">
              <span className="object-name">{obj.name}</span>
              <span className="object-status">{obj.status}</span>
            </div>
          </button>
        ))}
      </div>

      {scenarioId && (
        <>
          <button className="create-btn" onClick={() => setShowCreate(!showCreate)}>
            + Create new object
          </button>

          {showCreate && (
            <div className="create-form">
              <input
                type="text"
                placeholder="Object name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="input"
              />
              <textarea
                placeholder="Comment (optional)"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                className="input textarea"
              />
              <button
                className="submit-btn"
                onClick={handleCreate}
                disabled={creating || !newName.trim()}
              >
                {creating ? 'Creating...' : 'Create'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
