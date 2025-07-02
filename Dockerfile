# Dockerfile
# DENSO Project Manager Pro - Production Container
# Multi-stage build for optimal image size and security

# =============================================================================
# BUILD STAGE
# =============================================================================
FROM python:3.11-slim as builder

# Set build arguments
ARG APP_VERSION=2.0.0
ARG BUILD_DATE
ARG VCS_REF

# Labels for metadata
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="DENSO Project Manager Pro" \
      org.label-schema.description="Enterprise Project Management Platform" \
      org.label-schema.version=$APP_VERSION \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.schema-version="1.0" \
      maintainer="DENSO Development Team <dev@denso.com>"

# Set environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gnupg2 \
    unixodbc-dev \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver 18 for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt \
    && pip cache purge

# =============================================================================
# PRODUCTION STAGE
# =============================================================================
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    unixodbc \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver 18 for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app user for security
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

# Create application directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/logs /app/data/uploads /app/data/exports /app/data/backups \
    && chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Create .streamlit directory and copy config
RUN mkdir -p .streamlit

# Copy configuration files
COPY --chown=appuser:appuser .streamlit/ .streamlit/
COPY --chown=appuser:appuser config/ config/

# Set proper permissions
RUN chmod +x app.py \
    && chmod -R 755 /app \
    && chmod -R 777 /app/logs /app/data

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=true", \
     "--browser.gatherUsageStats=false"]

# =============================================================================
# DEVELOPMENT STAGE (Optional)
# =============================================================================
FROM production as development

# Switch back to root for development tools
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    htop \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    black \
    flake8 \
    mypy \
    ipython \
    jupyter

# Create development entrypoint
COPY <<EOF /app/dev-entrypoint.sh
#!/bin/bash
set -e

echo "🔧 Development Mode - DENSO Project Manager Pro"
echo "=============================================="

# Check if database is accessible
if ! python -c "from database_service import get_database_service; get_database_service().connection_manager.test_connection()"; then
    echo "⚠️ Warning: Database connection failed"
fi

# Start the application with development settings
exec streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.runOnSave=true \
    --server.fileWatcherType=auto \
    --logger.level=debug
EOF

RUN chmod +x /app/dev-entrypoint.sh

# Switch back to app user
USER appuser

# Development command
CMD ["/app/dev-entrypoint.sh"]