import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useDelayedLoadingText } from '../hooks/useDelayedLoadingText';
import { useHorizontalSwipe } from '../hooks/useHorizontalSwipe';
import { DEAL_STATUS_LABELS, STAGE_STATUS_LABELS } from '../processes';
import { IconChevronLeft, IconCheck, IconX, IconSend, IconGitBranch, IconClock } from '@tabler/icons-react';

export default function DealPage() {
  const { dealId } = useParams();
  const navigate = useNavigate();
  const [deal, setDeal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewIndex, setViewIndex] = useState(0);
  const [draft, setDraft] = useState({});
  const [saving, setSaving] = useState(false);
  // Keeps "Далі" disabled briefly after a move, so a double tap cannot complete the next stage too.
  const [cooldown, setCooldown] = useState(false);
  const [highlightId, setHighlightId] = useState(null);
  // Set synchronously: blocks a second click that arrives before React re-renders the disabled button.
  const advancingRef = useRef(false);
  const cooldownTimer = useRef(null);
  const showLoadingText = useDelayedLoadingText(loading);
  const bindSwipe = useHorizontalSwipe();

  useEffect(() => { loadData(); }, [dealId]);
  useEffect(() => () => clearTimeout(cooldownTimer.current), []);

  // Loads the deal and opens its latest stage. The draft survives only if that stage is the one
  // the draft was typed for (keepDraftFor = its progress id).
  async function loadData(keepDraftFor) {
    try {
      const dealData = await api.getDeal(dealId);
      const latest = dealData.history[dealData.history.length - 1];
      setDeal(dealData);
      setViewIndex(Math.max(0, dealData.history.length - 1));
      if (keepDraftFor === undefined || latest?.id !== keepDraftFor) {
        setDraft({});
      }
      return latest;
    } catch (err) {
      console.error(err);
      return null;
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="loading">{showLoadingText ? 'Завантаження...' : ''}</div>;
  if (!deal) return <div className="error">Угоду не знайдено</div>;

  const history = deal.history;
  const totalVisits = history.length;
  const visit = history[Math.min(viewIndex, totalVisits - 1)];
  const isActive = visit?.status === 'in_progress';
  const isDealActive = deal.status === 'active';

  function goTo(i) {
    if (i < 0 || i >= totalVisits) return;
    setViewIndex(i);
    setDraft({});
  }
  function goPrev() { goTo(viewIndex - 1); }
  function goNext() { goTo(viewIndex + 1); }

  async function handleAdvance() {
    if (visit.is_decision && draft.decision === undefined) {
      alert(`Оберіть: ${visit.yes_label || 'Так'} / ${visit.no_label || 'Ні'}`);
      return;
    }
    if (advancingRef.current) return;
    advancingRef.current = true;
    setSaving(true);
    try {
      await api.advanceDeal(dealId, {
        progress_id: visit.id,
        decision: draft.decision ?? null,
        comment: (draft.comment || '').trim() || null,
      });
      const latest = await loadData();
      setHighlightId(latest?.id ?? null);
      setCooldown(true);
      clearTimeout(cooldownTimer.current);
      cooldownTimer.current = setTimeout(() => setCooldown(false), 1000);
    } catch (err) {
      // E.g. the stage was already completed in another tab: explain, then show where the deal is now.
      alert(err.message);
      await loadData(visit.id);
    } finally {
      advancingRef.current = false;
      setSaving(false);
    }
  }

  return (
    <div className="page" {...bindSwipe(goPrev, goNext)}>
      <div className="qhdr">
        <div className="qhdr-top">
          <button className="btn-bk" onClick={() => navigate('/')}>
            <IconChevronLeft size={18} />
          </button>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="qhdr-title">{deal.client_name}</div>
            <div className="qhdr-sub">{deal.client_phone} · статус: {DEAL_STATUS_LABELS[deal.status]}</div>
          </div>
        </div>
        <div className="qhdr-step">
          Пройдено {viewIndex + 1} з {totalVisits}
        </div>
      </div>

      <div className="sc" style={{ paddingTop: 8, paddingBottom: 16 }}>
        {totalVisits === 0 && <div className="empty-state">Етапів поки немає</div>}

        {visit && (
          <div
            key={visit.id}
            className={`qcard${visit.id === highlightId ? ' qcard--new' : ''}`}
            onAnimationEnd={() => setHighlightId(null)}
          >
            <div className="qtitle" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {visit.is_decision && <IconGitBranch size={16} color="var(--acc)" />}
              {visit.stage_code}: {visit.stage_name}
            </div>

            <div className="scen-card" style={{ marginTop: 8, marginBottom: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <IconClock size={13} color="var(--mu2)" />
                <span style={{ fontSize: 12, color: 'var(--mu)' }}>
                  {STAGE_STATUS_LABELS[visit.status]}{visit.decision !== null ? ` · ${visit.decision ? (visit.yes_label || 'Так') : (visit.no_label || 'Ні')}` : ''}
                </span>
              </div>
              {visit.comments?.map(c => (
                <div key={c.id} style={{ fontSize: 12, color: 'var(--mu)', marginTop: 4 }}>💬 {c.comment_text}</div>
              ))}
            </div>

            {isActive && isDealActive && (
              <div>
                {visit.is_decision && (
                  <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                    <button
                      className="btn-s"
                      style={{ flex: 1, background: draft.decision === true ? 'var(--ok)' : undefined, color: draft.decision === true ? '#fff' : undefined }}
                      onClick={() => setDraft(d => ({ ...d, decision: true }))}
                    >
                      <IconCheck size={16} /> {visit.yes_label || 'Так'}
                    </button>
                    <button
                      className="btn-s"
                      style={{ flex: 1, background: draft.decision === false ? 'var(--err)' : undefined, color: draft.decision === false ? '#fff' : undefined }}
                      onClick={() => setDraft(d => ({ ...d, decision: false }))}
                    >
                      <IconX size={16} /> {visit.no_label || 'Ні'}
                    </button>
                  </div>
                )}
                <textarea
                  className="finp"
                  rows={2}
                  placeholder="Коментар (необовʼязково)"
                  style={{ resize: 'none', marginBottom: 8 }}
                  value={draft.comment || ''}
                  onChange={e => setDraft(d => ({ ...d, comment: e.target.value }))}
                />
                <button className="btn-p" onClick={handleAdvance} disabled={saving || cooldown}>
                  <IconSend size={18} /> {saving ? 'Збереження...' : 'Далі'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {totalVisits > 0 && (
        <div className="step-nav-mini">
          <button className="step-nav-circle" onClick={goPrev} disabled={viewIndex <= 0}>‹</button>
          <span className="step-nav-counter">{viewIndex + 1} / {totalVisits}</span>
          <button className="step-nav-circle accent" onClick={goNext} disabled={viewIndex >= totalVisits - 1}>›</button>
        </div>
      )}
    </div>
  );
}
