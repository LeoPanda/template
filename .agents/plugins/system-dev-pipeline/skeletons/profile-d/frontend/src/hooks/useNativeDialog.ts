import { useCallback } from 'react';

/**
 * OS ネイティブファイル/フォルダピッカーを呼び出すフック
 * (ブラウザの <input type="file"> を排除し、ローカル絶対パスを直接取得)
 */
export const useNativeDialog = () => {
  const pickFile = useCallback(
    async (options?: { title?: string; filters?: { name: string; extensions: string[] }[] }): Promise<string | null> => {
      // Tauri 環境チェック
      if (typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window) {
        try {
          const { open } = await import('@tauri-apps/plugin-dialog');
          const selected = await open({
            title: options?.title || 'ファイルを選択',
            multiple: false,
            directory: false,
            filters: options?.filters,
          });
          return typeof selected === 'string' ? selected : null;
        } catch (e) {
          console.error('[useNativeDialog] Tauri dialog error:', e);
          return null;
        }
      }

      // Web/Docker モック開発環境向けフォールバック
      console.warn('[useNativeDialog] Fallback to mock prompt in browser/docker mode');
      return prompt('開発モック: ローカルファイルパスを入力してください', '/mock/path/data.fit');
    },
    []
  );

  const pickDirectory = useCallback(
    async (options?: { title?: string }): Promise<string | null> => {
      if (typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window) {
        try {
          const { open } = await import('@tauri-apps/plugin-dialog');
          const selected = await open({
            title: options?.title || 'フォルダを選択',
            multiple: false,
            directory: true,
          });
          return typeof selected === 'string' ? selected : null;
        } catch (e) {
          console.error('[useNativeDialog] Tauri dialog error:', e);
          return null;
        }
      }
      return prompt('開発モック: フォルダパスを入力してください', '/mock/output/dir');
    },
    []
  );

  return { pickFile, pickDirectory };
};
