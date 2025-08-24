# Multi-stage build for production
FROM node:18-alpine AS frontend-builder

# Build frontend
WORKDIR /app/frontend
COPY ascend-frontend/package*.json ./
RUN npm ci --only=production
COPY ascend-frontend/ ./
RUN npm run build

# Python backend
FROM python:3.11-slim AS backend

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app user
RUN groupadd -r app && useradd -r -g app app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY run_migrations.py init_db.py ./

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./static/

# Create data directory and set permissions
RUN mkdir -p data && chown -R app:app /app

# Switch to app user
USER app

# Initialize database
RUN python init_db.py

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]