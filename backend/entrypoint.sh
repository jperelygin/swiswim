#!/bin/sh
set -e

echo "Waiting for Postgres..."

until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-user}"; do
  sleep 1
done

echo "Postgres is ready"

cd /app

mkdir -p /app/alembic/versions



if [ "$ALEMBIC_RUN_MIGRATIONS_AUTO" = "1" ]; then
    echo "ALEMBIC MIGRATION IS RUNNING!"
    alembic -c alembic.ini upgrade head
    echo "ALEMBIC MIGRATION FINISHED!"
fi

if [ "$ALEMBIC_MAKE_NEW_REVISION" = "1" ]; then
    echo "ALEMBIC NEW REVISION CREATION STARTED."
    alembic -c alembic.ini revision --autogenerate -m "$ALEMBIC_REVISION_MESSAGE"
    alembic -c alembic.ini upgrade head
    echo "ALEMBIC NEW REVISION CREATION FINISHED."
fi

exec uvicorn backend.main:app --host 0.0.0.0 --port "${APP_PORT:-8000}" --workers 2