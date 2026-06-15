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

# NOTE: runs as root so it can always write the SQLite DB on the bind-mounted
# /app/instance volume, which Docker creates as root on a fresh deploy. Dropping
# to a non-root user here crash-loops the container unless volume ownership is
# handled first (e.g. an entrypoint chown + gosu). Not worth the risk for this tool.

ENTRYPOINT ["/entrypoint.sh"]