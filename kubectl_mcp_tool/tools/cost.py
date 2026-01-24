import logging
import subprocess
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp.types import ToolAnnotations

from ..k8s_config import get_k8s_client, get_apps_client

logger = logging.getLogger("mcp-server")


def _get_kubectl_context_args(context: str) -> List[str]:
    """Get kubectl context arguments if context is specified."""
    if context:
        return ["--context", context]
    return []


def _parse_cpu(cpu_str: str) -> int:
    """Parse CPU string to millicores."""
    try:
        cpu_str = str(cpu_str)
        if cpu_str.endswith("m"):
            return int(cpu_str[:-1])
        elif cpu_str.endswith("n"):
            return int(cpu_str[:-1]) // 1000000
        else:
            return int(float(cpu_str) * 1000)
    except:
        return 0


def _parse_memory(mem_str: str) -> int:
    """Parse memory string to bytes."""
    try:
        mem_str = str(mem_str)
        if mem_str.endswith("Ki"):
            return int(mem_str[:-2]) * 1024
        elif mem_str.endswith("Mi"):
            return int(mem_str[:-2]) * 1024 * 1024
        elif mem_str.endswith("Gi"):
            return int(mem_str[:-2]) * 1024 * 1024 * 1024
        elif mem_str.endswith("K"):
            return int(mem_str[:-1]) * 1000
        elif mem_str.endswith("M"):
            return int(mem_str[:-1]) * 1000000
        elif mem_str.endswith("G"):
            return int(mem_str[:-1]) * 1000000000
        else:
            return int(mem_str)
    except:
        return 0


def _calculate_available(hard: str, used: str) -> str:
    """Calculate available resources from hard and used values."""
    try:
        hard_num = int(re.sub(r'[^\d]', '', str(hard)) or 0)
        used_num = int(re.sub(r'[^\d]', '', str(used)) or 0)
        suffix = re.sub(r'[\d]', '', str(hard))
        return f"{max(0, hard_num - used_num)}{suffix}"
    except:
        return "N/A"


