import React, { useState } from 'react';
import { Menu, Sun, Moon, Laptop } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

interface HeaderProps {
  systemName?: string;
  version?: string;
  onMenuToggle?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  systemName = 'システム名称',
  version = '1.0.0',
  onMenuToggle,
}) => {
  const { theme, setTheme } = useTheme();

  return (
    <header className="sticky top-0 z-40 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <a href="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white font-bold text-lg shadow-md group-hover:scale-105 transition">
            🚀
          </div>
          <span className="text-xl font-black bg-gradient-to-r from-blue-600 via-indigo-600 to-slate-900 dark:to-slate-100 bg-clip-text text-transparent tracking-tight">
            {systemName}
          </span>
          <span className="px-2 py-0.5 text-[11px] font-bold rounded-full bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 tracking-wide font-mono">
            v{version}
          </span>
        </a>

        <div className="flex items-center gap-2">
          {/* テーマ切替ボタン群 */}
          <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-lg p-0.5 border border-slate-200 dark:border-slate-700">
            <button
              onClick={() => setTheme('light')}
              title="Light mode"
              className={`p-1.5 rounded-md transition ${
                theme === 'light'
                  ? 'bg-white dark:bg-slate-700 text-blue-600 shadow-xs'
                  : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <Sun className="w-4 h-4" />
            </button>
            <button
              onClick={() => setTheme('dark')}
              title="Dark mode"
              className={`p-1.5 rounded-md transition ${
                theme === 'dark'
                  ? 'bg-white dark:bg-slate-700 text-blue-400 shadow-xs'
                  : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <Moon className="w-4 h-4" />
            </button>
            <button
              onClick={() => setTheme('system')}
              title="System theme"
              className={`p-1.5 rounded-md transition ${
                theme === 'system'
                  ? 'bg-white dark:bg-slate-700 text-indigo-500 shadow-xs'
                  : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <Laptop className="w-4 h-4" />
            </button>
          </div>

          {onMenuToggle && (
            <button
              onClick={onMenuToggle}
              title="Menu"
              className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
