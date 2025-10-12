FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi==0.118.0 \
    uvicorn==0.24.0 \
    google-cloud-firestore==2.13.1 \
    google-cloud-aiplatform==1.119.0 \
    google-auth==2.23.4 \
    pydantic==2.5.0 \
    email-validator==2.1.0 \
    PyJWT==2.8.0

# Copy packages and application code
COPY ./packages ./packages
COPY ./services/api/chat ./

# Expose port
EXPOSE 8081

# Run the application
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8081}"]
