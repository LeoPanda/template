/**
 * このファイルは `npm run codegen:types` によりバックエンドの OpenAPI スキーマから自動生成されます。
 * 手動で編集しないでください。
 */

export interface ItemDto {
  id: number;
  user_id: string;
  code: string;
  name: string;
  location_description?: string;
  image_url?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface InternalHealthDto {
  status: string;
  timestamp: string;
  database: {
    connected: boolean;
    engine?: string;
  };
}
