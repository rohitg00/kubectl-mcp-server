# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies (if needed for pip packages or build tools)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy only requirements first for better caching during builds
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose port 8080 for SSE transport
EXPOSE 8080

# Use environment variables for flexibility (optional)
ENV TRANSPORT=sse
ENV PORT=8080

# By default, run the MCP server with SSE transport on port 8080
CMD ["python", "run_server.py", "--transport", "sse", "--port", "8080"]
