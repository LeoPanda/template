# ==============================================================================
# Stage 1: フロントエンド ビルドステージ
# ==============================================================================
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
# 本番ビルド時はモックを完全無効化
ENV VITE_ENABLE_MOCK=false
RUN npm run build

# ==============================================================================
# Stage 2: バックエンド & 実行ステージ
# ==============================================================================
FROM python:3.11-slim-bookworm AS runner

# システム依存パッケージおよび Litestream のインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Litestream のバイナリ取得
ADD https://github.com/benbjohnson/litestream/releases/download/v0.3.13/litestream-v0.3.13-linux-amd64.tar.gz /tmp/litestream.tar.gz
RUN tar -C /usr/local/bin -xzf /tmp/litestream.tar.gz && rm /tmp/litestream.tar.gz

WORKDIR /app

# バックエンド依存パッケージのインストール
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションソースコードのコピー
COPY backend/ ./backend/
COPY docker/litestream.yml /etc/litestream.yml
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Stage 1 でビルドしたフロントエンド静的アセットをコピー
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# データ永続化ディレクトリの準備
RUN mkdir -p /data

EXPOSE 8080
ENV PORT=8080
ENV PYTHONPATH=/app/backend

ENTRYPOINT ["/app/entrypoint.sh"]
