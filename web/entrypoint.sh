#!/bin/bash

# Initialize the database (if not already initialized)
flask db init

# Apply any pending database migrations
flask db upgrade

# Run database migrations (if applicable)
flask db migrate

# Start the application with Gunicorn
exec gunicorn --bind 0.0.0.0:5000 app:app
