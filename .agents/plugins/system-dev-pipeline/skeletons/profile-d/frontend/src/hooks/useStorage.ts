import { useState, useEffect, useCallback, useMemo } from 'react';
import { IStorageAdapter } from '../services/storage/adapter.interface';
import { TauriStoreAdapter } from '../services/storage/tauriStoreAdapter';
import { LocalStorageAdapter } from '../services/storage/localStorageAdapter';

/**
 * 環境に応じて TauriStore または LocalStorage を透過的に利用する永続化フック
 */
export function useStorage<T>(key: string, defaultValue: T) {
  const adapter: IStorageAdapter = useMemo(() => {
    if (typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window) {
      return new TauriStoreAdapter();
    }
    return new LocalStorageAdapter();
  }, []);

  const [state, setState] = useState<T>(defaultValue);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    let isMounted = true;
    adapter.getItem<T>(key, defaultValue).then((val) => {
      if (isMounted) {
        setState(val);
        setIsLoaded(true);
      }
    });
    return () => {
      isMounted = false;
    };
  }, [adapter, key, defaultValue]);

  const setValue = useCallback(
    async (value: T | ((prev: T) => T)) => {
      const nextValue = typeof value === 'function' ? (value as (prev: T) => T)(state) : value;
      setState(nextValue);
      await adapter.setItem(key, nextValue);
    },
    [adapter, key, state]
  );

  return [state, setValue, isLoaded] as const;
}
