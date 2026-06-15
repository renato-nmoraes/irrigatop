# Use the official Python image as the base image
FROM python:3.9-slim-bookworm

# Set the working directory inside the container
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy the requirements.txt file to the working directory
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the working directory
COPY . .
RUN mv /app/entrypoint.sh /entrypoint.sh && chmod +x /entrypoint.sh

# Create a volume for the database
VOLUME /app/instance

# Expose the port on which the application will run
EXPOSE 5000

# Set the environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run as a non-root user; the app needs to write to /app (migrations) and /app/instance (db)
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

ENTRYPOINT ["/entrypoint.sh"]