import React, { useState } from 'react';
import { Folder, Settings, BarChart2, HardDrive } from 'lucide-react';
import { FramelessTitleBar } from './components/layout/FramelessTitleBar';
import { CollapsibleSidebar } from './components/layout/CollapsibleSidebar';
import { SplitPane } from './components/layout/SplitPane';
import { StatusBar } from './components/layout/StatusBar';
import { Button } from './components/ui/Button';
import { useSidecarStatus } from './hooks/useSidecarStatus';
import { useNativeDialog } from './hooks/useNativeDialog';
import { useShortcuts } from './hooks/useShortcuts';

export const App: React.FC = () => {
  const { isConnected, platform } = useSidecarStatus();
  const { pickFile } = useNativeDialog();
  const [activeTab, setActiveTab] = useState('files');
  const [currentFile, setCurrentFile] = useState<string | undefined>();

  // グローバルショートカット監視
  useShortcuts({
    onSave: () => console.log('Shortcut: Save triggered'),
    onOpen: async () => {
      const file = await pickFile();
      if (file) setCurrentFile(file);
    },
  });

  const sidebarItems = [
    { id: 'files', label: 'プロジェクトファイル', icon: <Folder className="w-4 h-4" /> },
    { id: 'analyze', label: 'データ解析・計算', icon: <BarChart2 className="w-4 h-4" /> },
    { id: 'storage', label: 'ローカルストレージ', icon: <HardDrive className="w-4 h-4" /> },
    { id: 'settings', label: '環境設定', icon: <Settings className="w-4 h-4" /> },
  ];

  const handleSelectFile = async () => {
    const file = await pickFile();
    if (file) setCurrentFile(file);
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 overflow-hidden font-sans">
      <FramelessTitleBar
        title="Desktop Application"
        version="1.0.0"
        platform={platform}
      />

      <div className="flex-1 flex overflow-hidden">
        <CollapsibleSidebar
          items={sidebarItems}
          activeId={activeTab}
          onSelect={setActiveTab}
        />

        <SplitPane
          leftPane={
            <div className="p-4 flex flex-col gap-3">
              <h2 className="text-sm font-bold text-slate-700 dark:text-slate-200">ファイル一覧</h2>
              <Button size="sm" onClick={handleSelectFile}>
                ファイルを開く (Cmd+O)
              </Button>
              {currentFile && (
                <div className="p-2.5 rounded bg-slate-100 dark:bg-slate-800 text-xs font-mono break-all border border-slate-200 dark:border-slate-700">
                  {currentFile}
                </div>
              )}
            </div>
          }
          rightPane={
            <div className="p-6 flex flex-col gap-4">
              <h1 className="text-lg font-bold">ワークスペース</h1>
              <p className="text-sm text-slate-500">
                Tauri v2 + Vue/React + Python Sidecar による完全ローカル処理環境。
              </p>
            </div>
          }
        />
      </div>

      <StatusBar
        sidecarStatus={isConnected ? 'connected' : 'disconnected'}
        activeFile={currentFile}
      />
    </div>
  );
};

export default App;
