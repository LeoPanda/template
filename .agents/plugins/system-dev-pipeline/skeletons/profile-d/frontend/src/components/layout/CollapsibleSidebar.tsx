import React, { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface SidebarItem {
  id: string;
  label: string;
  icon: React.ReactNode;
}

interface CollapsibleSidebarProps {
  items: SidebarItem[];
  activeId: string;
  onSelect: (id: string) => void;
}

/**
 * 常設折りたたみサイドバー (アイコン幅 64px ↔ 展開幅 240px)
 */
export const CollapsibleSidebar: React.FC<CollapsibleSidebarProps> = ({
  items,
  activeId,
  onSelect,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <aside
      className={`h-full border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 transition-all duration-200 flex flex-col flex-shrink-0 ${
        isExpanded ? 'w-60' : 'w-16'
      }`}
    >
      {/* ナビゲーションアイテム一覧 */}
      <nav className="flex-1 py-3 flex flex-col gap-1 px-2">
        {items.map((item) => {
          const isActive = item.id === activeId;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelect(item.id)}
              className={`h-10 rounded-lg flex items-center transition px-3 gap-3 ${
                isActive
                  ? 'bg-primary-50 dark:bg-primary-950 text-primary-600 dark:text-primary-400 font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <span className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                {item.icon}
              </span>
              {isExpanded && <span className="text-sm truncate">{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* 開閉トグルボタン */}
      <div className="p-2 border-t border-slate-200 dark:border-slate-800 flex justify-end">
        <button
          type="button"
          onClick={() => setIsExpanded((prev) => !prev)}
          className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          title={isExpanded ? 'サイドバーを閉じる' : 'サイドバーを展開'}
        >
          {isExpanded ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
};
