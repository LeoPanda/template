import { IStorageAdapter } from './adapter.interface';
import { LazyStore } from '@tauri-apps/plugin-store';

/**
 * デスクトップ本番用 Tauri Store アダプター
 * (ローカル設定ファイル settings.json に安全に永続化)
 */
export class TauriStoreAdapter implements IStorageAdapter {
  private store: LazyStore;

  constructor(filename: string = 'settings.json') {
    this.store = new LazyStore(filename);
  }

  async getItem<T>(key: string, defaultValue: T): Promise<T> {
    try {
      const val = await this.store.get<T>(key);
      return val !== null && val !== undefined ? val : defaultValue;
    } catch (e) {
      console.warn(`[TauriStoreAdapter] Failed to get key: ${key}`, e);
      return defaultValue;
    }
  }

  async setItem<T>(key: string, value: T): Promise<void> {
    await this.store.set(key, value);
    await this.store.save();
  }

  async removeItem(key: string): Promise<void> {
    await this.store.delete(key);
    await this.store.save();
  }

  async clear(): Promise<void> {
    await this.store.clear();
    await this.store.save();
  }
}
