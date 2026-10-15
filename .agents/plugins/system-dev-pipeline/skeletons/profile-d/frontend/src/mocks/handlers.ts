import { http, HttpResponse } from 'msw';

export const handlers = [
  // ヘルスチェックエンドポイントモック
  http.get('http://127.0.0.1:54321/api/internal/health', () => {
    return HttpResponse.json({ status: 'ok', mode: 'mock' });
  }),

  // サンプル業務APIモック
  http.get('http://127.0.0.1:54321/api/v1/items', () => {
    return HttpResponse.json([
      { id: '1', name: 'サンプルプロジェクトA', updated_at: '2026-10-15T07:30:00Z' },
      { id: '2', name: 'サンプルプロジェクトB', updated_at: '2026-10-15T08:00:00Z' },
    ]);
  }),
];
