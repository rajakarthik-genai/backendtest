# Dockerfile
FROM python:3.10-slim

# Create working directory
WORKDIR /app

# Install system dependencies (if any, e.g., build tools)
RUN apt-get update && apt-get install -y gcc

# Copy requirements and install them
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application code (preserve src folder)
COPY . .

# Expose port (FastAPI default)
EXPOSE 8000

# Set PYTHONPATH so 'src' is importable
ENV PYTHONPATH=/app

# Command to run the app with Uvicorn using the correct module path
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
