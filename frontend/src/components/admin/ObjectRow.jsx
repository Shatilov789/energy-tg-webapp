import { IconChevronDown, IconChevronRight, IconMessagePlus, IconUserPlus, IconUsers } from '@tabler/icons-react';
import { formatDate, formatDateTime } from '../../utils/date';
import { getProgress } from './objectStats';

function ResponsibleWorkers({ obj, onRemoveWorker, onOpenWorkerModal }) {
  const workers = obj.workers || [];
  return (
    <div className="adm-workers-row">
      <IconUsers size={12} style={{ color: 'var(--mu)', flexShrink: 0 }} />
      <div className="adm-workers-list">
        {workers.map(w => (
          <span className="adm-worker-tag" key={w.user_id}>
            {w.user?.first_name} {(w.user?.last_name || '').charAt(0)}.
            <button
              className="adm-worker-remove"
              onClick={() => onRemoveWorker(obj.id, w.user_id)}
              title="Прибрати відповідального"
            >×</button>
          </span>
        ))}
        <button
          className="adm-worker-add"
          onClick={() => onOpenWorkerModal({ objectId: obj.id, currentWorkerIds: workers.map(w => w.user_id) })}
          title="Додати відповідального"
        >
          <IconUserPlus size={12} />
        </button>
      </div>
    </div>
  );
}

function StatusNote({ note }) {
  return (
    <div style={{
      fontSize: 13,
      color: 'var(--tx)',
      background: 'var(--bg)',
      border: '1px solid var(--br)',
      borderRadius: 'var(--rs)',
      padding: '9px 12px',
      lineHeight: 1.45,
      marginBottom: 6,
      whiteSpace: 'pre-wrap',
    }}>
      <div>{note.note_text}</div>
      <div style={{ fontSize: 11, color: 'var(--mu)', marginTop: 5 }}>
        {note.author?.first_name} {note.author?.last_name || ''} · {formatDateTime(note.created_at)}
      </div>
    </div>
  );
}

function ObjectDetails({ obj, notesByStep, onRemoveWorker, onOpenWorkerModal, onOpenComment }) {
  const { stepsCount, answersCount, pct } = getProgress(obj);
  const notesLoaded = !!notesByStep;

  const answeredItems = (obj.answers || [])
    .map(answer => ({
      answer,
      step: obj.scenario?.steps?.find(s => s.id === answer.step_id),
      notes: notesByStep?.[answer.step_id] || [],
    }))
    .filter(item => item.step)
    .sort((a, b) => a.step.step_number - b.step.step_number);

  return (
    <div className="obj-body">
      <ResponsibleWorkers obj={obj} onRemoveWorker={onRemoveWorker} onOpenWorkerModal={onOpenWorkerModal} />

      <div className="obj-progress-bar" style={{ marginTop: 8 }}>
        <div className="obj-progress-fill" style={{
          width: `${pct}%`,
          background: pct === 100 ? 'var(--ok)' : pct === 0 ? 'var(--err)' : 'var(--acc)',
        }} />
      </div>
      <div style={{ fontSize: 11, color: 'var(--mu)', marginTop: 4, marginBottom: 8 }}>
        {answersCount} з {stepsCount} етапів заповнено
      </div>

      {!notesLoaded && (
        <div style={{ fontSize: 12, color: 'var(--mu)', fontStyle: 'italic' }}>Завантаження...</div>
      )}

      {notesLoaded && answeredItems.length === 0 && (
        <div style={{ fontSize: 12, color: 'var(--mu)', fontStyle: 'italic', padding: '4px 0' }}>
          Записів поки немає
        </div>
      )}

      {notesLoaded && answeredItems.map(({ answer, step, notes }) => (
        <div className="adm-detail" key={answer.id}>
          <div style={{ fontSize: 11, color: 'var(--mu)', marginBottom: 4 }}>
            Етап {step.step_number} · {step.question_text}
          </div>

          {notes.length === 0 && (
            <div style={{ fontSize: 12, color: 'var(--mu)', fontStyle: 'italic', marginBottom: 8 }}>
              Немає записів
            </div>
          )}

          {notes.map(note => <StatusNote note={note} key={note.id} />)}

          <div className="adm-actions">
            <button
              className="comment-btn"
              onClick={() => onOpenComment({ answerId: answer.id, stepText: step.question_text })}
            >
              <IconMessagePlus size={13} /> Коментар
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ObjectRow({ obj, isOpen, notesByStep, onToggle, onRemoveWorker, onOpenWorkerModal, onOpenComment }) {
  const { pct } = getProgress(obj);

  let badgeCls = 'bdg-pend';
  if (pct === 0) badgeCls = 'bdg-err';
  if (pct === 100) badgeCls = 'bdg-ok';

  return (
    <div className="obj-accordion">
      <div className="obj-row" onClick={() => onToggle(obj)}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {obj.name}
          </div>
          <div style={{ fontSize: 11, color: 'var(--mu)', marginTop: 2 }}>
            {obj.scenario?.name || '—'} · {formatDate(obj.created_at)}
          </div>
        </div>
        <span className={`bdg ${badgeCls}`}>{pct}%</span>
        <span className="obj-caret">
          {isOpen ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}
        </span>
      </div>
      {isOpen && (
        <ObjectDetails
          obj={obj}
          notesByStep={notesByStep}
          onRemoveWorker={onRemoveWorker}
          onOpenWorkerModal={onOpenWorkerModal}
          onOpenComment={onOpenComment}
        />
      )}
    </div>
  );
}
