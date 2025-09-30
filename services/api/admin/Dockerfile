FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY ../../pyproject.toml ./
RUN pip install --no-cache-dir uv && uv pip install --system -e .

# Copy application code
COPY . .

# Expose port
EXPOSE 8084

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8084"]
