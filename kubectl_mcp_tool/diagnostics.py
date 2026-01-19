#!/usr/bin/env python3
"""
Kubernetes diagnostics and monitoring module for kubectl-mcp-tool.
"""

import json
import logging
from typing import Dict, List, Any, Optional
import subprocess

logger = logging.getLogger(__name__)

class KubernetesDiagnostics:
    """Kubernetes diagnostics and monitoring tools."""

    @staticmethod
    def run_command(cmd: List[str]) -> str:
        """Run a kubectl command and return the output."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"Error output: {e.stderr}")
            return f"Error: {e.stderr}"

    def get_logs(self, pod_name: str, namespace: Optional[str] = None, 
                container: Optional[str] = None, tail: Optional[int] = None, 
                previous: bool = False) -> Dict[str, Any]:
        """Get logs from a pod."""
        cmd = ["kubectl", "logs"]
        
        if namespace:
            cmd.extend(["-n", namespace])
        
        if container:
            cmd.extend(["-c", container])
        
        if tail:
            cmd.extend(["--tail", str(tail)])
        
        if previous:
            cmd.append("-p")
        
        cmd.append(pod_name)
        
        logs = self.run_command(cmd)
        return {
            "pod_name": pod_name,
            "namespace": namespace or "default",
            "container": container,
            "logs": logs
        }

    def get_events(self, namespace: Optional[str] = None, 
                  resource_name: Optional[str] = None) -> Dict[str, Any]:
        """Get Kubernetes events."""
        cmd = ["kubectl", "get", "events"]
        
        if namespace:
            cmd.extend(["-n", namespace])
        
        if resource_name:
            cmd.extend([f"--field-selector=involvedObject.name={resource_name}"])
        
        cmd.extend(["--sort-by=.metadata.creationTimestamp"])
        
        events = self.run_command(cmd)
        return {
            "namespace": namespace or "default",
            "resource_name": resource_name,
            "events": events
        }

    def check_pod_health(self, pod_name: str, namespace: str = "default") -> Dict[str, Any]:
        """Check pod health and detect common issues."""
        # Get pod details
        cmd = ["kubectl", "get", "pod", pod_name, "-n", namespace, "-o", "json"]
        pod_json_str = self.run_command(cmd)
        
        try:
            pod_json = json.loads(pod_json_str)
        except json.JSONDecodeError:
            return {"error": "Failed to get pod details", "raw_output": pod_json_str}

        issues = []
        
        # Check pod status
        status = pod_json.get("status", {})
        phase = status.get("phase")
        if phase != "Running":
            issues.append(f"Pod is not running (Status: {phase})")
        
        # Check container statuses
        for container in status.get("containerStatuses", []):
            if not container.get("ready"):
                waiting = container.get("state", {}).get("waiting", {})
                if waiting:
                    issues.append(
                        f"Container {container['name']} is waiting: "
                        f"{waiting.get('reason')} - {waiting.get('message')}"
                    )
        
        # Get recent events
        events = self.get_events(namespace, pod_name)
        
        # Check resource usage
        usage = self.get_resource_usage("pods", namespace, pod_name)
        
        return {
            "pod_name": pod_name,
            "namespace": namespace,
            "status": phase,
            "issues": issues,
            "events": events.get("events"),
            "resource_usage": usage.get("usage")
        }

    def get_resource_usage(self, resource_type: str = "pods", 
                         namespace: Optional[str] = None,
                         resource_name: Optional[str] = None) -> Dict[str, Any]:
        """Get resource usage statistics."""
        cmd = ["kubectl", "top", resource_type]
        
        if namespace:
            cmd.extend(["-n", namespace])
        
        if resource_name:
            cmd.append(resource_name)
        
        usage = self.run_command(cmd)
        return {
            "resource_type": resource_type,
            "namespace": namespace,
            "resource_name": resource_name,
            "usage": usage
        }

    def validate_resources(self, namespace: str = "default") -> Dict[str, Any]:
        """Validate Kubernetes resources for common misconfigurations."""
        validations = []
        
        # Get all pods
        cmd = ["kubectl", "get", "pods", "-n", namespace, "-o", "json"]
        pods_json_str = self.run_command(cmd)
        
        try:
            pods = json.loads(pods_json_str)
        except json.JSONDecodeError:
            return {"error": "Failed to get pods", "raw_output": pods_json_str}

        for pod in pods.get("items", []):
            pod_name = pod["metadata"]["name"]
            
            # Check resource limits
            for container in pod["spec"]["containers"]:
                if not container.get("resources", {}).get("limits"):
                    validations.append({
                        "level": "warning",
                        "type": "no_resource_limits",
                        "message": f"Container {container['name']} in pod {pod_name} has no resource limits"
                    })
                
                # Check probes
                if not container.get("livenessProbe"):
                    validations.append({
                        "level": "warning",
                        "type": "no_liveness_probe",
                        "message": f"Container {container['name']} in pod {pod_name} has no liveness probe"
                    })
                if not container.get("readinessProbe"):
                    validations.append({
                        "level": "warning",
                        "type": "no_readiness_probe",
                        "message": f"Container {container['name']} in pod {pod_name} has no readiness probe"
                    })

        return {
            "namespace": namespace,
            "validations": validations,
            "summary": {
                "total_validations": len(validations),
                "warnings": len([v for v in validations if v["level"] == "warning"]),
                "errors": len([v for v in validations if v["level"] == "error"])
            }
        }

    def analyze_pod_logs(self, pod_name: str, namespace: str = "default",
                        container: Optional[str] = None, tail: int = 1000) -> Dict[str, Any]:
        """Analyze pod logs for common issues and patterns."""
        # Get logs
        logs_data = self.get_logs(pod_name, namespace, container, tail)
        logs = logs_data.get("logs", "")
        
        analysis = {
            "error_count": 0,
            "warning_count": 0,
            "errors": [],
            "warnings": [],
            "patterns": {}
        }
        
        # Common error patterns to look for
        error_patterns = [
            "error", "exception", "failed", "failure", "fatal",
            "OOMKilled", "CrashLoopBackOff"
        ]
        
        warning_patterns = [
            "warning", "warn", "deprecated"
        ]
        
        # Analyze logs
        for line in logs.split("\n"):
            line_lower = line.lower()
            
            # Check for errors
            for pattern in error_patterns:
                if pattern in line_lower:
                    analysis["error_count"] += 1
                    analysis["errors"].append(line)
                    break
            
            # Check for warnings
            for pattern in warning_patterns:
                if pattern in line_lower:
                    analysis["warning_count"] += 1
                    analysis["warnings"].append(line)
                    break
        
        return {
            "pod_name": pod_name,
            "namespace": namespace,
            "container": container,
            "analysis": analysis
        }


# Convenience functions for direct import
_diagnostics = KubernetesDiagnostics()


def check_kubectl_installation() -> Dict[str, Any]:
    """Check if kubectl is installed and accessible."""
    try:
        import shutil
        kubectl_path = shutil.which("kubectl")
        if not kubectl_path:
            return {
                "installed": False,
                "error": "kubectl not found in PATH"
            }
        
        import subprocess
        result = subprocess.run(
            ["kubectl", "version", "--client", "-o", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {
                "installed": True,
                "path": kubectl_path,
                "error": result.stderr
            }
        
        import json
        version_info = json.loads(result.stdout)
        return {
            "installed": True,
            "path": kubectl_path,
            "version": version_info.get("clientVersion", {})
        }
    except Exception as e:
        return {
            "installed": False,
            "error": str(e)
        }


def check_cluster_connection() -> Dict[str, Any]:
    """Check if we can connect to a Kubernetes cluster."""
    try:
        import subprocess
        result = subprocess.run(
            ["kubectl", "cluster-info"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {
                "connected": False,
                "error": result.stderr
            }
        
        return {
            "connected": True,
            "cluster_info": result.stdout.strip()
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }


def run_diagnostics() -> Dict[str, Any]:
    """Run comprehensive diagnostics."""
    kubectl_check = check_kubectl_installation()
    cluster_check = check_cluster_connection()
    
    diagnostics = {
        "kubectl": kubectl_check,
        "cluster": cluster_check,
        "overall_status": "healthy" if (
            kubectl_check.get("installed") and 
            cluster_check.get("connected")
        ) else "unhealthy"
    }
    
    if diagnostics["overall_status"] == "healthy":
        # Additional checks
        try:
            import subprocess
            
            # Check nodes
            nodes_result = subprocess.run(
                ["kubectl", "get", "nodes", "-o", "json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if nodes_result.returncode == 0:
                import json
                nodes_data = json.loads(nodes_result.stdout)
                nodes_count = len(nodes_data.get("items", []))
                ready_nodes = sum(
                    1 for node in nodes_data.get("items", [])
                    if any(
                        c.get("type") == "Ready" and c.get("status") == "True"
                        for c in node.get("status", {}).get("conditions", [])
                    )
                )
                diagnostics["nodes"] = {
                    "total": nodes_count,
                    "ready": ready_nodes
                }
        except Exception as e:
            diagnostics["nodes_error"] = str(e)
    
    return diagnostics