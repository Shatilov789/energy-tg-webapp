import { IconCircleCheck } from '@tabler/icons-react';
import { formatDate } from '../../utils/date';
import { objectsWord } from './objectStats';

function CompletedObject({ obj }) {
  const workers = obj.workers || [];
  return (
    <div className="obj-accordion">
      <div className="obj-row" style={{ cursor: 'default' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {obj.name}
          </div>
          <div style={{ fontSize: 11, color: 'var(--mu)', marginTop: 2 }}>
            {obj.scenario?.name || '—'} · {formatDate(obj.created_at)}
          </div>
          {workers.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 5 }}>
              {workers.map(w => (
                <span className="adm-worker-tag" key={w.user_id} style={{ cursor: 'default' }}>
                  {w.user?.first_name} {(w.user?.last_name || '').charAt(0)}{w.user?.last_name ? '.' : ''}
                </span>
              ))}
            </div>
          )}
        </div>
        <span className="bdg bdg-ok">100%</span>
      </div>
    </div>
  );
}

export default function CompletedTab({ objects }) {
  return (
    <>
      {objects.length === 0 ? (
        <div className="empty-state">
          <IconCircleCheck size={40} />
          Завершених обʼєктів поки немає
        </div>
      ) : (
        <>
          <div className="slbl" style={{ marginTop: 4 }}>
            {objects.length} {objectsWord(objects.length)} завершено
          </div>
          {objects.map(obj => <CompletedObject obj={obj} key={obj.id} />)}
        </>
      )}
      <div style={{ height: 20 }} />
    </>
  );
}
