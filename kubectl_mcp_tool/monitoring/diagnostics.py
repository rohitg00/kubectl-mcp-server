"""
Monitoring and diagnostics module for Kubernetes.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class KubernetesDiagnostics:
    """Monitoring and diagnostics for Kubernetes."""
    
    def __init__(self):
        """Initialize Kubernetes client."""
        try:
            config.load_kube_config()
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.metrics_v1 = None  # Will be initialized on first use
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    def get_pod_logs(self, pod_name: str, namespace: str = "default", 
                    container: Optional[str] = None, tail_lines: int = 100,
                    since_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Get logs from a pod."""
        try:
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines,
                since_seconds=since_seconds
            )
            return {
                "status": "success",
                "pod_name": pod_name,
                "namespace": namespace,
                "container": container,
                "logs": logs
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to get pod logs: {e.reason}"
            }

    def analyze_pod_logs(self, pod_name: str, namespace: str = "default",
                        container: Optional[str] = None, tail_lines: int = 1000) -> Dict[str, Any]:
        """Analyze pod logs for patterns and issues."""
        try:
            logs = self.get_pod_logs(pod_name, namespace, container, tail_lines)
            if logs["status"] != "success":
                return logs

            log_content = logs["logs"]
            analysis = {
                "error_count": 0,
                "warning_count": 0,
                "error_patterns": [],
                "warning_patterns": [],
                "common_patterns": [],
                "time_analysis": self._analyze_log_timing(log_content)
            }

            # Analyze log content
            lines = log_content.split("\n")
            pattern_counts = {}
            
            for line in lines:
                # Count errors and warnings
                if re.search(r"error|exception|fail", line, re.IGNORECASE):
                    analysis["error_count"] += 1
                    analysis["error_patterns"].append(line)
                elif re.search(r"warn|warning", line, re.IGNORECASE):
                    analysis["warning_count"] += 1
                    analysis["warning_patterns"].append(line)

                # Track common patterns
                pattern = self._extract_log_pattern(line)
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

            # Get most common patterns
            sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
            analysis["common_patterns"] = [
                {"pattern": p, "count": c} for p, c in sorted_patterns[:5]
            ]

            return {
                "status": "success",
                "pod_name": pod_name,
                "namespace": namespace,
                "analysis": analysis
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to analyze pod logs: {str(e)}"
            }

    def get_pod_events(self, pod_name: str, namespace: str = "default") -> Dict[str, Any]:
        """Get events related to a pod."""
        try:
            field_selector = f"involvedObject.name={pod_name}"
            events = self.core_v1.list_namespaced_event(
                namespace=namespace,
                field_selector=field_selector
            )
            
            formatted_events = []
            for event in events.items:
                formatted_events.append({
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "count": event.count,
                    "first_timestamp": event.first_timestamp.isoformat() if event.first_timestamp else None,
                    "last_timestamp": event.last_timestamp.isoformat() if event.last_timestamp else None
                })

            return {
                "status": "success",
                "pod_name": pod_name,
                "namespace": namespace,
                "events": formatted_events
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to get pod events: {e.reason}"
            }

    def check_pod_health(self, pod_name: str, namespace: str = "default") -> Dict[str, Any]:
        """Check the health status of a pod."""
        try:
            pod = self.core_v1.read_namespaced_pod(pod_name, namespace)
            
            health_check = {
                "status": pod.status.phase,
                "container_statuses": [],
                "conditions": [],
                "events": [],
                "warnings": []
            }

            # Check container statuses
            if pod.status.container_statuses:
                for container in pod.status.container_statuses:
                    container_status = {
                        "name": container.name,
                        "ready": container.ready,
                        "restart_count": container.restart_count,
                        "state": self._get_container_state(container.state)
                    }
                    health_check["container_statuses"].append(container_status)

                    if container.restart_count > 5:
                        health_check["warnings"].append(
                            f"Container {container.name} has restarted {container.restart_count} times"
                        )

            # Check pod conditions
            if pod.status.conditions:
                for condition in pod.status.conditions:
                    health_check["conditions"].append({
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message
                    })

            # Get recent events
            events = self.get_pod_events(pod_name, namespace)
            if events["status"] == "success":
                health_check["events"] = events["events"]

            return {
                "status": "success",
                "pod_name": pod_name,
                "namespace": namespace,
                "health_check": health_check
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to check pod health: {e.reason}"
            }

    def get_resource_usage(self, namespace: str = None) -> Dict[str, Any]:
        """Get resource usage metrics for pods."""
        try:
            if not self.metrics_v1:
                self.metrics_v1 = client.CustomObjectsApi()

            # Get pod metrics
            if namespace:
                metrics = self.metrics_v1.list_namespaced_custom_object(
                    group="metrics.k8s.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="pods"
                )
            else:
                metrics = self.metrics_v1.list_cluster_custom_object(
                    group="metrics.k8s.io",
                    version="v1beta1",
                    plural="pods"
                )

            formatted_metrics = []
            for pod in metrics["items"]:
                pod_metrics = {
                    "name": pod["metadata"]["name"],
                    "namespace": pod["metadata"]["namespace"],
                    "containers": []
                }

                for container in pod["containers"]:
                    container_metrics = {
                        "name": container["name"],
                        "cpu": container["usage"]["cpu"],
                        "memory": container["usage"]["memory"]
                    }
                    pod_metrics["containers"].append(container_metrics)

                formatted_metrics.append(pod_metrics)

            return {
                "status": "success",
                "metrics": formatted_metrics
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to get resource usage metrics: {e.reason}"
            }

    def validate_resources(self, namespace: str = None) -> Dict[str, Any]:
        """Validate resource configurations and usage."""
        try:
            pods = (self.core_v1.list_namespaced_pod(namespace)
                   if namespace else self.core_v1.list_pod_for_all_namespaces())
            
            validation_results = {
                "resource_issues": [],
                "recommendations": []
            }

            for pod in pods.items:
                pod_name = pod.metadata.name
                pod_namespace = pod.metadata.namespace

                # Check for resource requests and limits
                for container in pod.spec.containers:
                    container_name = container.name
                    resources = container.resources

                    if not resources or not resources.requests:
                        validation_results["resource_issues"].append({
                            "pod": pod_name,
                            "namespace": pod_namespace,
                            "container": container_name,
                            "issue": "No resource requests specified"
                        })
                        validation_results["recommendations"].append(
                            f"Set resource requests for container {container_name} in pod {pod_name}"
                        )

                    if not resources or not resources.limits:
                        validation_results["resource_issues"].append({
                            "pod": pod_name,
                            "namespace": pod_namespace,
                            "container": container_name,
                            "issue": "No resource limits specified"
                        })
                        validation_results["recommendations"].append(
                            f"Set resource limits for container {container_name} in pod {pod_name}"
                        )

            return {
                "status": "success",
                "validation": validation_results
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to validate resources: {e.reason}"
            }

    @staticmethod
    def _get_container_state(state) -> Dict[str, Any]:
        """Extract container state information."""
        if state.running:
            return {
                "state": "running",
                "started_at": state.running.started_at.isoformat() if state.running.started_at else None
            }
        elif state.waiting:
            return {
                "state": "waiting",
                "reason": state.waiting.reason,
                "message": state.waiting.message
            }
        elif state.terminated:
            return {
                "state": "terminated",
                "reason": state.terminated.reason,
                "exit_code": state.terminated.exit_code,
                "message": state.terminated.message
            }
        return {"state": "unknown"}

    @staticmethod
    def _extract_log_pattern(line: str) -> str:
        """Extract a generic pattern from a log line."""
        # Remove timestamps
        pattern = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "TIMESTAMP", line)
        # Remove specific IDs/hashes
        pattern = re.sub(r"[a-f0-9]{8,}", "ID", pattern)
        # Remove IP addresses
        pattern = re.sub(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "IP", pattern)
        return pattern

    @staticmethod
    def _analyze_log_timing(log_content: str) -> Dict[str, Any]:
        """Analyze timing patterns in logs."""
        timestamps = []
        timestamp_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
        
        for line in log_content.split("\n"):
            match = re.search(timestamp_pattern, line)
            if match:
                try:
                    timestamp = datetime.fromisoformat(match.group(0))
                    timestamps.append(timestamp)
                except ValueError:
                    continue

        if not timestamps:
            return {"message": "No timestamps found in logs"}

        time_analysis = {
            "start_time": min(timestamps).isoformat(),
            "end_time": max(timestamps).isoformat(),
            "duration": str(max(timestamps) - min(timestamps)),
            "log_frequency": {}
        }

        # Analyze log frequency by hour
        hour_counts = {}
        for timestamp in timestamps:
            hour = timestamp.strftime("%Y-%m-%d %H:00")
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        time_analysis["log_frequency"] = dict(sorted(hour_counts.items()))
        return time_analysis 