#!/bin/sh
# A fresh production volume has no schema. Apply the versioned migrations
# before serving traffic; Alembic makes this a no-op on subsequent starts.
set -eu

alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
