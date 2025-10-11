FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn python-multipart

# Copy application code
COPY . .

# Expose port
EXPOSE 8085

# Run the application
CMD ["uvicorn", "minimal_app:app", "--host", "0.0.0.0", "--port", "8085"]