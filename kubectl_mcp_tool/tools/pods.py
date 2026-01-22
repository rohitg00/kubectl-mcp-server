import json
import logging
import shlex
import subprocess
from typing import Any, Callable, Dict, List, Optional

from mcp.types import ToolAnnotations

logger = logging.getLogger("mcp-server")


def register_pod_tools(
    server,
    non_destructive: bool
):
    """Register all Pod-related tools with the MCP server.

    Args:
        server: FastMCP server instance
        non_destructive: If True, block destructive operations
    """

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Pods",
            readOnlyHint=True,
        ),
    )
    def get_pods(namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get all pods in the specified namespace."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()

            if namespace:
                pods = v1.list_namespaced_pod(namespace)
            else:
                pods = v1.list_pod_for_all_namespaces()

            return {
                "success": True,
                "pods": [
                    {
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "status": pod.status.phase,
                        "ip": pod.status.pod_ip
                    }
                    for pod in pods.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting pods: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Logs",
            readOnlyHint=True,
        ),
    )
    def get_logs(
        pod_name: str,
        namespace: Optional[str] = "default",
        container: Optional[str] = None,
        tail: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get logs from a pod."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()

            logs = v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail
            )

            return {
                "success": True,
                "logs": logs
            }
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Pod Events",
            readOnlyHint=True,
        ),
    )
    def get_pod_events(pod_name: str, namespace: str = "default") -> Dict[str, Any]:
        """Get events for a specific pod."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()
            field_selector = f"involvedObject.name={pod_name}"
            events = v1.list_namespaced_event(namespace, field_selector=field_selector)
            return {
                "success": True,
                "events": [
                    {
                        "name": event.metadata.name,
                        "type": event.type,
                        "reason": event.reason,
                        "message": event.message,
                        "timestamp": event.last_timestamp.isoformat() if event.last_timestamp else None
                    } for event in events.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting pod events: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Check Pod Health",
            readOnlyHint=True,
        ),
    )
    def check_pod_health(pod_name: str, namespace: str = "default") -> Dict[str, Any]:
        """Check the health status of a pod."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()
            pod = v1.read_namespaced_pod(pod_name, namespace)
            status = pod.status
            return {
                "success": True,
                "phase": status.phase,
                "conditions": [c.type for c in status.conditions] if status.conditions else []
            }
        except Exception as e:
            logger.error(f"Error checking pod health: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Exec in Pod",
            destructiveHint=True,
        ),
    )
    def exec_in_pod(
        pod_name: str,
        command: str,
        namespace: Optional[str] = "default",
        container: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a command inside a pod."""
        try:
            cmd = ["kubectl", "exec", pod_name, "-n", namespace]
            if container:
                cmd.extend(["-c", container])
            cmd.append("--")
            cmd.extend(shlex.split(command))

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except Exception as e:
            logger.error(f"Error executing in pod: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Cleanup Pods",
            destructiveHint=True,
        ),
    )
    def cleanup_pods(
        namespace: Optional[str] = None,
        states: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Clean up pods in problematic states (Evicted, Error, Completed, etc.)."""
        if non_destructive:
            return {"success": False, "error": "Blocked: non-destructive mode"}
        try:
            if states is None:
                states = ["Evicted", "Error", "Completed", "ContainerStatusUnknown"]

            ns_flag = ["-n", namespace] if namespace else ["--all-namespaces"]

            deleted_pods = []
            for state in states:
                if state == "Evicted":
                    cmd = ["kubectl", "get", "pods"] + ns_flag + ["-o", "json"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        try:
                            pods = json.loads(result.stdout)
                            for pod in pods.get("items", []):
                                if pod.get("status", {}).get("reason") == "Evicted":
                                    pod_name = pod["metadata"]["name"]
                                    pod_ns = pod["metadata"]["namespace"]
                                    del_cmd = ["kubectl", "delete", "pod", pod_name, "-n", pod_ns]
                                    subprocess.run(del_cmd, capture_output=True, timeout=10)
                                    deleted_pods.append(f"{pod_ns}/{pod_name}")
                        except json.JSONDecodeError:
                            pass

            return {
                "success": True,
                "deleted_count": len(deleted_pods),
                "deleted_pods": deleted_pods[:20]
            }
        except Exception as e:
            logger.error(f"Error cleaning up pods: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Pod Conditions Detailed",
            readOnlyHint=True,
        ),
    )
    def get_pod_conditions(pod_name: str, namespace: str = "default") -> Dict[str, Any]:
        """Get detailed pod conditions breakdown."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()

            pod = v1.read_namespaced_pod(pod_name, namespace)

            conditions = []
            for c in (pod.status.conditions or []):
                conditions.append({
                    "type": c.type,
                    "status": c.status,
                    "reason": c.reason,
                    "message": c.message,
                    "lastTransitionTime": str(c.last_transition_time) if c.last_transition_time else None,
                    "lastProbeTime": str(c.last_probe_time) if c.last_probe_time else None
                })

            container_statuses = []
            for cs in (pod.status.container_statuses or []):
                status = {
                    "name": cs.name,
                    "ready": cs.ready,
                    "started": cs.started,
                    "restartCount": cs.restart_count,
                    "image": cs.image,
                    "containerID": cs.container_id
                }
                if cs.state:
                    if cs.state.running:
                        status["state"] = "running"
                        status["startedAt"] = str(cs.state.running.started_at)
                    elif cs.state.waiting:
                        status["state"] = "waiting"
                        status["waitingReason"] = cs.state.waiting.reason
                    elif cs.state.terminated:
                        status["state"] = "terminated"
                        status["terminatedReason"] = cs.state.terminated.reason
                        status["exitCode"] = cs.state.terminated.exit_code
                container_statuses.append(status)

            phase_analysis = {
                "phase": pod.status.phase,
                "reason": pod.status.reason,
                "message": pod.status.message,
                "hostIP": pod.status.host_ip,
                "podIP": pod.status.pod_ip,
                "startTime": str(pod.status.start_time) if pod.status.start_time else None,
                "qosClass": pod.status.qos_class
            }

            return {
                "success": True,
                "pod": pod_name,
                "namespace": namespace,
                "phaseAnalysis": phase_analysis,
                "conditions": conditions,
                "containerStatuses": container_statuses
            }
        except Exception as e:
            logger.error(f"Error getting pod conditions: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Container Logs Previous",
            readOnlyHint=True,
        ),
    )
    def get_previous_logs(
        pod_name: str,
        namespace: str = "default",
        container: Optional[str] = None,
        tail: int = 100
    ) -> Dict[str, Any]:
        """Get logs from the previous container instance (useful for crash debugging)."""
        try:
            cmd = ["kubectl", "logs", pod_name, "-n", namespace, "--previous", f"--tail={tail}"]
            if container:
                cmd.extend(["-c", container])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                if "previous terminated container" in result.stderr.lower():
                    return {"success": False, "error": "No previous container instance found (container hasn't crashed)"}
                return {"success": False, "error": result.stderr.strip()}

            return {
                "success": True,
                "pod": pod_name,
                "namespace": namespace,
                "container": container,
                "logs": result.stdout,
                "lineCount": len(result.stdout.split("\n"))
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Log retrieval timed out"}
        except Exception as e:
            logger.error(f"Error getting previous logs: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Diagnose Pod Crash",
            readOnlyHint=True,
        ),
    )
    def diagnose_pod_crash(pod_name: str, namespace: str = "default") -> Dict[str, Any]:
        """Automated diagnosis of pod crash loops and failures."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()

            pod = v1.read_namespaced_pod(pod_name, namespace)

            diagnosis = {
                "pod": pod_name,
                "namespace": namespace,
                "phase": pod.status.phase,
                "issues": [],
                "recommendations": [],
                "containerStatuses": [],
                "events": []
            }

            for cs in (pod.status.container_statuses or []):
                container_info = {
                    "name": cs.name,
                    "ready": cs.ready,
                    "restartCount": cs.restart_count,
                    "state": None,
                    "lastState": None
                }

                if cs.state:
                    if cs.state.waiting:
                        container_info["state"] = {
                            "status": "waiting",
                            "reason": cs.state.waiting.reason,
                            "message": cs.state.waiting.message
                        }
                        if cs.state.waiting.reason == "CrashLoopBackOff":
                            diagnosis["issues"].append({
                                "container": cs.name,
                                "issue": "CrashLoopBackOff",
                                "severity": "critical",
                                "description": "Container is crashing repeatedly"
                            })
                            diagnosis["recommendations"].append("Check container logs for error messages")
                            diagnosis["recommendations"].append("Verify the container command and args are correct")
                        elif cs.state.waiting.reason == "ImagePullBackOff":
                            diagnosis["issues"].append({
                                "container": cs.name,
                                "issue": "ImagePullBackOff",
                                "severity": "critical",
                                "description": "Unable to pull container image"
                            })
                            diagnosis["recommendations"].append("Verify the image name and tag exist")
                            diagnosis["recommendations"].append("Check imagePullSecrets if using private registry")
                        elif cs.state.waiting.reason == "CreateContainerConfigError":
                            diagnosis["issues"].append({
                                "container": cs.name,
                                "issue": "CreateContainerConfigError",
                                "severity": "critical",
                                "description": "Container configuration error"
                            })
                            diagnosis["recommendations"].append("Check ConfigMaps and Secrets referenced by the container")
                    elif cs.state.running:
                        container_info["state"] = {"status": "running", "startedAt": str(cs.state.running.started_at)}
                    elif cs.state.terminated:
                        container_info["state"] = {
                            "status": "terminated",
                            "exitCode": cs.state.terminated.exit_code,
                            "reason": cs.state.terminated.reason,
                            "message": cs.state.terminated.message
                        }
                        if cs.state.terminated.exit_code != 0:
                            diagnosis["issues"].append({
                                "container": cs.name,
                                "issue": f"Exited with code {cs.state.terminated.exit_code}",
                                "severity": "error",
                                "reason": cs.state.terminated.reason
                            })
                            if cs.state.terminated.reason == "OOMKilled":
                                diagnosis["recommendations"].append(f"Increase memory limit for container '{cs.name}'")
                            elif cs.state.terminated.reason == "Error":
                                diagnosis["recommendations"].append(f"Check logs for container '{cs.name}' to identify the error")

                if cs.last_state and cs.last_state.terminated:
                    container_info["lastState"] = {
                        "status": "terminated",
                        "exitCode": cs.last_state.terminated.exit_code,
                        "reason": cs.last_state.terminated.reason,
                        "finishedAt": str(cs.last_state.terminated.finished_at)
                    }

                diagnosis["containerStatuses"].append(container_info)

            events = v1.list_namespaced_event(namespace, field_selector=f"involvedObject.name={pod_name}")
            for event in events.items:
                if event.type == "Warning":
                    diagnosis["events"].append({
                        "type": event.type,
                        "reason": event.reason,
                        "message": event.message,
                        "count": event.count
                    })

            return {"success": True, "diagnosis": diagnosis}
        except Exception as e:
            logger.error(f"Error diagnosing pod crash: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Detect Pending Pods",
            readOnlyHint=True,
        ),
    )
    def detect_pending_pods(namespace: Optional[str] = None) -> Dict[str, Any]:
        """Find pending pods and explain why they are not scheduled."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()

            if namespace:
                pods = v1.list_namespaced_pod(namespace, field_selector="status.phase=Pending")
            else:
                pods = v1.list_pod_for_all_namespaces(field_selector="status.phase=Pending")

            pending_pods = []
            for pod in pods.items:
                pod_info = {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "createdAt": str(pod.metadata.creation_timestamp),
                    "reasons": [],
                    "events": []
                }

                for condition in (pod.status.conditions or []):
                    if condition.type == "PodScheduled" and condition.status == "False":
                        pod_info["reasons"].append({
                            "type": "SchedulingFailed",
                            "reason": condition.reason,
                            "message": condition.message
                        })

                events = v1.list_namespaced_event(
                    pod.metadata.namespace,
                    field_selector=f"involvedObject.name={pod.metadata.name}"
                )
                for event in events.items:
                    if event.reason in ["FailedScheduling", "FailedAttachVolume", "FailedMount"]:
                        pod_info["events"].append({
                            "reason": event.reason,
                            "message": event.message,
                            "count": event.count
                        })
                        msg = event.message or ""
                        if "Insufficient cpu" in msg:
                            pod_info["reasons"].append({
                                "type": "InsufficientCPU",
                                "message": "Not enough CPU available on any node"
                            })
                        elif "Insufficient memory" in msg:
                            pod_info["reasons"].append({
                                "type": "InsufficientMemory",
                                "message": "Not enough memory available on any node"
                            })
                        elif "node(s) didn't match node selector" in msg:
                            pod_info["reasons"].append({
                                "type": "NodeSelectorMismatch",
                                "message": "No nodes match the pod's nodeSelector"
                            })
                        elif "PersistentVolumeClaim" in msg:
                            pod_info["reasons"].append({
                                "type": "PVCPending",
                                "message": "PersistentVolumeClaim is not bound"
                            })

                pending_pods.append(pod_info)

            return {
                "success": True,
                "pendingCount": len(pending_pods),
                "pendingPods": pending_pods
            }
        except Exception as e:
            logger.error(f"Error detecting pending pods: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Evicted Pods",
            readOnlyHint=True,
        ),
    )
    def get_evicted_pods(namespace: Optional[str] = None) -> Dict[str, Any]:
        """Find evicted pods with their eviction reasons."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()

            if namespace:
                pods = v1.list_namespaced_pod(namespace)
            else:
                pods = v1.list_pod_for_all_namespaces()

            evicted = []
            for pod in pods.items:
                if pod.status.phase == "Failed" and pod.status.reason == "Evicted":
                    evicted.append({
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "reason": pod.status.reason,
                        "message": pod.status.message,
                        "nodeName": pod.spec.node_name,
                        "evictedAt": str(pod.status.start_time) if pod.status.start_time else None
                    })

            by_reason = {}
            for pod in evicted:
                msg = pod.get("message", "Unknown")
                if "ephemeral-storage" in msg.lower():
                    reason = "DiskPressure"
                elif "memory" in msg.lower():
                    reason = "MemoryPressure"
                else:
                    reason = "Other"

                if reason not in by_reason:
                    by_reason[reason] = []
                by_reason[reason].append(pod["name"])

            return {
                "success": True,
                "summary": {
                    "totalEvicted": len(evicted),
                    "byReason": {k: len(v) for k, v in by_reason.items()}
                },
                "evictedPods": evicted,
                "recommendations": [
                    "DiskPressure: Clean up disk space or increase ephemeral-storage limits" if "DiskPressure" in by_reason else None,
                    "MemoryPressure: Increase memory limits or add more nodes" if "MemoryPressure" in by_reason else None
                ]
            }
        except Exception as e:
            logger.error(f"Error getting evicted pods: {e}")
            return {"success": False, "error": str(e)}
