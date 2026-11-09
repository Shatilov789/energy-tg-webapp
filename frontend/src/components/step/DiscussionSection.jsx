import { useEffect, useRef, useState } from 'react';
import {
  IconAt,
  IconChevronDown,
  IconCornerUpLeft,
  IconMessage2,
  IconMessageCircle,
  IconSend,
  IconSpeakerphone,
  IconX,
} from '@tabler/icons-react';
import { api } from '../../api/client';
import { formatShortDateTime } from '../../utils/date';
import { getInitials } from '../../utils/person';

function authorName(comment) {
  if (comment.is_system_event) return 'Система';
  return `${comment.author?.first_name || ''} ${comment.author?.last_name || ''}`.trim();
}

function SystemEvent({ comment }) {
  return (
    <div className="discuss-event">
      {comment.event_type === 'admin_comment' ? <IconMessage2 size={13} /> : <IconSpeakerphone size={13} />}
      {comment.comment_text}
      <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--mu2)' }}>
        {formatShortDateTime(comment.created_at)}
      </span>
    </div>
  );
}

function Message({ comment, highlighted, onReply, onQuoteClick }) {
  return (
    <div className={`discuss-msg${highlighted ? ' discuss-msg--highlight' : ''}`} id={`comment-${comment.id}`}>
      <div className="discuss-avatar">
        {getInitials(comment.author?.first_name, comment.author?.last_name)}
      </div>
      <div className="discuss-body">
        <div className="discuss-meta">
          <span className="discuss-author">
            {comment.author?.first_name} {comment.author?.last_name || ''}
          </span>
          {comment.recipient && (
            <span className="discuss-to">
              <IconAt size={11} /> {comment.recipient.first_name} {comment.recipient.last_name || ''}
            </span>
          )}
          <span className="discuss-time">{formatShortDateTime(comment.created_at)}</span>
          <button className="discuss-reply-btn" onClick={() => onReply(comment)} title="Відповісти">
            <IconCornerUpLeft size={13} />
          </button>
        </div>
        {comment.reply_to && (
          <div className="discuss-quoted" onClick={() => onQuoteClick(comment.reply_to.id)} title="Перейти до повідомлення">
            <span className="discuss-quoted-author">{authorName(comment.reply_to)}</span>
            {comment.reply_to.comment_text}
          </div>
        )}
        <div className="discuss-text">{comment.comment_text}</div>
      </div>
    </div>
  );
}

export default function DiscussionSection({ objectId, stepId }) {
  const [open, setOpen] = useState(false);
  const [comments, setComments] = useState([]);
  const [text, setText] = useState('');
  const [posting, setPosting] = useState(false);
  const [replyTo, setReplyTo] = useState(null);
  const [highlightedId, setHighlightedId] = useState(null);
  const listRef = useRef(null);

  useEffect(() => {
    setText('');
    setReplyTo(null);
    api.getStepComments(objectId, stepId).then(data => {
      setComments(data);
      if (data.length === 0) return;
      setOpen(true);
      // Wait for the list to render before jumping to the latest message.
      setTimeout(() => {
        if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
      }, 100);
    }).catch(() => setComments([]));
  }, [objectId, stepId]);

  function scrollToComment(id) {
    const el = document.getElementById(`comment-${id}`);
    if (!el) return;
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setHighlightedId(id);
    setTimeout(() => setHighlightedId(null), 1500);
  }

  async function handlePost() {
    const value = text.trim();
    if (!value) return;
    setPosting(true);
    try {
      const created = await api.addStepComment(objectId, stepId, {
        comment_text: value,
        reply_to_id: replyTo?.id ?? null,
      });
      setComments(await api.getStepComments(objectId, stepId));
      setText('');
      setReplyTo(null);
      // A reply is placed after its parent, not at the end of the list.
      setTimeout(() => scrollToComment(created.id), 100);
    } catch (err) {
      alert(err.message);
    } finally {
      setPosting(false);
    }
  }

  return (
    <div className="discuss-block">
      <div
        className="discuss-hdr collapse-toggle"
        style={!open ? { marginBottom: 0 } : undefined}
        onClick={() => setOpen(o => !o)}
      >
        <IconMessageCircle size={16} />
        Обговорення кроку
        {comments.length > 0 && <span className="collapse-badge" style={{ marginLeft: 4 }}>{comments.length}</span>}
        <IconChevronDown size={13} className={`collapse-chev${open ? ' open' : ''}`} />
      </div>

      {open && (
        <>
          {comments.length > 0 && (
            <div className="discuss-list" ref={listRef}>
              {comments.map(c => (c.is_system_event ? (
                <SystemEvent comment={c} key={c.id} />
              ) : (
                <Message
                  comment={c}
                  key={c.id}
                  highlighted={highlightedId === c.id}
                  onReply={setReplyTo}
                  onQuoteClick={scrollToComment}
                />
              )))}
            </div>
          )}

          <div className="discuss-form">
            {replyTo && (
              <div className="discuss-reply-bar">
                <div className="discuss-reply-bar-content">
                  <span className="discuss-reply-bar-author">{authorName(replyTo)}</span>
                  {replyTo.comment_text}
                </div>
                <button className="discuss-reply-cancel" onClick={() => setReplyTo(null)}>
                  <IconX size={14} />
                </button>
              </div>
            )}
            <div className="discuss-inputwrap">
              <textarea
                className="discuss-textarea"
                placeholder="Написати повідомлення..."
                value={text}
                onChange={e => setText(e.target.value)}
                rows={1}
              />
              <button
                className="discuss-send"
                onClick={handlePost}
                disabled={posting || !text.trim()}
                aria-label="Надіслати"
              >
                <IconSend size={16} />
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
