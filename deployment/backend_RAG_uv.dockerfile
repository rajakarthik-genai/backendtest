# Optimized Dockerfile using UV for faster dependency management
FROM python:3.10-slim

# Install system dependencies and UV
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add UV to PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Create working directory
WORKDIR /app

# Copy UV configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies using UV (much faster than pip)
RUN uv sync --frozen --no-dev

# Copy the application code
COPY . .

# Set PYTHONPATH so 'src' is importable
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Use UV to run the application
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
