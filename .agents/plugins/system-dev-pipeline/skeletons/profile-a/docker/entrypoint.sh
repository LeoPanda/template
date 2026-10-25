#!/bin/bash
set -e

echo "=== [Profile A] Starting Cloud Run Container ==="

DB_PATH="/data/app.db"
export DATABASE_URL="sqlite:///${DB_PATH}"

# 1. Litestream リストア処理 (初回起動またはコンテナ再起動時のフェイルセーフ)
if [ -n "$LITESTREAM_BUCKET" ]; then
    echo "--> Checking for existing Litestream replica in GCS..."
    if litestream restore -if-replica-exists -config /etc/litestream.yml "${DB_PATH}"; then
        echo "--> Database restored successfully or no replica found."
    else
        echo "FATAL: Litestream restore failed! Aborting startup to prevent split-brain." >&2
        exit 1
    fi
else
    echo "--> WARNING: LITESTREAM_BUCKET is not set. Running without replication."
fi

# 2. Alembic マイグレーション適用
echo "--> Applying database migrations with Alembic..."
cd /app/backend
if alembic upgrade head; then
    echo "--> Alembic migrations applied successfully."
else
    echo "FATAL: Alembic migration failed! Aborting startup." >&2
    exit 1
fi
cd /app

# 3. Litestream スーパーバイザー起動 (SIGTERM シグナル伝播と最終 WAL フラッシュ同期保証)
if [ -n "$LITESTREAM_BUCKET" ]; then
    echo "--> Starting Uvicorn under Litestream supervisor on port ${PORT:-8080}..."
    exec litestream run -config /etc/litestream.yml -- uvicorn core.main:app --host 0.0.0.0 --port "${PORT:-8080}"
else
    echo "--> Starting Uvicorn server standalone on port ${PORT:-8080}..."
    exec uvicorn core.main:app --host 0.0.0.0 --port "${PORT:-8080}"
fi
