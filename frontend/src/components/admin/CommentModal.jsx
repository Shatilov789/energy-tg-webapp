import { useState } from 'react';

export default function CommentModal({ stepText, onSubmit, onClose }) {
  const [text, setText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    if (!text.trim()) return;
    setSubmitting(true);
    try {
      await onSubmit(text.trim());
    } catch (err) {
      alert(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="comment-overlay" onClick={onClose}>
      <div className="comment-modal" onClick={e => e.stopPropagation()}>
        <h3>Коментар до відповіді</h3>
        <div style={{ fontSize: 12, color: 'var(--mu)', marginBottom: 10 }}>
          {stepText}
        </div>
        <textarea
          className="qtextarea"
          placeholder="Введіть коментар..."
          value={text}
          onChange={e => setText(e.target.value)}
          rows={3}
          autoFocus
        />
        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          <button className="btn-s" style={{ flex: 1 }} onClick={onClose}>
            Скасувати
          </button>
          <button className="btn-p" style={{ flex: 1 }} onClick={handleSubmit} disabled={submitting || !text.trim()}>
            {submitting ? 'Надсилання...' : 'Надіслати'}
          </button>
        </div>
      </div>
    </div>
  );
}
