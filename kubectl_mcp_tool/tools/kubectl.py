"""Generic kubectl tools that work for every resource kind, including CRDs."""

import re
import shutil
from typing import Any, Dict, List, Optional

from mcp.types import ToolAnnotations

from kubectl_mcp_tool.crd_detector import detect_crds
from kubectl_mcp_tool.tools.utils import run_kubectl as _run_kubectl
from kubectl_mcp_tool.toolsets import CRD_GROUP_TOOLSET, DEFAULT_TOOLSETS, TOOLSETS

MAX_OUTPUT_CHARS = 60_000
OUTPUT_FORMATS = {"table", "wide", "name", "yaml", "json"}
DURATION = re.compile(r"^\d+(s|m|h)$")
CLI_TOOLSETS = {"helm": "helm_dev", "kind": "kind", "vcluster": "vind", "istioctl": "istio", "hubble": "cilium", "cmctl": "certs"}

def _read(title: str) -> ToolAnnotations:
    return ToolAnnotations(title=title, readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)


def run_kubectl(args: List[str], context: str = "", timeout: int = 60) -> Dict[str, Any]:
    result = _run_kubectl(args, context, timeout)
    if not result["success"]:
        return {"success": False, "error": result["error"].strip() or "kubectl failed"}
    output = result["output"]
    response: Dict[str, Any] = {"success": True, "context": context or "current", "output": output[:MAX_OUTPUT_CHARS]}
    if len(output) > MAX_OUTPUT_CHARS:
        response.update(truncated=True, hint="Output truncated; narrow with name, namespace, label_selector or field_selector")
    return response


def _scope(namespace: Optional[str], all_namespaces: bool) -> List[str]:
    if all_namespaces:
        return ["--all-namespaces"]
    return ["-n", namespace] if namespace else []


