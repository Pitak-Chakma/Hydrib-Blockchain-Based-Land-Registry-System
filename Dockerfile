# Production Dockerfile for Hydrib Land Registry System
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    FLASK_DEBUG=False

# Create application user
RUN groupadd -r landregistry && useradd -r -g landregistry landregistry

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /var/lib/landregistry/uploads \
    && mkdir -p /var/lib/landregistry/backups \
    && mkdir -p /var/log/landregistry

# Set permissions
RUN chown -R landregistry:landregistry /app \
    && chown -R landregistry:landregistry /var/lib/landregistry \
    && chown -R landregistry:landregistry /var/log/landregistry

# Switch to non-root user
USER landregistry

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "wsgi:application"]