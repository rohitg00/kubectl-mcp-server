# Security Policy

## Reporting a vulnerability

Report vulnerabilities privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability**. Do not open a public issue.

Include the affected version, transport (stdio or HTTP), safety mode, and a reproduction. You should get an acknowledgement within 7 days.

## Supported versions

| Version | Supported |
|---------|-----------|
| 2.x | Yes |
| < 2.0 | No. 1.24.0 and earlier fail to start on a fresh install (FastMCP 4) and lack the 2.0 hardening |

## Known advisories

| ID | Affected | Fixed | Summary |
|----|----------|-------|---------|
| CVE-2025-69902 | `kubectl-mcp-tool` <= 1.1.1 | 1.2.0 | OS command injection through `shell=True` in `minimal_wrapper.py` |
| (unassigned) | <= 1.24.0 | 2.0.0 | HTTP/SSE transports bound `0.0.0.0` by default with no authentication |
| (unassigned) | <= 1.24.0 | 2.0.0 | Identifier arguments starting with `-` were passed to kubectl/helm as flags (for example `--server`, `--kubeconfig`, `--post-renderer`) |
| (unassigned) | <= 1.24.0 | 2.0.0 | Secret masking was documented but never applied to tool output |

## Deployment guidance

- Keep the default `127.0.0.1` bind, or enable OAuth (`MCP_AUTH_ENABLED`, `MCP_AUTH_ISSUER`) before exposing HTTP.
- Grant the ServiceAccount or kubeconfig the least privilege you need, and run `--read-only` unless writes are required.
- Tools that read or write local paths (`kubectl_cp`, `helm_package`, `kind_export_logs`, ...) act on the server's filesystem. Over HTTP that is the host or pod running the server.
