import React from 'react';

interface StatusBarProps {
  sidecarStatus?: 'connected' | 'disconnected' | 'processing';
  activeFile?: string;
  progressPercent?: number;
  message?: string;
}

/**
 * 画面最下部常駐ステータスバー (高さ 24px)
 */
export const StatusBar: React.FC<StatusBarProps> = ({
  sidecarStatus = 'connected',
  activeFile,
  progressPercent,
  message,
}) => {
  const statusColors = {
    connected: 'bg-emerald-500',
    disconnected: 'bg-rose-500',
    processing: 'bg-primary-500 animate-pulse',
  };

  return (
    <footer className="h-6 bg-slate-100 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 px-3 flex items-center justify-between text-[11px] text-slate-500 font-mono select-none flex-shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${statusColors[sidecarStatus]}`} />
          <span className="capitalize">Engine: {sidecarStatus}</span>
        </div>
        {activeFile && <span className="truncate max-w-xs">File: {activeFile}</span>}
        {message && <span className="text-slate-400">| {message}</span>}
      </div>

      <div className="flex items-center gap-3">
        {progressPercent !== undefined && (
          <div className="flex items-center gap-1.5">
            <div className="w-24 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-500 transition-all duration-200"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <span>{Math.round(progressPercent)}%</span>
          </div>
        )}
      </div>
    </footer>
  );
};
