import React, { useState } from 'react';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { Button } from './components/ui/Button';
import { Modal } from './components/ui/Modal';
import { Drawer } from './components/ui/Drawer';
import { Table } from './components/ui/Table';
import { formatToJST } from './utils/dateTime';

export function App() {
  const [currentPath, setCurrentPath] = useState('/');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // サンプルデータ
  const sampleItems = [
    {
      id: 1,
      code: 'A-01',
      name: 'Sample Item 1',
      created_at: '2026-10-15T00:00:00Z',
    },
    {
      id: 2,
      code: 'A-02',
      name: 'Sample Item 2',
      created_at: '2026-10-15T01:00:00Z',
    },
  ];

  const columns = [
    { key: 'code', header: '識別コード' },
    { key: 'name', header: '名称' },
    {
      key: 'created_at',
      header: '作成日時 (JST)',
      render: (item: typeof sampleItems[0]) => formatToJST(item.created_at),
    },
    {
      key: 'actions',
      header: '操作',
      render: () => (
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => setIsDrawerOpen(true)}
          >
            詳細
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans">
      <Header
        systemName="Profile A Web System"
        version="1.0.0"
        onMenuToggle={() => setIsDrawerOpen(true)}
      />

      <div className="flex-1 flex max-w-[1800px] w-full mx-auto">
        <Sidebar currentPath={currentPath} onNavigate={setCurrentPath} />

        <main className="flex-1 p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100 tracking-tight">
                ダッシュボード
              </h1>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                AI駆動システム開発テンプレート V2.2 (Profile A)
              </p>
            </div>
            <Button onClick={() => setIsModalOpen(true)}>新規作成</Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                総データ件数
              </span>
              <p className="text-3xl font-black text-blue-600 mt-2">2 件</p>
            </div>
            <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                モックモード
              </span>
              <p className="text-3xl font-black text-emerald-600 mt-2">
                {import.meta.env.VITE_ENABLE_MOCK === 'true' ? 'ON (MSW)' : 'OFF'}
              </p>
            </div>
            <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                システムプロファイル
              </span>
              <p className="text-3xl font-black text-indigo-600 mt-2">Profile A</p>
            </div>
          </div>

          <div className="space-y-4">
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              データ一覧
            </h2>
            <Table
              columns={columns}
              data={sampleItems}
              keyExtractor={(item) => item.id}
            />
          </div>
        </main>
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="新規データ登録"
      >
        <p className="text-sm text-slate-600 dark:text-slate-300">
          ここにフォームコンポーネントを配置します。
        </p>
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
            キャンセル
          </Button>
          <Button onClick={() => setIsModalOpen(false)}>保存</Button>
        </div>
      </Modal>

      <Drawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        title="アイテム詳細"
      >
        <p className="text-sm text-slate-600 dark:text-slate-300">
          詳細情報および画像ギャラリーを表示します。
        </p>
      </Drawer>
    </div>
  );
}

export default App;
