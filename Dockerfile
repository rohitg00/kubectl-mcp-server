# syntax=docker/dockerfile:1.7

FROM python:3.13-slim AS build
WORKDIR /src
COPY setup.py README.md ./
COPY kubectl_mcp_tool ./kubectl_mcp_tool
RUN pip install --no-cache-dir --upgrade pip \
 && pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.13-slim AS tools
ARG TARGETARCH
ARG KUBECTL_VERSION=v1.37.1
ARG HELM_VERSION=v3.22.1
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /tmp/tools
RUN curl -fsSLO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl" \
 && curl -fsSLO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${TARGETARCH}/kubectl.sha256" \
 && echo "$(cat kubectl.sha256)  kubectl" | sha256sum -c - \
 && install -m 0755 kubectl /usr/local/bin/kubectl
RUN HELM_TGZ="helm-${HELM_VERSION}-linux-${TARGETARCH}.tar.gz" \
 && curl -fsSLO "https://get.helm.sh/${HELM_TGZ}" \
 && curl -fsSLO "https://get.helm.sh/${HELM_TGZ}.sha256sum" \
 && sha256sum -c "${HELM_TGZ}.sha256sum" \
 && tar -xzf "${HELM_TGZ}" \
 && install -m 0755 "linux-${TARGETARCH}/helm" /usr/local/bin/helm

FROM python:3.13-slim
ARG VERSION=2.0.0
LABEL org.opencontainers.image.title="kubectl-mcp-server" \
      org.opencontainers.image.description="Stateless MCP (2026-07-28) server for Kubernetes" \
      org.opencontainers.image.source="https://github.com/rohitg00/kubectl-mcp-server" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="${VERSION}"

RUN groupadd --gid 10001 mcp \
 && useradd --uid 10001 --gid 10001 --create-home --home-dir /home/mcp --shell /usr/sbin/nologin mcp

COPY --from=tools /usr/local/bin/kubectl /usr/local/bin/helm /usr/local/bin/
COPY --from=build /wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/*.whl && rm -rf /tmp/wheels

USER 10001:10001
WORKDIR /home/mcp

ENV HOME=/home/mcp \
    PYTHONUNBUFFERED=1 \
    MCP_SERVER_TRANSPORT=stdio \
    MCP_SERVER_HOST=0.0.0.0 \
    MCP_SERVER_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,sys,urllib.request; os.environ.get('MCP_SERVER_TRANSPORT','stdio')=='stdio' or urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('MCP_SERVER_PORT','8000')+'/health', timeout=4)" || exit 1

ENTRYPOINT ["kubectl-mcp"]
