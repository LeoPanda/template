/**
 * プラットフォーム非依存のストレージアダプターインターフェース
 * (LocalStorageの揮発性を防ぎ、Tauri Store / Local File へ透過的に切り替える)
 */
export interface IStorageAdapter {
  getItem<T>(key: string, defaultValue: T): Promise<T>;
  setItem<T>(key: string, value: T): Promise<void>;
  removeItem(key: string): Promise<void>;
  clear(): Promise<void>;
}
