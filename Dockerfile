FROM --platform=$TARGETPLATFORM python:3.11-slim
ARG TARGETARCH

# Install system dependencies and tools (curl, gz, gnupg, ca-certificates) and build essentials for some Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        curl \
        gnupg \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Install kubectl (latest stable) and helm (v3)
# -----------------------------------------------------------------------------
RUN curl -sSL https://dl.k8s.io/release/$(curl -sSL https://dl.k8s.io/release/stable.txt)/bin/linux/${TARGETARCH}/kubectl \
    -o /usr/local/bin/kubectl && \
    chmod +x /usr/local/bin/kubectl && \
    kubectl version --client --output=yaml

# Install Helm
RUN curl -fsSL https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash

# -----------------------------------------------------------------------------
# Set up application
# -----------------------------------------------------------------------------
WORKDIR /app

# Copy requirements and install Python deps first (leverage Docker layer cache)
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the codebase
COPY . .

# Expose server port
EXPOSE 8000

# Environment variables (can be overridden)
# TRANSPORT: Transport mode - "sse", "http", "streamable-http", or "stdio"
# HOST: Bind address - use "0.0.0.0" for Docker to allow external connections
# PORT: Port number for SSE/HTTP transports
ENV TRANSPORT=sse \
    HOST=0.0.0.0 \
    PORT=8000

# Run the server
# Note: --host 0.0.0.0 is REQUIRED for Docker to accept external connections.
# The container binds to all interfaces so that port mapping (-p) works correctly.
CMD ["python", "run_server.py", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
