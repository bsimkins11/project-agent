FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    google-cloud-firestore==2.13.1 \
    google-cloud-storage==2.10.0 \
    google-auth==2.23.4 \
    pydantic==2.5.0

# Copy application code
COPY . .

# Expose port
EXPOSE 8083

# Run the application
CMD ["sh", "-c", "uvicorn simple_app:app --host 0.0.0.0 --port ${PORT:-8083}"]
