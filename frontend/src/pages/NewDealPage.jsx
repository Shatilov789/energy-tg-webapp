import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import { IconChevronLeft, IconCircleCheck, IconGitBranch } from '@tabler/icons-react';
import { PROCESSES } from '../processes';

export default function NewDealPage() {
  const navigate = useNavigate();
  const [processType, setProcessType] = useState('СЕС');
  const [stages, setStages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [clientName, setClientName] = useState('');
  const [clientPhone, setClientPhone] = useState('');
  const showLoadingText = useDelayedLoadingText(loading);

  useEffect(() => { loadData(processType); }, [processType]);

  async function loadData(procType) {
    setLoading(true);
    try {
      setStages(await api.getStages(procType));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!clientName.trim() || !clientPhone.trim()) return;
    setCreating(true);
    try {
      const deal = await api.createDeal({
        process_type: processType,
        client_name: clientName.trim(),
        client_phone: clientPhone.trim(),
      });
      navigate(`/deals/${deal.id}`);
    } catch (err) {
      alert(err.message);
    } finally {
      setCreating(false);
    }
  }

  if (loading) return <div className="loading">{showLoadingText ? 'Завантаження...' : ''}</div>;

  return (
    <div className="page">
      <div className="tbar">
        <button className="btn-bk" onClick={() => navigate('/')}>
          <IconChevronLeft size={20} />
        </button>
        <div style={{ fontSize: 18, fontWeight: 700 }}>Нова угода</div>
      </div>

      <div className="sc" style={{ paddingBottom: 32 }}>
        <div className="fgrp" style={{ marginTop: 4 }}>
          <label className="flbl">Процес</label>
          {PROCESSES.map(p => {
            const Icon = p.icon;
            const selected = processType === p.key;
            return (
              <div
                key={p.key}
                className={`scen-card${selected ? ' sel' : ''}`}
                style={{ padding: '10px 14px', marginBottom: 6, cursor: 'pointer' }}
                onClick={() => setProcessType(p.key)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Icon size={18} color="var(--acc)" />
                  <span style={{ fontWeight: 600 }}>{p.label}</span>
                  <span style={{ fontSize: 12, color: 'var(--mu2)' }}>— {p.hint}</span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="fgrp">
          <label className="flbl">Імʼя клієнта</label>
          <input
            className="finp"
            type="text"
            placeholder="Імʼя клієнта"
            value={clientName}
            onChange={e => setClientName(e.target.value)}
          />
        </div>
        <div className="fgrp">
          <label className="flbl">Телефон</label>
          <input
            className="finp"
            type="text"
            placeholder="Телефон"
            value={clientPhone}
            onChange={e => setClientPhone(e.target.value)}
          />
        </div>
        <button
          className="btn-p"
          onClick={handleCreate}
          disabled={creating || !clientName.trim() || !clientPhone.trim()}
          style={{ marginBottom: 24 }}
        >
          <IconCircleCheck size={18} />
          {creating ? 'Створення...' : 'Створити угоду'}
        </button>

        <div className="flbl" style={{ marginBottom: 8 }}>
          Довідник етапів ({stages.length})
        </div>
        {stages.map(s => (
          <div key={s.id} className="scen-card" style={{ marginBottom: 6, padding: '8px 12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {s.is_decision && <IconGitBranch size={14} color="var(--acc)" />}
              <span style={{ fontSize: 12, color: 'var(--mu)', minWidth: 28 }}>{s.display_code}</span>
              <span style={{ flex: 1, fontSize: 13 }}>{s.name}</span>
              <span style={{ fontSize: 11, color: 'var(--mu2)' }}>{s.role_owner}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
