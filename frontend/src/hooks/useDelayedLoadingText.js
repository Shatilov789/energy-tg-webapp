import { useEffect, useState } from 'react';

/**
 * Shows the loading text only when loading takes longer than delayMs,
 * so fast loads do not flash it.
 */
export function useDelayedLoadingText(loading, delayMs = 3000) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (!loading) {
      setShow(false);
      return;
    }
    const timer = setTimeout(() => setShow(true), delayMs);
    return () => clearTimeout(timer);
  }, [loading, delayMs]);

  return show;
}
