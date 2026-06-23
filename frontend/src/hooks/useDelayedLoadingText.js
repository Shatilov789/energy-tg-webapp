import { useEffect, useState } from 'react';

/**
 * Показывает текст "Загрузка..." только если загрузка длится дольше delayMs.
 * Быстрые загрузки не мигают текстом.
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
