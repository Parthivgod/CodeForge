FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create temp directory for uploads
RUN mkdir -p /app/temp

# Copy and set permissions for startup script
COPY start.sh .
RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Run the application
CMD ["bash", "start.sh"]
