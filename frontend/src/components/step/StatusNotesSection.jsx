import { useEffect, useState } from 'react';
import { IconChevronDown, IconDeviceFloppy, IconSend } from '@tabler/icons-react';
import { formatShortDateTime } from '../../utils/date';

function autoGrow(e) {
  e.target.style.height = 'auto';
  e.target.style.height = e.target.scrollHeight + 'px';
}

// Immutable status log of a step. Only responsible workers and admins can add to it.
export default function StatusNotesSection({ stepId, notes, canPost, onPost }) {
  const [open, setOpen] = useState(true);
  const [text, setText] = useState('');
  const [posting, setPosting] = useState(false);

  useEffect(() => { setText(''); }, [stepId]);

  async function handlePost() {
    const value = text.trim();
    if (!value) return;
    setPosting(true);
    try {
      await onPost(value);
      setText('');
    } catch (err) {
      alert(err.message);
    } finally {
      setPosting(false);
    }
  }

  return (
    <div className="step-comment-section">
      <div className="step-comment-lbl collapse-toggle" onClick={() => setOpen(o => !o)}>
        <IconDeviceFloppy size={13} />
        Коментар до етапу
        {notes.length > 0 && <span className="collapse-badge">{notes.length}</span>}
        <IconChevronDown size={13} className={`collapse-chev${open ? ' open' : ''}`} />
      </div>

      {open && (
        <>
          {notes.length > 0 && (
            <div className="snotes-list">
              {notes.map(n => (
                <div className="snote" key={n.id}>
                  <div className="snote-meta">
                    <span className="snote-author">
                      {n.author?.first_name} {n.author?.last_name || ''}
                    </span>
                    <span className="snote-time">{formatShortDateTime(n.created_at)}</span>
                  </div>
                  <div className="snote-text">{n.note_text}</div>
                </div>
              ))}
            </div>
          )}

          {notes.length === 0 && !canPost && (
            <div className="snotes-empty">Немає записів статусу</div>
          )}

          {canPost && (
            <div className="discuss-inputwrap" style={{ marginTop: 6 }}>
              <textarea
                className="discuss-textarea"
                placeholder="Оновити статус етапу..."
                value={text}
                onChange={e => setText(e.target.value)}
                onInput={autoGrow}
                rows={1}
              />
              <button
                className="discuss-send"
                onClick={handlePost}
                disabled={posting || !text.trim()}
                aria-label="Додати запис"
              >
                <IconSend size={16} />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
