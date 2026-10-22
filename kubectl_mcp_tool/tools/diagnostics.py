import logging
from typing import Any, Dict

from mcp.types import ToolAnnotations

from ..k8s_config import get_k8s_client, get_apps_client

logger = logging.getLogger("mcp-server")


def register_diagnostics_tools(server: "FastMCP", non_destructive: bool):
    """Register diagnostic and troubleshooting tools.

    Note: Pod-specific diagnostic tools (diagnose_pod_crash, detect_pending_pods,
    get_evicted_pods, get_pod_conditions, get_previous_logs) are in pods.py.
    This module contains additional diagnostic tools for namespace comparison and metrics.
    """

    @server.tool(
        annotations=ToolAnnotations(
            title="Compare Namespaces",
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )
    def compare_namespaces(namespace1: str, namespace2: str, resource_type: str = "deployment", context: str = "") -> Dict[str, Any]:
        """Compare resources between two namespaces.

        Args:
            namespace1: First namespace to compare
            namespace2: Second namespace to compare
            resource_type: Type of resource to compare (deployment, service, configmap, secret)
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            apps = get_apps_client(context)
            v1 = get_k8s_client(context)

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
                "context": context or "current",
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

