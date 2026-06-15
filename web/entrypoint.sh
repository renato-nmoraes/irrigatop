#!/bin/bash
set -e

# Initialize the migrations directory only the first time
if [ ! -d migrations ]; then
    flask db init
    flask db migrate -m "initial schema"
fi

# Apply any pending database migrations
flask db upgrade


# Start the application with Gunicorn
if [[ $FLASK_DEBUG == "1" ]]; then
    echo "Running in debug mode..."
    pip install debugpy -t /tmp
    exec python /tmp/debugpy --wait-for-client --listen 0.0.0.0:5678 app.py runserver 0.0.0.0:5000 --nothreading --noreload
else
    exec gunicorn --bind 0.0.0.0:5000 app:app
fi