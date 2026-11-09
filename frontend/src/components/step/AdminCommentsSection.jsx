import { useState } from 'react';
import { IconChevronDown, IconSpeakerphone } from '@tabler/icons-react';
import { formatShortDateTime } from '../../utils/date';

export default function AdminCommentsSection({ comments }) {
  const [open, setOpen] = useState(true);

  if (comments.length === 0) return null;

  return (
    <div className="discuss-block">
      <div
        className="discuss-hdr collapse-toggle"
        style={!open ? { marginBottom: 0 } : undefined}
        onClick={() => setOpen(o => !o)}
      >
        <IconSpeakerphone size={15} />
        Коментар адміністратора
        <span className="collapse-badge" style={{ marginLeft: 4 }}>{comments.length}</span>
        <IconChevronDown size={13} className={`collapse-chev${open ? ' open' : ''}`} />
      </div>
      {open && (
        <div style={{ marginTop: 8 }}>
          {comments.map(c => (
            <div className="admin-comment-item" key={c.id}>
              <div className="admin-comment-text">{c.comment_text}</div>
              <div className="admin-comment-time">{formatShortDateTime(c.created_at)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
