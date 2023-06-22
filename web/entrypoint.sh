#!/bin/bash

# Initialize the database (if not already initialized)
flask db init

# Run database migrations (if applicable)
flask db migrate

# Apply any pending database migrations
flask db upgrade


# Start the application with Gunicorn
exec gunicorn --bind 0.0.0.0:5000 app:app