def register_kubectl_tools(server, non_destructive: bool):
    from fastmcp import Context
    from kubectl_mcp_tool.elicit import check_write_allowed, confirm_destructive

    @server.tool(annotations=_read("Get Resources"))
    def kubectl_get(
        resource_type: str,
        name: Optional[str] = None,
        namespace: Optional[str] = None,
        all_namespaces: bool = False,
        label_selector: Optional[str] = None,
        field_selector: Optional[str] = None,
        output: str = "table",
        sort_by: Optional[str] = None,
        context: str = "",
    ) -> Dict[str, Any]:
        """List or get any Kubernetes resource, including custom resources (kubectl get).

        Args:
            resource_type: Kind, plural or short name, e.g. pods, deploy, svc, nodes, events, certificates.cert-manager.io
            name: A single resource name (omit to list)
            namespace: Namespace (omit for the context default; ignored for cluster-scoped kinds)
            all_namespaces: List across all namespaces
            label_selector: e.g. app=web,tier!=db
            field_selector: e.g. status.phase=Running or involvedObject.name=web-123
            output: table (default), wide, name, yaml or json. Secret values are always redacted
            sort_by: JSONPath to sort by, e.g. .lastTimestamp for events
            context: Kubernetes context (optional)
        """
        if output not in OUTPUT_FORMATS:
            return {"success": False, "error": f"output must be one of {sorted(OUTPUT_FORMATS)}"}
        args = ["get", resource_type, *([name] if name else []), *_scope(namespace, all_namespaces)]
        if label_selector:
            args += ["-l", label_selector]
        if field_selector:
            args += ["--field-selector", field_selector]
        if sort_by:
            args += ["--sort-by", sort_by]
        if output != "table":
            args += ["-o", output]
        return run_kubectl(args, context)

    @server.tool(annotations=_read("Container Logs"))
    def kubectl_logs(
        pod_name: str,
        namespace: str = "default",
        container: Optional[str] = None,
        tail: int = 200,
        previous: bool = False,
        since: Optional[str] = None,
        context: str = "",
    ) -> Dict[str, Any]:
        """Get container logs (kubectl logs).

        Args:
            pod_name: Pod name, or TYPE/NAME such as deployment/web to pick a pod of a workload
            namespace: Namespace of the pod
            container: Container name for multi-container pods
            tail: Lines from the end (default 200; -1 for all)
            previous: Logs of the previous, crashed container instance
            since: Only newer logs, e.g. 10m or 2h
            context: Kubernetes context (optional)
        """
        args = ["logs", pod_name, "-n", namespace, f"--tail={tail}"]
        if container:
            args += ["-c", container]
        if previous:
            args.append("--previous")
        if since:
            if not DURATION.match(since):
                return {"success": False, "error": "since must look like 30s, 10m or 2h"}
            args.append(f"--since={since}")
        return run_kubectl(args, context)

    @server.tool(annotations=_read("Resource Usage"))
    def kubectl_top(
        resource: str = "pods",
        name: Optional[str] = None,
        namespace: Optional[str] = None,
        all_namespaces: bool = False,
        containers: bool = False,
        sort_by: Optional[str] = None,
        context: str = "",
    ) -> Dict[str, Any]:
        """CPU and memory usage of pods or nodes from metrics-server (kubectl top).

        Args:
            resource: pods or nodes
            name: A single pod or node
            namespace: Namespace for pods
            all_namespaces: Pods across all namespaces
            containers: Per-container usage for pods
            sort_by: cpu or memory
            context: Kubernetes context (optional)
        """
        if resource not in ("pods", "nodes"):
            return {"success": False, "error": "resource must be pods or nodes"}
        if sort_by and sort_by not in ("cpu", "memory"):
            return {"success": False, "error": "sort_by must be cpu or memory"}
        args = ["top", resource, *([name] if name else [])]
        if resource == "pods":
            args += _scope(namespace, all_namespaces)
            if containers:
                args.append("--containers")
        if sort_by:
            args += ["--sort-by", sort_by]
        return run_kubectl(args, context)

    @server.tool(annotations=ToolAnnotations(title="Scale Workload", readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=True))
    async def kubectl_scale(
        resource_type: str,
        name: str,
        replicas: int,
        namespace: str = "default",
        context: str = "",
        ctx: Context = None,
    ) -> Dict[str, Any]:
        """Scale a deployment, statefulset, replicaset or any scalable resource (kubectl scale).

        Args:
            resource_type: deployment, statefulset, replicaset, or another kind with a scale subresource
            name: Resource name
            replicas: Desired replica count (0 stops the workload and needs confirmation in confirm mode)
            namespace: Namespace
            context: Kubernetes context (optional)
        """
        if replicas < 0:
            return {"success": False, "error": "replicas must be >= 0"}
        blocked = await check_write_allowed()
        if not blocked and replicas == 0:
            blocked = await confirm_destructive(ctx, "Scale to zero", f"{resource_type}/{name}", namespace)
        if blocked:
            return blocked
        return run_kubectl(["scale", f"{resource_type}/{name}", f"--replicas={replicas}", "-n", namespace], context)

    @server.tool(annotations=_read("Detect Ecosystem"))
    def detect_ecosystem(context: str = "") -> Dict[str, Any]:
        """Detect installed operators (Flux, Argo CD, cert-manager, Kyverno, Istio, ...) and local CLIs, and report
        which toolsets or dedicated MCP servers cover them.

        Args:
            context: Kubernetes context (optional)
        """
        enabled = set(getattr(server, "enabled", DEFAULT_TOOLSETS))
        crds = detect_crds(context, force_refresh=True)
        installed = sorted(group for group, present in crds.items() if present)
        clis = sorted(cli for cli in CLI_TOOLSETS if shutil.which(cli))
        relevant = sorted({CRD_GROUP_TOOLSET[g] for g in installed} | {CLI_TOOLSETS[c] for c in clis})
        return {
            "success": True,
            "context": context or "current",
            "installed_operators": installed,
            "local_clis": clis,
            "toolsets": {
                name: {
                    "enabled": name in enabled,
                    "description": TOOLSETS[name].description,
                    "official_mcp_servers": TOOLSETS[name].official_servers,
                }
                for name in relevant
            },
            "enable_hint": "Restart the server with --toolsets default,<name> (or MCP_TOOLSETS) to load a toolset",
        }
