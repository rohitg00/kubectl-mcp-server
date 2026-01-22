import logging
import subprocess
from typing import Any, Dict, Optional

from mcp.types import ToolAnnotations

logger = logging.getLogger("mcp-server")


def register_diagnostics_tools(server, non_destructive: bool):
    """Register diagnostic and troubleshooting tools.

    Note: Pod-specific diagnostic tools (diagnose_pod_crash, detect_pending_pods,
    get_evicted_pods, get_pod_conditions, get_previous_logs) are in pods.py.
    This module contains additional diagnostic tools for namespace comparison and metrics.
    """

    @server.tool(
        annotations=ToolAnnotations(
            title="Compare Namespaces",
            readOnlyHint=True,
        ),
    )
    def compare_namespaces(namespace1: str, namespace2: str, resource_type: str = "deployment") -> Dict[str, Any]:
        """Compare resources between two namespaces."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            apps = client.AppsV1Api()
            v1 = client.CoreV1Api()

            def get_resources(ns, res_type):
                if res_type == "deployment":
                    items = apps.list_namespaced_deployment(ns).items
                    return {d.metadata.name: d.spec.replicas for d in items}
                elif res_type == "service":
                    items = v1.list_namespaced_service(ns).items
                    return {s.metadata.name: s.spec.type for s in items}
                elif res_type == "configmap":
                    items = v1.list_namespaced_config_map(ns).items
                    return {c.metadata.name: len(c.data or {}) for c in items}
                elif res_type == "secret":
                    items = v1.list_namespaced_secret(ns).items
                    return {s.metadata.name: s.type for s in items}
                else:
                    return {}

            res1 = get_resources(namespace1, resource_type)
            res2 = get_resources(namespace2, resource_type)

            only_in_ns1 = [name for name in res1 if name not in res2]
            only_in_ns2 = [name for name in res2 if name not in res1]
            in_both = [name for name in res1 if name in res2]

            differences = []
            for name in in_both:
                if res1[name] != res2[name]:
                    differences.append({
                        "name": name,
                        f"{namespace1}": res1[name],
                        f"{namespace2}": res2[name]
                    })

            return {
                "success": True,
                "resourceType": resource_type,
                "namespaces": [namespace1, namespace2],
                "summary": {
                    f"onlyIn_{namespace1}": len(only_in_ns1),
                    f"onlyIn_{namespace2}": len(only_in_ns2),
                    "inBoth": len(in_both),
                    "withDifferences": len(differences)
                },
                f"onlyIn_{namespace1}": only_in_ns1,
                f"onlyIn_{namespace2}": only_in_ns2,
                "differences": differences
            }
        except Exception as e:
            logger.error(f"Error comparing namespaces: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Pod Metrics",
            readOnlyHint=True,
        ),
    )
    def get_pod_metrics(namespace: Optional[str] = None, pod_name: Optional[str] = None) -> Dict[str, Any]:
        """Get pod resource usage metrics (requires metrics-server)."""
        try:
            cmd = ["kubectl", "top", "pods", "--no-headers"]
            if namespace:
                cmd.extend(["-n", namespace])
            else:
                cmd.append("-A")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip() or "Metrics server not available"}

            metrics = []
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split()
                if namespace and len(parts) >= 3:
                    name, cpu, memory = parts[0], parts[1], parts[2]
                    ns = namespace
                elif len(parts) >= 4:
                    ns, name, cpu, memory = parts[0], parts[1], parts[2], parts[3]
                else:
                    continue

                if pod_name and name != pod_name:
                    continue

                metrics.append({
                    "namespace": ns,
                    "pod": name,
                    "cpuUsage": cpu,
                    "memoryUsage": memory
                })

            return {
                "success": True,
                "count": len(metrics),
                "metrics": metrics
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Metrics retrieval timed out"}
        except Exception as e:
            logger.error(f"Error getting pod metrics: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Node Metrics",
            readOnlyHint=True,
        ),
    )
    def get_node_metrics() -> Dict[str, Any]:
        """Get node resource usage metrics (requires metrics-server)."""
        try:
            cmd = ["kubectl", "top", "nodes", "--no-headers"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip() or "Metrics server not available"}

            metrics = []
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 5:
                    metrics.append({
                        "node": parts[0],
                        "cpuUsage": parts[1],
                        "cpuPercent": parts[2],
                        "memoryUsage": parts[3],
                        "memoryPercent": parts[4]
                    })

            return {
                "success": True,
                "count": len(metrics),
                "metrics": metrics
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Metrics retrieval timed out"}
        except Exception as e:
            logger.error(f"Error getting node metrics: {e}")
            return {"success": False, "error": str(e)}
