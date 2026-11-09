import { IconChecks, IconChevronDown, IconChevronRight } from '@tabler/icons-react';
import { getInitials } from '../../utils/person';
import ObjectRow from './ObjectRow';
import { objectsWord } from './objectStats';

const AVA_COLORS = ['ava-a', 'ava-b', 'ava-c', 'ava-d'];

export default function ObjectsTab({
  metrics,
  workers,
  objectsByWorker,
  unassignedObjects,
  expandedWorkers,
  expandedObjects,
  objectNotes,
  onToggleWorker,
  onToggleObject,
  onRemoveWorker,
  onOpenWorkerModal,
  onOpenComment,
}) {
  function renderObjectRow(obj) {
    return (
      <ObjectRow
        key={obj.id}
        obj={obj}
        isOpen={expandedObjects.has(obj.id)}
        notesByStep={objectNotes[obj.id]}
        onToggle={onToggleObject}
        onRemoveWorker={onRemoveWorker}
        onOpenWorkerModal={onOpenWorkerModal}
        onOpenComment={onOpenComment}
      />
    );
  }

  return (
    <>
      <div className="dash-grid" style={{ marginTop: 4 }}>
        {metrics.map(m => (
          <div className="mc" key={m.label}>
            <div className="mc-label">{m.label}</div>
            <div className="mv" style={{ color: m.color }}>{m.value}</div>
            <div className="ml">{m.sub}</div>
          </div>
        ))}
      </div>

      <div className="slbl">Співробітники</div>

      {workers.length === 0 && unassignedObjects.length === 0 && (
        <div className="empty-state">
          <IconChecks size={40} />
          Обʼєктів немає
        </div>
      )}

      {workers.map((worker, idx) => {
        const workerObjects = objectsByWorker[worker.id] || [];
        const isOpen = expandedWorkers.has(worker.id);
        return (
          <div className="wkr-accordion" key={worker.id}>
            <div className="wkr-row" onClick={() => onToggleWorker(worker.id)}>
              <div className={`ava ${AVA_COLORS[idx % AVA_COLORS.length]}`}>
                {getInitials(worker.first_name, worker.last_name)}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>
                  {worker.first_name} {worker.last_name || ''}
                </div>
                <div style={{ fontSize: 11, color: 'var(--mu)', marginTop: 2 }}>
                  {workerObjects.length} {objectsWord(workerObjects.length)}
                </div>
              </div>
              <span style={{ color: 'var(--mu)', display: 'flex' }}>
                {isOpen ? <IconChevronDown size={16} /> : <IconChevronRight size={16} />}
              </span>
            </div>
            {isOpen && <div className="wkr-body">{workerObjects.map(renderObjectRow)}</div>}
          </div>
        );
      })}

      {unassignedObjects.length > 0 && (
        <>
          <div className="slbl" style={{ marginTop: 8 }}>Без відповідальних</div>
          {unassignedObjects.map(renderObjectRow)}
        </>
      )}

      <div style={{ height: 20 }} />
    </>
  );
}
