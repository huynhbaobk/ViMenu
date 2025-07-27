# ViMenu - Development Dockerfile with uv
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/app/.uv-cache

# Set working directory
WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Create user for development
RUN useradd -m -u 1000 appuser

# Create directories and set permissions early
RUN mkdir -p /app/static /app/logs /app/.uv-cache && \
    chown -R appuser:appuser /app

# Switch to user before copying files
USER appuser

# Copy uv configuration files for better caching
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Install Python dependencies using uv (including dev dependencies)
RUN uv sync --frozen

# Copy application code
COPY --chown=appuser:appuser . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application using uv
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
