import { useState, useEffect } from 'react';
import { apiClient } from '../services/apiClient';

interface AppConfig {
  session_token: string;
  api_port: number;
  platform: 'macos' | 'windows' | 'linux';
}

/**
 * Sidecar の接続状態とシステム設定を管理するフック
 */
export const useSidecarStatus = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [platform, setPlatform] = useState<'macos' | 'windows' | 'linux'>('windows');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const init = async () => {
      try {
        if (typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window) {
          const { invoke } = await import('@tauri-apps/api/core');
          const config = await invoke<AppConfig>('get_app_config');
          apiClient.setConfig(config.api_port, config.session_token);
          setPlatform(config.platform);
        } else {
          // Docker/Web 開発時のフォールバック設定
          apiClient.setConfig(54321, 'local-dev-token');
          setPlatform('macos');
        }

        // ヘルスチェック
        const health = await apiClient.get<{ status: string }>('/api/internal/health');
        if (health.status === 'ok') {
          setIsConnected(true);
        }
      } catch (e) {
        console.warn('[useSidecarStatus] Sidecar not yet connected:', e);
        setIsConnected(false);
      } finally {
        setIsLoading(false);
      }
    };

    init();
  }, []);

  return { isConnected, platform, isLoading };
};
