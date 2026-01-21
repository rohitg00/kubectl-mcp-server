FROM --platform=$TARGETPLATFORM python:3.11-slim
ARG TARGETARCH
# Build: 2026-01-21 - Rebuild Docker image with proper tags

# Install system dependencies and tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        curl \
        gnupg \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Install kubectl (pinned version for reliability) and helm (v3)
# -----------------------------------------------------------------------------
ARG KUBECTL_VERSION=v1.32.0
RUN curl -fsSL -o /usr/local/bin/kubectl \
    "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl" && \
    chmod +x /usr/local/bin/kubectl && \
    kubectl version --client --output=yaml

# Install Helm
RUN curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

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

# Install the package
RUN pip install --no-cache-dir -e .

# Expose server port (for SSE/HTTP modes)
EXPOSE 8000

# Environment variables (can be overridden)
# TRANSPORT: "stdio" (default for Docker MCP Toolkit), "sse", "http", "streamable-http"
# HOST: Bind address for network transports
# PORT: Port for network transports
ENV TRANSPORT=stdio \
    HOST=0.0.0.0 \
    PORT=8000 \
    PYTHONUNBUFFERED=1

# Health check for network modes
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD if [ "$TRANSPORT" != "stdio" ]; then curl -f http://localhost:${PORT}/health || exit 1; else exit 0; fi

# Default entrypoint for Docker MCP Toolkit compatibility (stdio transport)
# For SSE/HTTP modes, override with: --transport sse --host 0.0.0.0 --port 8000
ENTRYPOINT ["python", "-m", "kubectl_mcp_tool.mcp_server"]

# Default to stdio for Docker MCP Toolkit compatibility
# Override with: docker run ... <image> --transport sse --port 8000
CMD ["--transport", "stdio"]
