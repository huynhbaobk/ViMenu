FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (https://github.com/astral-sh/uv)
RUN pip install --no-cache-dir uv

# Copy only pyproject.toml and source code early (for caching layers)
COPY pyproject.toml ./
COPY app ./app

# Install Python dependencies directly from pyproject.toml
RUN uv pip install --system ".[all]" --editable .

# Copy the rest of your app code if needed (e.g., scripts, static, etc.)
COPY . .

# Tạo user không phải root
RUN useradd -m -u 1000 appuser

# Tạo thư mục static và logs, đảm bảo quyền thuộc về appuser
RUN mkdir -p /app/static /app/logs && \
    chown -R appuser:appuser /app

# Set user không phải root
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=10)"

# Run the application
CMD ["python", "-m", "app.main"]
