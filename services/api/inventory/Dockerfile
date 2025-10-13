FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    fastapi==0.118.0 \
    uvicorn==0.24.0 \
    google-cloud-firestore==2.13.1 \
    google-cloud-storage==2.10.0 \
    google-cloud-pubsub==2.18.4 \
    google-cloud-secret-manager==2.16.4 \
    google-auth==2.23.4 \
    google-auth-oauthlib==1.1.0 \
    google-auth-httplib2==0.1.1 \
    google-api-python-client==2.108.0 \
    google-cloud-aiplatform==1.119.0 \
    google-cloud-documentai==3.6.0 \
    pydantic==2.5.0 \
    python-multipart==0.0.6 \
    requests==2.32.5 \
    PyJWT==2.8.0

# Copy the entire project structure
COPY ./packages ./packages
COPY ./services/api/inventory ./

# Expose port
EXPOSE 8082

# Run the application
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8082}"]
