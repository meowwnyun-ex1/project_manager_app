# Dockerfile
# SDX Project Manager - Production Container Image
# Multi-stage build for optimized production deployment

# ============================================================================
# BUILD STAGE - Development Dependencies
# ============================================================================
FROM python:3.11-slim as builder

# Build arguments
ARG PYTHON_VERSION=3.11
ARG APP_ENV=production
ARG BUILD_DATE
ARG VCS_REF

# Labels for container metadata
LABEL maintainer="DENSO Innovation Team <innovation@denso.com>" \
      version="2.5.0" \
      description="SDX Project Manager - Enterprise Edition" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/denso-innovation/sdx-project-manager" \
      org.label-schema.schema-version="1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    gnupg2 \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get install -y unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user and directory
RUN groupadd -r appuser && useradd -r -g appuser appuser
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# ============================================================================
# PRODUCTION STAGE - Runtime Environment
# ============================================================================
FROM python:3.11-slim as production

# Runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    APP_HOME=/app \
    APP_USER=appuser \
    PORT=8501

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg2 \
    ca-certificates \
    unixodbc \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver (runtime only)
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Create app user and directories
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && mkdir -p /app/logs /app/data/uploads /app/data/cache /app/data/backups /app/data/temp \
    && chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories and set permissions
RUN mkdir -p logs data/uploads data/cache data/backups data/temp \
    && chown -R appuser:appuser /app \
    && chmod +x scripts/*.sh 2>/dev/null || true

# Copy health check script
COPY --chown=appuser:appuser <<EOF /app/healthcheck.py
#!/usr/bin/env python3
import requests
import sys
import os

def check_health():
    try:
        port = os.getenv('PORT', '8501')
        response = requests.get(f'http://localhost:{port}/health', timeout=10)
        if response.status_code == 200:
            print("Health check passed")
            sys.exit(0)
        else:
            print(f"Health check failed with status: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Health check failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_health()
EOF

# Copy startup script
COPY --chown=appuser:appuser <<EOF /app/start.sh
#!/bin/bash
set -e

echo "=== SDX Project Manager Startup ==="
echo "Environment: $APP_ENV"
echo "Port: $PORT"
echo "User: $(whoami)"
echo "Working Directory: $(pwd)"

# Wait for database
echo "Waiting for database connection..."
python -c "
import time
import sys
from config.database import DatabaseManager
for i in range(30):
    try:
        db = DatabaseManager()
        db.get_connection()
        print('Database connection successful')
        break
    except Exception as e:
        print(f'Database connection attempt {i+1}/30 failed: {e}')
        time.sleep(2)
else:
    print('Failed to connect to database after 30 attempts')
    sys.exit(1)
"

# Run database migrations if needed
echo "Running database setup..."
python -c "
try:
    from config.database import DatabaseManager
    db = DatabaseManager()
    db.initialize_database()
    print('Database initialization completed')
except Exception as e:
    print(f'Database initialization failed: {e}')
"

# Start the application
echo "Starting SDX Project Manager..."
exec streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=true
EOF

RUN chmod +x /app/start.sh /app/healthcheck.py

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python /app/healthcheck.py

# Default command
CMD ["/app/start.sh"]

# ============================================================================
# BUILD INSTRUCTIONS
# ============================================================================
# 
# Build commands:
# docker build -t sdx-project-manager:latest .
# docker build -t sdx-project-manager:2.5.0 .
# 
# Development build:
# docker build --target builder -t sdx-project-manager:dev .
# 
# Multi-platform build:
# docker buildx build --platform linux/amd64,linux/arm64 -t sdx-project-manager:latest .
# 
# Build with arguments:
# docker build \
#   --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
#   --build-arg VCS_REF=$(git rev-parse HEAD) \
#   -t sdx-project-manager:latest .
# 
# ============================================================================