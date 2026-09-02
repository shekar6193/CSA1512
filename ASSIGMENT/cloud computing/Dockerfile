# Multi-stage Cloud-Ready Dockerfile for CampusPulse Platform
# Stage 1: Build & Dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir --user email-validator

# Stage 2: Minimal Production Runtime
FROM python:3.11-slim AS runtime

# Create non-root user for security compliance (CIS benchmark)
RUN useradd -m -u 1001 campususer

WORKDIR /app

# Copy python packages from builder stage
COPY --from=builder /root/.local /home/campususer/.local
ENV PATH=/home/campususer/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HOST=0.0.0.0

# Copy application source code
COPY --chown=campususer:campususer . .

# Create uploads directory with appropriate permissions
RUN mkdir -p /app/uploads && chown -R campususer:campususer /app/uploads

USER campususer

# Expose HTTP port
EXPOSE 8000

# Health check probe for container orchestrator
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Start Uvicorn ASGI Server
CMD ["python", "main.py"]