def register_cost_tools(server, non_destructive: bool):
    """Register cost and resource optimization tools."""

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Resource Recommendations",
            readOnlyHint=True,
        ),
    )
    def get_resource_recommendations(
        namespace: Optional[str] = None,
        resource_type: str = "all",
        context: str = ""
    ) -> Dict[str, Any]:
        """Analyze resource usage and provide optimization recommendations for pods/deployments.

        Args:
            namespace: Target namespace (optional, all namespaces if not specified)
            resource_type: Type of resource to analyze
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            from kubernetes import client
            v1 = get_k8s_client(context)

            recommendations = []

            if namespace:
                pods = v1.list_namespaced_pod(namespace).items
            else:
                pods = v1.list_pod_for_all_namespaces().items

            for pod in pods:
                if pod.status.phase != "Running":
                    continue

                for container in pod.spec.containers:
                    issues = []
                    suggestions = []

                    resources = container.resources or client.V1ResourceRequirements()
                    requests = resources.requests or {}
                    limits = resources.limits or {}

                    if not requests:
                        issues.append("No resource requests defined")
                        suggestions.append("Set CPU/memory requests for better scheduling")

                    if not limits:
                        issues.append("No resource limits defined")
                        suggestions.append("Set CPU/memory limits to prevent resource exhaustion")

                    if requests and limits:
                        cpu_req = requests.get("cpu", "0")
                        cpu_lim = limits.get("cpu", "0")
                        mem_req = requests.get("memory", "0")
                        mem_lim = limits.get("memory", "0")

                        if cpu_req == cpu_lim and mem_req == mem_lim:
                            issues.append("Requests equal limits (Guaranteed QoS)")
                            suggestions.append("Consider Burstable QoS for non-critical workloads")

                    if not container.liveness_probe:
                        issues.append("No liveness probe")
                        suggestions.append("Add liveness probe for automatic recovery")

                    if not container.readiness_probe:
                        issues.append("No readiness probe")
                        suggestions.append("Add readiness probe for traffic management")

                    if issues:
                        recommendations.append({
                            "pod": pod.metadata.name,
                            "namespace": pod.metadata.namespace,
                            "container": container.name,
                            "issues": issues,
                            "suggestions": suggestions,
                            "currentResources": {
                                "requests": requests,
                                "limits": limits
                            }
                        })

            return {
                "success": True,
                "context": context or "current",
                "totalAnalyzed": len(pods),
                "issuesFound": len(recommendations),
                "recommendations": recommendations[:50]
            }
        except Exception as e:
            logger.error(f"Error getting resource recommendations: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Idle Resources",
            readOnlyHint=True,
        ),
    )
    def get_idle_resources(
        namespace: Optional[str] = None,
        cpu_threshold: float = 10.0,
        memory_threshold: float = 10.0,
        context: str = ""
    ) -> Dict[str, Any]:
        """Find underutilized pods using less than threshold percentage of requested resources.

        Args:
            namespace: Target namespace (optional, all namespaces if not specified)
            cpu_threshold: CPU usage threshold percentage
            memory_threshold: Memory usage threshold percentage
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["top", "pods", "--no-headers"]
            if namespace:
                cmd.extend(["-n", namespace])
            else:
                cmd.append("-A")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip() or "Metrics server not available"}

            idle_pods = []
            lines = result.stdout.strip().split("\n")

            for line in lines:
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    if namespace:
                        pod_name, cpu_usage, mem_usage = parts[0], parts[1], parts[2]
                        ns = namespace
                    elif len(parts) >= 4:
                        ns, pod_name, cpu_usage, mem_usage = parts[0], parts[1], parts[2], parts[3]
                    else:
                        continue

                    cpu_val = int(re.sub(r'[^\d]', '', cpu_usage) or 0)
                    mem_val = int(re.sub(r'[^\d]', '', mem_usage) or 0)

                    if cpu_val < cpu_threshold or mem_val < memory_threshold:
                        idle_pods.append({
                            "namespace": ns,
                            "pod": pod_name,
                            "cpuUsage": cpu_usage,
                            "memoryUsage": mem_usage,
                            "recommendation": "Consider scaling down or consolidating"
                        })

            return {
                "success": True,
                "context": context or "current",
                "thresholds": {
                    "cpu": f"{cpu_threshold}%",
                    "memory": f"{memory_threshold}%"
                },
                "idleCount": len(idle_pods),
                "idlePods": idle_pods[:50]
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Metrics retrieval timed out"}
        except Exception as e:
            logger.error(f"Error finding idle resources: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Resource Quotas Usage",
            readOnlyHint=True,
        ),
    )
    def get_resource_quotas_usage(namespace: Optional[str] = None, context: str = "") -> Dict[str, Any]:
        """Show resource quota usage and availability across namespaces.

        Args:
            namespace: Target namespace (optional, all namespaces if not specified)
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            v1 = get_k8s_client(context)

            if namespace:
                quotas = v1.list_namespaced_resource_quota(namespace).items
            else:
                quotas = v1.list_resource_quota_for_all_namespaces().items

            quota_usage = []
            for quota in quotas:
                hard = quota.status.hard or {}
                used = quota.status.used or {}

                resources = []
                for resource_name, hard_val in hard.items():
                    used_val = used.get(resource_name, "0")
                    resources.append({
                        "resource": resource_name,
                        "hard": hard_val,
                        "used": used_val,
                        "available": _calculate_available(hard_val, used_val)
                    })

                quota_usage.append({
                    "name": quota.metadata.name,
                    "namespace": quota.metadata.namespace,
                    "resources": resources
                })

            return {
                "success": True,
                "context": context or "current",
                "count": len(quota_usage),
                "quotas": quota_usage
            }
        except Exception as e:
            logger.error(f"Error getting quota usage: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Cost Analysis",
            readOnlyHint=True,
        ),
    )
    def get_cost_analysis(namespace: Optional[str] = None, context: str = "") -> Dict[str, Any]:
        """Analyze resource costs by namespace and workload based on resource requests.

        Args:
            namespace: Target namespace (optional, all namespaces if not specified)
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            v1 = get_k8s_client(context)

            if namespace:
                pods = v1.list_namespaced_pod(namespace).items
            else:
                pods = v1.list_pod_for_all_namespaces().items

            namespace_costs = {}
            workload_costs = []

            for pod in pods:
                if pod.status.phase != "Running":
                    continue

                ns = pod.metadata.namespace
                if ns not in namespace_costs:
                    namespace_costs[ns] = {"cpu": 0, "memory": 0, "pods": 0}

                pod_cpu = 0
                pod_memory = 0

                for container in pod.spec.containers:
                    if container.resources and container.resources.requests:
                        cpu = container.resources.requests.get("cpu", "0")
                        memory = container.resources.requests.get("memory", "0")
                        pod_cpu += _parse_cpu(cpu)
                        pod_memory += _parse_memory(memory)

                namespace_costs[ns]["cpu"] += pod_cpu
                namespace_costs[ns]["memory"] += pod_memory
                namespace_costs[ns]["pods"] += 1

                owner_kind = "standalone"
                if pod.metadata.owner_references:
                    owner_kind = pod.metadata.owner_references[0].kind

                workload_costs.append({
                    "namespace": ns,
                    "pod": pod.metadata.name,
                    "ownerKind": owner_kind,
                    "cpuMillicores": pod_cpu,
                    "memoryMi": round(pod_memory / (1024 * 1024), 2)
                })

            ns_summary = []
            for ns, costs in namespace_costs.items():
                ns_summary.append({
                    "namespace": ns,
                    "totalCpuMillicores": costs["cpu"],
                    "totalMemoryMi": round(costs["memory"] / (1024 * 1024), 2),
                    "podCount": costs["pods"]
                })

            ns_summary.sort(key=lambda x: x["totalCpuMillicores"], reverse=True)

            return {
                "success": True,
                "context": context or "current",
                "note": "Cost estimates based on resource requests. Integrate with cloud billing for actual costs.",
                "byNamespace": ns_summary,
                "topWorkloads": sorted(workload_costs, key=lambda x: x["cpuMillicores"], reverse=True)[:20]
            }
        except Exception as e:
            logger.error(f"Error analyzing costs: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Overprovisioned Resources",
            readOnlyHint=True,
        ),
    )
    def get_overprovisioned_resources(
        namespace: Optional[str] = None,
        threshold: float = 50.0,
        context: str = ""
    ) -> Dict[str, Any]:
        """Find pods using significantly less resources than requested (over-provisioned).

        Args:
            namespace: Target namespace (optional, all namespaces if not specified)
            threshold: Utilization threshold percentage below which resources are considered over-provisioned
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            v1 = get_k8s_client(context)

            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["top", "pods", "--no-headers"]
            if namespace:
                cmd.extend(["-n", namespace])
            else:
                cmd.append("-A")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip() or "Metrics server not available"}

            usage_map = {}
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split()
                if namespace and len(parts) >= 3:
                    usage_map[(namespace, parts[0])] = {"cpu": parts[1], "memory": parts[2]}
                elif len(parts) >= 4:
                    usage_map[(parts[0], parts[1])] = {"cpu": parts[2], "memory": parts[3]}

            if namespace:
                pods = v1.list_namespaced_pod(namespace).items
            else:
                pods = v1.list_pod_for_all_namespaces().items

            overprovisioned = []
            for pod in pods:
                if pod.status.phase != "Running":
                    continue

                key = (pod.metadata.namespace, pod.metadata.name)
                if key not in usage_map:
                    continue

                usage = usage_map[key]
                total_cpu_req = 0
                total_mem_req = 0

                for container in pod.spec.containers:
                    if container.resources and container.resources.requests:
                        total_cpu_req += _parse_cpu(container.resources.requests.get("cpu", "0"))
                        total_mem_req += _parse_memory(container.resources.requests.get("memory", "0"))

                if total_cpu_req == 0 and total_mem_req == 0:
                    continue

                cpu_used = _parse_cpu(usage["cpu"])
                mem_used = _parse_memory(usage["memory"])

                cpu_util = (cpu_used / total_cpu_req * 100) if total_cpu_req > 0 else 0
                mem_util = (mem_used / total_mem_req * 100) if total_mem_req > 0 else 0

                if cpu_util < threshold or mem_util < threshold:
                    overprovisioned.append({
                        "namespace": pod.metadata.namespace,
                        "pod": pod.metadata.name,
                        "cpuRequested": f"{total_cpu_req}m",
                        "cpuUsed": usage["cpu"],
                        "cpuUtilization": f"{cpu_util:.1f}%",
                        "memoryRequested": f"{total_mem_req // (1024*1024)}Mi",
                        "memoryUsed": usage["memory"],
                        "memoryUtilization": f"{mem_util:.1f}%",
                        "recommendation": "Consider reducing resource requests"
                    })

            overprovisioned.sort(key=lambda x: float(x["cpuUtilization"].rstrip("%")))

            return {
                "success": True,
                "context": context or "current",
                "threshold": f"{threshold}%",
                "count": len(overprovisioned),
                "overprovisioned": overprovisioned[:50]
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Metrics retrieval timed out"}
        except Exception as e:
            logger.error(f"Error finding overprovisioned resources: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Resource Trends",
            readOnlyHint=True,
        ),
    )
    def get_resource_trends(
        namespace: Optional[str] = None,
        resource_type: str = "pods",
        context: str = ""
    ) -> Dict[str, Any]:
        """Get current resource usage snapshot for trend analysis (requires metrics-server).

        Args:
            namespace: Target namespace (optional, all namespaces if not specified)
            resource_type: Type of resource to analyze (pods or nodes)
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            if resource_type == "nodes":
                cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["top", "nodes", "--no-headers"]
            else:
                cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["top", "pods", "--no-headers"]
                if namespace:
                    cmd.extend(["-n", namespace])
                else:
                    cmd.append("-A")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip() or "Metrics server not available"}

            metrics = []
            total_cpu = 0
            total_memory = 0

            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split()

                if resource_type == "nodes" and len(parts) >= 5:
                    cpu_val = _parse_cpu(parts[1])
                    mem_bytes = _parse_memory(parts[3])
                    total_cpu += cpu_val
                    total_memory += mem_bytes
                    metrics.append({
                        "node": parts[0],
                        "cpuUsage": parts[1],
                        "cpuPercent": parts[2],
                        "memoryUsage": parts[3],
                        "memoryPercent": parts[4]
                    })
                elif len(parts) >= 3:
                    if namespace:
                        cpu_val = _parse_cpu(parts[1])
                        mem_bytes = _parse_memory(parts[2])
                        metrics.append({
                            "namespace": namespace,
                            "pod": parts[0],
                            "cpuUsage": parts[1],
                            "memoryUsage": parts[2]
                        })
                    elif len(parts) >= 4:
                        cpu_val = _parse_cpu(parts[2])
                        mem_bytes = _parse_memory(parts[3])
                        metrics.append({
                            "namespace": parts[0],
                            "pod": parts[1],
                            "cpuUsage": parts[2],
                            "memoryUsage": parts[3]
                        })
                    else:
                        cpu_val = 0
                        mem_bytes = 0
                    total_cpu += cpu_val
                    total_memory += mem_bytes

            return {
                "success": True,
                "context": context or "current",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "resourceType": resource_type,
                "summary": {
                    "totalCpuMillicores": total_cpu,
                    "totalMemoryMi": round(total_memory / (1024 * 1024), 2),
                    "resourceCount": len(metrics)
                },
                "metrics": metrics[:100],
                "note": "Store snapshots over time for trend analysis"
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Metrics retrieval timed out"}
        except Exception as e:
            logger.error(f"Error getting resource trends: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Namespace Cost Allocation",
            readOnlyHint=True,
        ),
    )
    def get_namespace_cost_allocation(context: str = "") -> Dict[str, Any]:
        """Calculate resource allocation percentages across all namespaces.

        Args:
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            v1 = get_k8s_client(context)

            pods = v1.list_pod_for_all_namespaces().items

            ns_allocation = {}
            total_cpu = 0
            total_memory = 0

            for pod in pods:
                if pod.status.phase != "Running":
                    continue

                ns = pod.metadata.namespace
                if ns not in ns_allocation:
                    ns_allocation[ns] = {"cpu": 0, "memory": 0, "pods": 0}

                for container in pod.spec.containers:
                    if container.resources and container.resources.requests:
                        cpu = _parse_cpu(container.resources.requests.get("cpu", "0"))
                        memory = _parse_memory(container.resources.requests.get("memory", "0"))
                        ns_allocation[ns]["cpu"] += cpu
                        ns_allocation[ns]["memory"] += memory
                        total_cpu += cpu
                        total_memory += memory

                ns_allocation[ns]["pods"] += 1

            allocations = []
            for ns, alloc in ns_allocation.items():
                cpu_pct = (alloc["cpu"] / total_cpu * 100) if total_cpu > 0 else 0
                mem_pct = (alloc["memory"] / total_memory * 100) if total_memory > 0 else 0

                allocations.append({
                    "namespace": ns,
                    "cpuMillicores": alloc["cpu"],
                    "cpuPercent": f"{cpu_pct:.1f}%",
                    "memoryMi": round(alloc["memory"] / (1024 * 1024), 2),
                    "memoryPercent": f"{mem_pct:.1f}%",
                    "podCount": alloc["pods"]
                })

            allocations.sort(key=lambda x: x["cpuMillicores"], reverse=True)

            return {
                "success": True,
                "context": context or "current",
                "clusterTotals": {
                    "totalCpuMillicores": total_cpu,
                    "totalMemoryMi": round(total_memory / (1024 * 1024), 2),
                    "namespaceCount": len(allocations)
                },
                "allocations": allocations
            }
        except Exception as e:
            logger.error(f"Error calculating namespace allocation: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Optimize Resource Requests",
            readOnlyHint=True,
        ),
    )
    def optimize_resource_requests(
        namespace: str,
        deployment_name: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Suggest optimal resource requests based on current usage patterns.

        Args:
            namespace: Target namespace
            deployment_name: Specific deployment to analyze (optional, all deployments if not specified)
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            apps = get_apps_client(context)
            v1 = get_k8s_client(context)

            if deployment_name:
                deployments = [apps.read_namespaced_deployment(deployment_name, namespace)]
            else:
                deployments = apps.list_namespaced_deployment(namespace).items

            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["top", "pods", "-n", namespace, "--no-headers"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            usage_map = {}
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line.strip():
                        continue
                    parts = line.split()
                    if len(parts) >= 3:
                        usage_map[parts[0]] = {
                            "cpu": _parse_cpu(parts[1]),
                            "memory": _parse_memory(parts[2])
                        }

            suggestions = []
            for deploy in deployments:
                pods = v1.list_namespaced_pod(
                    namespace,
                    label_selector=",".join([f"{k}={v}" for k, v in (deploy.spec.selector.match_labels or {}).items()])
                ).items

                for container_spec in deploy.spec.template.spec.containers:
                    current_cpu = 0
                    current_mem = 0
                    if container_spec.resources and container_spec.resources.requests:
                        current_cpu = _parse_cpu(container_spec.resources.requests.get("cpu", "0"))
                        current_mem = _parse_memory(container_spec.resources.requests.get("memory", "0"))

                    max_cpu_used = 0
                    max_mem_used = 0
                    for pod in pods:
                        if pod.metadata.name in usage_map:
                            max_cpu_used = max(max_cpu_used, usage_map[pod.metadata.name]["cpu"])
                            max_mem_used = max(max_mem_used, usage_map[pod.metadata.name]["memory"])

                    if max_cpu_used > 0 or max_mem_used > 0:
                        suggested_cpu = int(max_cpu_used * 1.2)
                        suggested_mem = int(max_mem_used * 1.2)

                        suggestions.append({
                            "deployment": deploy.metadata.name,
                            "container": container_spec.name,
                            "current": {
                                "cpu": f"{current_cpu}m",
                                "memory": f"{current_mem // (1024*1024)}Mi"
                            },
                            "observed": {
                                "maxCpu": f"{max_cpu_used}m",
                                "maxMemory": f"{max_mem_used // (1024*1024)}Mi"
                            },
                            "suggested": {
                                "cpu": f"{suggested_cpu}m",
                                "memory": f"{suggested_mem // (1024*1024)}Mi"
                            },
                            "potentialSavings": {
                                "cpu": f"{max(0, current_cpu - suggested_cpu)}m",
                                "memory": f"{max(0, (current_mem - suggested_mem) // (1024*1024))}Mi"
                            }
                        })

            return {
                "success": True,
                "context": context or "current",
                "namespace": namespace,
                "note": "Suggestions based on current usage + 20% buffer. Monitor over time for accuracy.",
                "suggestions": suggestions
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Metrics retrieval timed out"}
        except Exception as e:
            logger.error(f"Error optimizing resources: {e}")
            return {"success": False, "error": str(e)}
