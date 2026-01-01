# Multi-stage build for optimized Docker image
# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies (including devDependencies for build)
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend (outputs to backend/app/static)
RUN npm run build

# Stage 2: Python dependencies
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 3: Final runtime image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=backend-builder /root/.local /root/.local

# Copy backend application
COPY backend/ .

# Copy built frontend from frontend-builder
COPY --from=frontend-builder /frontend/../backend/app/static ./app/static

# Make sure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Expose port (Cloud Run will override with PORT env var)
EXPOSE 8000

# Health check (commented out for Cloud Run - it has its own health checks)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
#     CMD python -c "import requests; requests.get('http://localhost:8000/api/health')"

# Run the application
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
