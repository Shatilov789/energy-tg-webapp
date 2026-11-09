import { useRef } from 'react';

const MIN_SWIPE_PX = 50;

// Returns a binder: spread bindSwipe(onSwipeRight, onSwipeLeft) onto the swipeable element.
// Taking the callbacks at bind time lets pages define them after their early returns.
export function useHorizontalSwipe() {
  const start = useRef(null);

  return function bindSwipe(onSwipeRight, onSwipeLeft) {
    return {
      onTouchStart(e) {
        start.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      },
      onTouchEnd(e) {
        if (start.current === null) return;
        const dx = e.changedTouches[0].clientX - start.current.x;
        const dy = e.changedTouches[0].clientY - start.current.y;
        start.current = null;
        // A mostly vertical gesture is a scroll, not a swipe.
        if (Math.abs(dx) < MIN_SWIPE_PX || Math.abs(dx) < Math.abs(dy)) return;
        if (dx > 0) onSwipeRight();
        else onSwipeLeft();
      },
    };
  };
}
