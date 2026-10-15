import React from 'react';
import { Minus, Square, X } from 'lucide-react';

interface FramelessTitleBarProps {
  title?: string;
  version?: string;
  platform?: 'macos' | 'windows' | 'linux';
  onMinimize?: () => void;
  onMaximize?: () => void;
  onClose?: () => void;
}

/**
 * デスクトップ用フレームレス・タイトルバー
 * (macOS トラフィックライトボタン回避 pl-20、Windows 操作ボタン配置)
 */
export const FramelessTitleBar: React.FC<FramelessTitleBarProps> = ({
  title = 'Desktop Application',
  version = '1.0.0',
  platform = 'windows',
  onMinimize,
  onMaximize,
  onClose,
}) => {
  const isMac = platform === 'macos';

  return (
    <header
      data-tauri-drag-region
      className={`h-9 select-none bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs z-50 flex-shrink-0 ${
        isMac ? 'pl-20 pr-4' : 'pl-4 pr-0'
      }`}
      style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}
    >
      {/* アプリ名 & バージョン */}
      <div className="flex items-center gap-2" style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}>
        <span className="font-bold text-slate-800 dark:text-slate-100">{title}</span>
        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700">
          v{version}
        </span>
      </div>

      {/* 中央ドラッグ余白 */}
      <div className="flex-1 h-full" data-tauri-drag-region />

      {/* Windows / Linux 操作ボタン群 (no-drag) */}
      {!isMac && (
        <div
          data-tauri-drag-region="false"
          style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}
          className="flex items-center h-full"
        >
          <button
            type="button"
            onClick={onMinimize}
            title="最小化"
            aria-label="最小化"
            className="w-10 h-full flex items-center justify-center text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <Minus className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={onMaximize}
            title="最大化"
            aria-label="最大化"
            className="w-10 h-full flex items-center justify-center text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <Square className="w-3 h-3" />
          </button>
          <button
            type="button"
            onClick={onClose}
            title="閉じる"
            aria-label="閉じる"
            className="w-10 h-full flex items-center justify-center text-slate-500 hover:bg-rose-600 hover:text-white transition"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </header>
  );
};
