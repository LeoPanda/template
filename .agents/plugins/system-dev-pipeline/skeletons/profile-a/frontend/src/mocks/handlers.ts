import { http, HttpResponse } from 'msw';

export const handlers = [
  // ヘルスチェックモック
  http.get('/api/internal/health', () => {
    return HttpResponse.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      database: {
        connected: true,
        mock: true,
      },
    });
  }),

  // サンプルアイテムAPIモック
  http.get('/api/v1/items', () => {
    return HttpResponse.json([
      {
        id: 1,
        user_id: 'mock-user-123',
        code: 'A-01',
        name: 'Mock Item 1',
        created_at: '2026-10-15T00:00:00Z',
        updated_at: '2026-10-15T00:00:00Z',
      },
      {
        id: 2,
        user_id: 'mock-user-123',
        code: 'A-02',
        name: 'Mock Item 2',
        created_at: '2026-10-15T01:00:00Z',
        updated_at: '2026-10-15T01:00:00Z',
      },
    ]);
  }),
];
