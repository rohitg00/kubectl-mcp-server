import logging
import subprocess
from typing import Any, Dict, Optional

from mcp.types import ToolAnnotations

from ..k8s_config import get_k8s_client, _get_kubectl_context_args

logger = logging.getLogger("mcp-server")


def register_networking_tools(server: "FastMCP", non_destructive: bool):
    """Register networking-related tools."""

    @server.tool(
        annotations=ToolAnnotations(
            title="Diagnose Network Connectivity",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def diagnose_network_connectivity(
        source_pod: str,
        target: str,
        source_namespace: str = "default",
        port: Optional[int] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Diagnose network connectivity between pods or to external endpoints.

        Args:
            source_pod: Name of the pod to test from
            target: Target hostname or IP to test connectivity to
            source_namespace: Namespace of the source pod
            port: Optional port number to test
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            results = {"success": True, "context": context or "current", "tests": []}
            ctx_args = _get_kubectl_context_args(context)

            # Test DNS resolution
            dns_cmd = ["kubectl"] + ctx_args + ["exec", source_pod, "-n", source_namespace, "--", "nslookup", target]
            dns_result = subprocess.run(dns_cmd, capture_output=True, text=True, timeout=30)
            results["tests"].append({
                "test": "DNS Resolution",
                "passed": dns_result.returncode == 0,
                "output": dns_result.stdout if dns_result.returncode == 0 else dns_result.stderr
            })

            # Test connectivity
            if port:
                conn_cmd = ["kubectl"] + ctx_args + ["exec", source_pod, "-n", source_namespace, "--",
                           "nc", "-zv", "-w", "5", target, str(port)]
            else:
                conn_cmd = ["kubectl"] + ctx_args + ["exec", source_pod, "-n", source_namespace, "--",
                           "ping", "-c", "3", target]

            conn_result = subprocess.run(conn_cmd, capture_output=True, text=True, timeout=30)
            results["tests"].append({
                "test": f"Connectivity to {target}" + (f":{port}" if port else ""),
                "passed": conn_result.returncode == 0,
                "output": conn_result.stdout if conn_result.returncode == 0 else conn_result.stderr
            })

            results["allPassed"] = all(t["passed"] for t in results["tests"])
            return results
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Network test timed out"}
        except Exception as e:
            logger.error(f"Error diagnosing network: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Check DNS Resolution",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def check_dns_resolution(
        hostname: str,
        namespace: str = "default",
        pod_name: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Check DNS resolution from within the cluster.

        Args:
            hostname: Hostname to resolve
            namespace: Namespace to find a pod in
            pod_name: Specific pod to use for testing (optional)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            if not pod_name:
                # Find a running pod in the namespace
                v1 = get_k8s_client(context)
                pods = v1.list_namespaced_pod(namespace, field_selector="status.phase=Running")
                if not pods.items:
                    return {"success": False, "error": f"No running pods in namespace {namespace}"}
                pod_name = pods.items[0].metadata.name

            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["exec", pod_name, "-n", namespace, "--", "nslookup", hostname]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            return {
                "success": result.returncode == 0,
                "context": context or "current",
                "hostname": hostname,
                "pod": pod_name,
                "namespace": namespace,
                "output": result.stdout if result.returncode == 0 else result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "DNS resolution timed out"}
        except Exception as e:
            logger.error(f"Error checking DNS: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Trace Service to Pods",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def trace_service_chain(
        service_name: str,
        namespace: str = "default",
        context: str = ""
    ) -> Dict[str, Any]:
        """Trace the connection chain from service to pods.

        Args:
            service_name: Name of the service to trace
            namespace: Namespace of the service
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            v1 = get_k8s_client(context)

            # Get service
            service = v1.read_namespaced_service(service_name, namespace)

            # Get endpoints
            try:
                endpoints = v1.read_namespaced_endpoints(service_name, namespace)
            except Exception:
                endpoints = None

            # Get pods matching selector
            selector = service.spec.selector
            if selector:
                label_selector = ",".join([f"{k}={v}" for k, v in selector.items()])
                pods = v1.list_namespaced_pod(namespace, label_selector=label_selector)
            else:
                pods = None

            result = {
                "success": True,
                "context": context or "current",
                "service": {
                    "name": service.metadata.name,
                    "type": service.spec.type,
                    "clusterIP": service.spec.cluster_ip,
                    "ports": [
                        {
                            "name": p.name,
                            "port": p.port,
                            "targetPort": str(p.target_port),
                            "protocol": p.protocol
                        }
                        for p in (service.spec.ports or [])
                    ],
                    "selector": selector
                },
                "endpoints": [],
                "pods": []
            }

            if endpoints:
                for subset in (endpoints.subsets or []):
                    for addr in (subset.addresses or []):
                        for port in (subset.ports or []):
                            result["endpoints"].append({
                                "ip": addr.ip,
                                "port": port.port,
                                "podName": addr.target_ref.name if addr.target_ref else None
                            })

            if pods:
                result["pods"] = [
                    {
                        "name": p.metadata.name,
                        "status": p.status.phase,
                        "podIP": p.status.pod_ip,
                        "ready": all(
                            c.ready for c in (p.status.container_statuses or [])
                        )
                    }
                    for p in pods.items
                ]

            return result
        except Exception as e:
            logger.error(f"Error tracing service chain: {e}")
            return {"success": False, "error": str(e)}

