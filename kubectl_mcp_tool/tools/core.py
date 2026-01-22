import logging
from typing import Any, Dict, List, Optional

from mcp.types import ToolAnnotations

logger = logging.getLogger("mcp-server")


def register_core_tools(server, non_destructive: bool):
    """Register core Kubernetes resource tools."""

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Namespaces",
            readOnlyHint=True,
        ),
    )
    def get_namespaces() -> Dict[str, Any]:
        """Get all Kubernetes namespaces."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()
            namespaces = v1.list_namespace()
            return {
                "success": True,
                "namespaces": [ns.metadata.name for ns in namespaces.items]
            }
        except Exception as e:
            logger.error(f"Error getting namespaces: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Services",
            readOnlyHint=True,
        ),
    )
    def get_services(namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get all services in the specified namespace."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()
            if namespace:
                services = v1.list_namespaced_service(namespace)
            else:
                services = v1.list_service_for_all_namespaces()
            return {
                "success": True,
                "services": [
                    {
                        "name": svc.metadata.name,
                        "namespace": svc.metadata.namespace,
                        "type": svc.spec.type,
                        "cluster_ip": svc.spec.cluster_ip
                    } for svc in services.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Nodes",
            readOnlyHint=True,
        ),
    )
    def get_nodes() -> Dict[str, Any]:
        """Get all nodes in the cluster."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()
            nodes = v1.list_node()
            return {
                "success": True,
                "nodes": [
                    {
                        "name": node.metadata.name,
                        "status": (
                            "Ready"
                            if any(
                                cond.type == "Ready" and cond.status == "True"
                                for cond in node.status.conditions
                            )
                            else "NotReady"
                        ),
                        "addresses": [
                            addr.address for addr in node.status.addresses
                        ],
                    }
                    for node in nodes.items
                ],
            }
        except Exception as e:
            logger.error(f"Error getting nodes: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get ConfigMaps",
            readOnlyHint=True,
        ),
    )
    def get_configmaps(namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get all ConfigMaps in the specified namespace."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()
            if namespace:
                cms = v1.list_namespaced_config_map(namespace)
            else:
                cms = v1.list_config_map_for_all_namespaces()
            return {
                "success": True,
                "configmaps": [
                    {
                        "name": cm.metadata.name,
                        "namespace": cm.metadata.namespace,
                        "data": cm.data
                    } for cm in cms.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting ConfigMaps: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Secrets",
            readOnlyHint=True,
        ),
    )
    def get_secrets(namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get all Secrets in the specified namespace."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()
            if namespace:
                secrets = v1.list_namespaced_secret(namespace)
            else:
                secrets = v1.list_secret_for_all_namespaces()
            return {
                "success": True,
                "secrets": [
                    {
                        "name": secret.metadata.name,
                        "namespace": secret.metadata.namespace,
                        "type": secret.type
                    } for secret in secrets.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting Secrets: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Events",
            readOnlyHint=True,
        ),
    )
    def get_events(namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get Kubernetes events."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()
            if namespace:
                events = v1.list_namespaced_event(namespace)
            else:
                events = v1.list_event_for_all_namespaces()
            return {
                "success": True,
                "events": [
                    {
                        "name": event.metadata.name,
                        "namespace": event.metadata.namespace,
                        "type": event.type,
                        "reason": event.reason,
                        "message": event.message,
                        "timestamp": event.last_timestamp.isoformat() if event.last_timestamp else None
                    } for event in events.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Resource Usage",
            readOnlyHint=True,
        ),
    )
    def get_resource_usage(namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get resource usage metrics for pods."""
        try:
            import subprocess
            cmd = ["kubectl", "top", "pods"]
            if namespace:
                cmd.extend(["-n", namespace])
            else:
                cmd.append("--all-namespaces")
            cmd.append("--no-headers")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return {"success": False, "error": result.stderr or "Failed to get metrics"}

            pods = []
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split()
                if namespace:
                    if len(parts) >= 3:
                        pods.append({
                            "name": parts[0],
                            "cpu": parts[1],
                            "memory": parts[2]
                        })
                else:
                    if len(parts) >= 4:
                        pods.append({
                            "namespace": parts[0],
                            "name": parts[1],
                            "cpu": parts[2],
                            "memory": parts[3]
                        })

            return {"success": True, "pods": pods}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Metrics retrieval timed out"}
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Service Accounts",
            readOnlyHint=True,
        ),
    )
    def get_service_accounts(namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get service accounts in a namespace or cluster-wide."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()

            if namespace:
                sas = v1.list_namespaced_service_account(namespace)
            else:
                sas = v1.list_service_account_for_all_namespaces()

            return {
                "success": True,
                "serviceAccounts": [
                    {
                        "name": sa.metadata.name,
                        "namespace": sa.metadata.namespace,
                        "secrets": [s.name for s in (sa.secrets or [])],
                        "imagePullSecrets": [s.name for s in (sa.image_pull_secrets or [])],
                        "automountToken": sa.automount_service_account_token
                    }
                    for sa in sas.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting service accounts: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Custom Resource Definitions",
            readOnlyHint=True,
        ),
    )
    def get_crds(group: Optional[str] = None) -> Dict[str, Any]:
        """Get Custom Resource Definitions in the cluster."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            api = client.ApiextensionsV1Api()

            crds = api.list_custom_resource_definition()

            result = []
            for crd in crds.items:
                if group and crd.spec.group != group:
                    continue
                result.append({
                    "name": crd.metadata.name,
                    "group": crd.spec.group,
                    "version": crd.spec.versions[0].name if crd.spec.versions else None,
                    "scope": crd.spec.scope,
                    "kind": crd.spec.names.kind,
                    "plural": crd.spec.names.plural,
                    "established": any(
                        c.type == "Established" and c.status == "True"
                        for c in (crd.status.conditions or [])
                    )
                })

            return {"success": True, "crds": result}
        except Exception as e:
            logger.error(f"Error getting CRDs: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Resource Quotas",
            readOnlyHint=True,
        ),
    )
    def get_resource_quotas(namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get resource quotas for namespaces."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()

            if namespace:
                quotas = v1.list_namespaced_resource_quota(namespace)
            else:
                quotas = v1.list_resource_quota_for_all_namespaces()

            return {
                "success": True,
                "quotas": [
                    {
                        "name": q.metadata.name,
                        "namespace": q.metadata.namespace,
                        "hard": q.status.hard,
                        "used": q.status.used
                    }
                    for q in quotas.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting resource quotas: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Limit Ranges",
            readOnlyHint=True,
        ),
    )
    def get_limit_ranges(namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get limit ranges for namespaces."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()

            if namespace:
                limits = v1.list_namespaced_limit_range(namespace)
            else:
                limits = v1.list_limit_range_for_all_namespaces()

            return {
                "success": True,
                "limitRanges": [
                    {
                        "name": lr.metadata.name,
                        "namespace": lr.metadata.namespace,
                        "limits": [
                            {
                                "type": item.type,
                                "default": item.default,
                                "defaultRequest": item.default_request,
                                "max": item.max,
                                "min": item.min
                            }
                            for item in (lr.spec.limits or [])
                        ]
                    }
                    for lr in limits.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting limit ranges: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Priority Classes",
            readOnlyHint=True,
        ),
    )
    def get_priority_classes() -> Dict[str, Any]:
        """Get priority classes in the cluster."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            api = client.SchedulingV1Api()

            pcs = api.list_priority_class()

            return {
                "success": True,
                "priorityClasses": [
                    {
                        "name": pc.metadata.name,
                        "value": pc.value,
                        "globalDefault": pc.global_default,
                        "description": pc.description,
                        "preemptionPolicy": pc.preemption_policy
                    }
                    for pc in pcs.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting priority classes: {e}")
            return {"success": False, "error": str(e)}
