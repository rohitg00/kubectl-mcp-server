import logging
import subprocess
from typing import Any, Dict, List, Optional

from mcp.types import ToolAnnotations

from ..k8s_config import get_k8s_client, get_networking_client

logger = logging.getLogger("mcp-server")


def _get_kubectl_context_args(context: str) -> List[str]:
    """Get kubectl context arguments if context is specified."""
    if context:
        return ["--context", context]
    return []


def register_networking_tools(server, non_destructive: bool):
    """Register networking-related tools."""

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Ingress Resources",
            readOnlyHint=True,
        ),
    )
    def get_ingress(
        namespace: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get Ingress resources in a namespace or cluster-wide.

        Args:
            namespace: Namespace to list ingresses from (all namespaces if not specified)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            networking = get_networking_client(context)

            if namespace:
                ingresses = networking.list_namespaced_ingress(namespace)
            else:
                ingresses = networking.list_ingress_for_all_namespaces()

            return {
                "success": True,
                "context": context or "current",
                "ingresses": [
                    {
                        "name": ing.metadata.name,
                        "namespace": ing.metadata.namespace,
                        "ingressClassName": ing.spec.ingress_class_name,
                        "rules": [
                            {
                                "host": rule.host,
                                "paths": [
                                    {
                                        "path": path.path,
                                        "pathType": path.path_type,
                                        "backend": {
                                            "serviceName": path.backend.service.name if path.backend.service else None,
                                            "servicePort": path.backend.service.port.number if path.backend.service and path.backend.service.port else None
                                        }
                                    }
                                    for path in (rule.http.paths if rule.http else [])
                                ]
                            }
                            for rule in (ing.spec.rules or [])
                        ],
                        "tls": [
                            {"hosts": tls.hosts, "secretName": tls.secret_name}
                            for tls in (ing.spec.tls or [])
                        ] if ing.spec.tls else None
                    }
                    for ing in ingresses.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting Ingresses: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Endpoints",
            readOnlyHint=True,
        ),
    )
    def get_endpoints(
        namespace: Optional[str] = None,
        service_name: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get Endpoints for services.

        Args:
            namespace: Namespace to list endpoints from (all namespaces if not specified)
            service_name: Filter by specific service name
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            v1 = get_k8s_client(context)

            if namespace:
                endpoints = v1.list_namespaced_endpoints(namespace)
            else:
                endpoints = v1.list_endpoints_for_all_namespaces()

            result = []
            for ep in endpoints.items:
                if service_name and ep.metadata.name != service_name:
                    continue

                addresses = []
                for subset in (ep.subsets or []):
                    for addr in (subset.addresses or []):
                        for port in (subset.ports or []):
                            addresses.append({
                                "ip": addr.ip,
                                "port": port.port,
                                "protocol": port.protocol,
                                "targetRef": {
                                    "kind": addr.target_ref.kind,
                                    "name": addr.target_ref.name
                                } if addr.target_ref else None
                            })

                result.append({
                    "name": ep.metadata.name,
                    "namespace": ep.metadata.namespace,
                    "addresses": addresses
                })

            return {
                "success": True,
                "context": context or "current",
                "endpoints": result
            }
        except Exception as e:
            logger.error(f"Error getting Endpoints: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Diagnose Network Connectivity",
            readOnlyHint=True,
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
            except:
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

    @server.tool(
        annotations=ToolAnnotations(
            title="Port Forward",
            destructiveHint=True,
        ),
    )
    def port_forward(
        pod_name: str,
        local_port: int,
        pod_port: int,
        namespace: Optional[str] = "default",
        context: str = ""
    ) -> Dict[str, Any]:
        """Start port forwarding to a pod (note: this starts a background process).

        Args:
            pod_name: Name of the pod to forward to
            local_port: Local port to listen on
            pod_port: Pod port to forward to
            namespace: Namespace of the pod
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            import os
            ctx_args = " ".join(_get_kubectl_context_args(context))
            cmd = f"kubectl {ctx_args} port-forward {pod_name} {local_port}:{pod_port} -n {namespace} &"
            os.system(cmd)
            return {
                "success": True,
                "context": context or "current",
                "message": f"Port forwarding started: localhost:{local_port} -> {pod_name}:{pod_port}",
                "note": "Port forwarding is running in background. Use 'pkill -f port-forward' to stop."
            }
        except Exception as e:
            logger.error(f"Error setting up port forward: {e}")
            return {"success": False, "error": str(e)}
