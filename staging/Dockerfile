FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test files
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/test-results

# Set environment variables
ENV PYTHONPATH=/app
ENV AWS_ACCESS_KEY_ID=test
ENV AWS_SECRET_ACCESS_KEY=test
ENV AWS_DEFAULT_REGION=us-east-1

# Default command
CMD ["python", "test_runner.py"] 