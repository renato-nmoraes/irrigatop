#!/bin/bash

# Initialize the database (if not already initialized)
flask db init

# Run database migrations (if applicable)
flask db migrate

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