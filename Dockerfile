# Multi-stage build for MicroCFO Backend
FROM python:3.14-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.14-slim

# Create non-root user
RUN useradd -m -u 1000 microcfo && \
    mkdir -p /app /app/logs /app/temp_uploads /app/legal_db /app/scheme_db && \
    chown -R microcfo:microcfo /app

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/microcfo/.local

# Copy application code
COPY --chown=microcfo:microcfo . .

# Switch to non-root user
USER microcfo

# Add local bin to PATH
ENV PATH=/home/microcfo/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# Run the application
CMD ["uvicorn", "integration_server:app", "--host", "0.0.0.0", "--port", "8000"]
