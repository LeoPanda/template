import { useEffect } from 'react';

export interface ShortcutHandlers {
  onSave?: () => void;
  onOpen?: () => void;
  onFind?: () => void;
  onSettings?: () => void;
  onEscape?: () => void;
}

/**
 * デスクトップ標準のグローバルキーボードショートカットを監視するフック
 */
export const useShortcuts = (handlers: ShortcutHandlers) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isCmdOrCtrl = e.metaKey || e.ctrlKey;

      if (isCmdOrCtrl && e.key.toLowerCase() === 's') {
        e.preventDefault();
        handlers.onSave?.();
      } else if (isCmdOrCtrl && e.key.toLowerCase() === 'o') {
        e.preventDefault();
        handlers.onOpen?.();
      } else if (isCmdOrCtrl && e.key.toLowerCase() === 'f') {
        e.preventDefault();
        handlers.onFind?.();
      } else if (isCmdOrCtrl && e.key === ',') {
        e.preventDefault();
        handlers.onSettings?.();
      } else if (e.key === 'Escape') {
        handlers.onEscape?.();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handlers]);
};
