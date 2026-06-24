#!/bin/bash
set -e

# The schema (a single `message` table) is created by db.create_all() in app.py,
# so we deliberately do NOT run flask-migrate here. Auto-generating migrations at
# runtime produces a new random revision id on every build, which then cannot be
# reconciled with a persisted DB that was stamped by an earlier build
# ("Can't locate revision ..."). If real migrations are ever needed, generate them
# in development and commit the migrations/ directory to the repo.

# Start the application with Gunicorn
if [[ $FLASK_DEBUG == "1" ]]; then
    echo "Running in debug mode..."
    pip install debugpy -t /tmp
    exec python /tmp/debugpy --wait-for-client --listen 0.0.0.0:5678 app.py runserver 0.0.0.0:5000 --nothreading --noreload
else
    exec gunicorn --bind 0.0.0.0:5000 app:app
fi
