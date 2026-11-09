import { IconSend } from '@tabler/icons-react';

export default function StepNav({ currentIndex, totalSteps, canAdvance, onPrev, onNext }) {
  if (currentIndex >= totalSteps) {
    return (
      <div className="step-nav-mini">
        <button className="btn-p green" onClick={onNext} disabled={!canAdvance} style={{ flex: 1 }}>
          <IconSend size={18} /> Надіслати звіт
        </button>
      </div>
    );
  }

  return (
    <div className="step-nav-mini">
      <button className="step-nav-circle" onClick={onPrev} disabled={currentIndex <= 1}>‹</button>
      <span className="step-nav-counter">{currentIndex} / {totalSteps}</span>
      <button className="step-nav-circle accent" onClick={onNext} disabled={!canAdvance}>›</button>
    </div>
  );
}
