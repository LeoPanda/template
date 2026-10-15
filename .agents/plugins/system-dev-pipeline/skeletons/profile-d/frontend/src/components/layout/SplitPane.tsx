import React, { useState, useRef, useCallback } from 'react';

interface SplitPaneProps {
  leftPane: React.ReactNode;
  rightPane: React.ReactNode;
  defaultLeftWidth?: number;
  minLeftWidth?: number;
  maxLeftWidth?: number;
}

/**
 * リサイザブル左右スプリットペイン
 */
export const SplitPane: React.FC<SplitPaneProps> = ({
  leftPane,
  rightPane,
  defaultLeftWidth = 320,
  minLeftWidth = 240,
  maxLeftWidth = 600,
}) => {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth);
  const isDragging = useRef(false);

  const startResize = useCallback(
    (e: React.MouseEvent) => {
      isDragging.current = true;
      e.preventDefault();

      const onMouseMove = (moveEvent: MouseEvent) => {
        if (!isDragging.current) return;
        const newWidth = Math.min(Math.max(moveEvent.clientX, minLeftWidth), maxLeftWidth);
        setLeftWidth(newWidth);
      };

      const onMouseUp = () => {
        isDragging.current = false;
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
      };

      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    },
    [minLeftWidth, maxLeftWidth]
  );

  return (
    <div className="flex-1 flex overflow-hidden">
      <div style={{ width: `${leftWidth}px` }} className="flex-shrink-0 h-full overflow-y-auto">
        {leftPane}
      </div>
      <div
        onMouseDown={startResize}
        className="w-1 hover:w-1.5 bg-slate-200 dark:bg-slate-800 hover:bg-primary-500 cursor-col-resize transition-all z-10 flex-shrink-0"
      />
      <div className="flex-1 h-full overflow-y-auto bg-slate-50 dark:bg-slate-900/50">
        {rightPane}
      </div>
    </div>
  );
};
