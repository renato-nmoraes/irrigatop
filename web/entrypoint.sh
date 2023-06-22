#!/bin/bash

# Initialize the database (if not already initialized)
flask db init

# Run database migrations (if applicable)
flask db migrate

# Apply any pending database migrations
flask db upgrade



# Start the application with Gunicorn
if [[ $FLASK_DEBUG == "1" ]]; then
    python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m flask run -h 0.0.0.0 -p 5000
else
    exec gunicorn --bind 0.0.0.0:5000 app:app
fi
