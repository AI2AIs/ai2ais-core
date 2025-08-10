# Multi-stage build for production optimization
FROM python:3.13-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies including tools for rhubarb
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    unzip \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Download platform-appropriate rhubarb binary
RUN ARCH=$(uname -m) && \
    echo "Detected architecture: $ARCH" && \
    mkdir -p bin && \
    if [ "$ARCH" = "x86_64" ] || [ "$ARCH" = "amd64" ]; then \
        echo "Downloading rhubarb v1.13.0 for x86_64/AMD64 Linux..." && \
        wget -q https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.13.0/rhubarb-lip-sync-1.13.0-linux.zip && \
        unzip -q rhubarb-lip-sync-1.13.0-linux.zip && \
        cp rhubarb-lip-sync-1.13.0-linux/rhubarb bin/ && \
        rm -rf rhubarb-lip-sync-1.13.0-linux* && \
        echo "x86_64/AMD64 rhubarb v1.13.0 binary installed"; \
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then \
        echo "ARM64 detected - creating fallback (no ARM64 rhubarb available)..." && \
        echo '#!/bin/bash\necho "TTS disabled - ARM64 not supported by rhubarb"' > bin/rhubarb; \
    else \
        echo "Unsupported architecture: $ARCH - creating fallback rhubarb binary" && \
        echo '#!/bin/bash\necho "TTS disabled for unsupported architecture: '$ARCH'"' > bin/rhubarb; \
    fi && \
    chmod +x bin/rhubarb && \
    echo "Rhubarb binary prepared for $ARCH"

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.13-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app user (security best practice)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy rhubarb binary from builder
COPY --from=builder /app/bin/rhubarb ./bin/rhubarb

# Copy application code
COPY . .

# Create necessary directories and set proper permissions
RUN mkdir -p logs data/voices && \
    chown -R appuser:appuser /app && \
    chmod +x bin/rhubarb

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3002/health || exit 1

# Expose port
EXPOSE 3002

# Run the application
CMD ["python", "-m", "app.main"]