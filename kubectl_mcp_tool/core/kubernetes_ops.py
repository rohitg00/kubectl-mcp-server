"""
Core Kubernetes operations module.
"""

import os
import json
import logging
import time
import re
import yaml
from typing import Dict, Any, List, Optional
import subprocess
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

class KubernetesOperations:
    """Core Kubernetes operations."""
    
    def __init__(self):
        """Initialize Kubernetes client."""
        try:
            config.load_kube_config()
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.networking_v1 = client.NetworkingV1Api()
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    def run_command(self, cmd: List[str]) -> str:
        """Run a kubectl command and return the output."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"Error output: {e.stderr}")
            return f"Error: {e.stderr}"

    # Pod Management
    def create_pod(self, pod_spec: Dict[str, Any], namespace: str = "default") -> Dict[str, Any]:
        """Create a pod from specification."""
        try:
            pod = self.core_v1.create_namespaced_pod(
                namespace=namespace,
                body=pod_spec
            )
            return {
                "status": "success",
                "pod_name": pod.metadata.name,
                "namespace": namespace,
                "message": f"Pod {pod.metadata.name} created successfully"
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to create pod: {e.reason}",
                "details": e.body
            }

    def delete_pod(self, pod_name: str, namespace: str = "default") -> Dict[str, Any]:
        """Delete a pod."""
        try:
            self.core_v1.delete_namespaced_pod(
                name=pod_name,
                namespace=namespace
            )
            return {
                "status": "success",
                "message": f"Pod {pod_name} deleted successfully"
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to delete pod: {e.reason}"
            }

    # Deployment Management
    def create_deployment(self, deployment_spec: Dict[str, Any], namespace: str = "default") -> Dict[str, Any]:
        """Create a deployment."""
        try:
            deployment = self.apps_v1.create_namespaced_deployment(
                namespace=namespace,
                body=deployment_spec
            )
            return {
                "status": "success",
                "deployment_name": deployment.metadata.name,
                "namespace": namespace,
                "message": f"Deployment {deployment.metadata.name} created successfully"
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to create deployment: {e.reason}",
                "details": e.body
            }

    def scale_deployment(self, name: str, replicas: int, namespace: str = "default") -> Dict[str, Any]:
        """Scale a deployment."""
        try:
            scale = self.apps_v1.read_namespaced_deployment_scale(name, namespace)
            scale.spec.replicas = replicas
            self.apps_v1.patch_namespaced_deployment_scale(name, namespace, scale)
            return {
                "status": "success",
                "message": f"Deployment {name} scaled to {replicas} replicas"
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to scale deployment: {e.reason}"
            }

    def update_deployment(self, name: str, deployment_spec: Dict[str, Any], namespace: str = "default") -> Dict[str, Any]:
        """Update a deployment."""
        try:
            deployment = self.apps_v1.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=deployment_spec
            )
            return {
                "status": "success",
                "message": f"Deployment {name} updated successfully"
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to update deployment: {e.reason}"
            }

    def rollback_deployment(self, name: str, revision: Optional[int] = None, namespace: str = "default") -> Dict[str, Any]:
        """Rollback a deployment to a previous revision."""
        try:
            if revision:
                cmd = ["kubectl", "rollout", "undo", "deployment", name, 
                      f"--to-revision={revision}", "-n", namespace]
            else:
                cmd = ["kubectl", "rollout", "undo", "deployment", name, "-n", namespace]
            
            result = self.run_command(cmd)
            return {
                "status": "success",
                "message": f"Deployment {name} rolled back successfully",
                "details": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to rollback deployment: {str(e)}"
            }

    # Service Management
    def create_service(self, service_spec: Dict[str, Any], namespace: str = "default") -> Dict[str, Any]:
        """Create a service."""
        try:
            service = self.core_v1.create_namespaced_service(
                namespace=namespace,
                body=service_spec
            )
            return {
                "status": "success",
                "service_name": service.metadata.name,
                "namespace": namespace,
                "message": f"Service {service.metadata.name} created successfully"
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to create service: {e.reason}"
            }

    def delete_service(self, name: str, namespace: str = "default") -> Dict[str, Any]:
        """Delete a service."""
        try:
            self.core_v1.delete_namespaced_service(
                name=name,
                namespace=namespace
            )
            return {
                "status": "success",
                "message": f"Service {name} deleted successfully"
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to delete service: {e.reason}"
            }

    # ConfigMap and Secret Management
    def create_config_map(self, name: str, data: Dict[str, str], namespace: str = "default") -> Dict[str, Any]:
        """Create a ConfigMap."""
        try:
            config_map = self.core_v1.create_namespaced_config_map(
                namespace=namespace,
                body=client.V1ConfigMap(
                    metadata=client.V1ObjectMeta(name=name),
                    data=data
                )
            )
            return {
                "status": "success",
                "message": f"ConfigMap {name} created successfully"
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to create ConfigMap: {e.reason}"
            }

    def create_secret(self, name: str, data: Dict[str, str], secret_type: str = "Opaque", 
                     namespace: str = "default") -> Dict[str, Any]:
        """Create a Secret."""
        try:
            # Encode data values in base64
            encoded_data = {k: self._encode_secret(v) for k, v in data.items()}
            
            secret = self.core_v1.create_namespaced_secret(
                namespace=namespace,
                body=client.V1Secret(
                    metadata=client.V1ObjectMeta(name=name),
                    type=secret_type,
                    data=encoded_data
                )
            )
            return {
                "status": "success",
                "message": f"Secret {name} created successfully"
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to create Secret: {e.reason}"
            }

    # Network Operations
    def create_network_policy(self, policy_spec: Dict[str, Any], namespace: str = "default") -> Dict[str, Any]:
        """Create a NetworkPolicy."""
        try:
            policy = self.networking_v1.create_namespaced_network_policy(
                namespace=namespace,
                body=policy_spec
            )
            return {
                "status": "success",
                "message": f"NetworkPolicy {policy.metadata.name} created successfully"
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to create NetworkPolicy: {e.reason}"
            }

    def create_ingress(self, ingress_spec: Dict[str, Any], namespace: str = "default") -> Dict[str, Any]:
        """Create an Ingress."""
        try:
            ingress = self.networking_v1.create_namespaced_ingress(
                namespace=namespace,
                body=ingress_spec
            )
            return {
                "status": "success",
                "message": f"Ingress {ingress.metadata.name} created successfully"
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to create Ingress: {e.reason}"
            }

    # Context Management
    def get_contexts(self) -> Dict[str, Any]:
        """Get available contexts."""
        try:
            cmd = ["kubectl", "config", "get-contexts"]
            result = self.run_command(cmd)
            return {
                "status": "success",
                "contexts": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to get contexts: {str(e)}"
            }

    def switch_context(self, context_name: str) -> Dict[str, Any]:
        """Switch to a different kubectl context."""
        try:
            cmd = ["kubectl", "config", "use-context", context_name]
            result = self.run_command(cmd)
            
            # Reload kubernetes config after switching context
            config.load_kube_config()
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            
            return {
                "status": "success",
                "message": f"Switched to context {context_name}",
                "details": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to switch context: {str(e)}"
            }

    # Resource Listing Methods
    def list_pods(self, namespace: str = "default", label_selector: Optional[str] = None, 
                 field_selector: Optional[str] = None) -> Dict[str, Any]:
        """List pods in a namespace."""
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=label_selector,
                field_selector=field_selector
            )
            
            result = []
            for pod in pods.items:
                containers = []
                for container in pod.spec.containers:
                    container_status = None
                    for cs in pod.status.container_statuses or []:
                        if cs.name == container.name:
                            container_status = cs
                            break
                            
                    container_info = {
                        "name": container.name,
                        "image": container.image,
                        "ready": container_status.ready if container_status else None,
                        "restart_count": container_status.restart_count if container_status else None,
                        "state": str(container_status.state) if container_status and container_status.state else None
                    }
                    containers.append(container_info)
                
                pod_info = {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "ip": pod.status.pod_ip,
                    "node": pod.spec.node_name,
                    "age": str(pod.metadata.creation_timestamp),
                    "containers": containers
                }
                result.append(pod_info)
                
            return {
                "status": "success",
                "items": result,
                "count": len(result)
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to list pods: {e.reason}"
            }
    
    def list_services(self, namespace: str = "default", label_selector: Optional[str] = None) -> Dict[str, Any]:
        """List services in a namespace."""
        try:
            services = self.core_v1.list_namespaced_service(
                namespace=namespace,
                label_selector=label_selector
            )
            
            result = []
            for svc in services.items:
                ports = []
                for port in svc.spec.ports or []:
                    port_info = {
                        "name": port.name,
                        "port": port.port,
                        "target_port": port.target_port,
                        "protocol": port.protocol,
                        "node_port": port.node_port if svc.spec.type == "NodePort" else None
                    }
                    ports.append(port_info)
                
                service_info = {
                    "name": svc.metadata.name,
                    "namespace": svc.metadata.namespace,
                    "type": svc.spec.type,
                    "cluster_ip": svc.spec.cluster_ip,
                    "external_ips": svc.spec.external_i_ps if hasattr(svc.spec, "external_i_ps") else None,
                    "ports": ports,
                    "selector": svc.spec.selector,
                    "age": str(svc.metadata.creation_timestamp)
                }
                result.append(service_info)
                
            return {
                "status": "success",
                "items": result,
                "count": len(result)
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to list services: {e.reason}"
            }
            
    def list_deployments(self, namespace: str = "default", label_selector: Optional[str] = None) -> Dict[str, Any]:
        """List deployments in a namespace."""
        try:
            deployments = self.apps_v1.list_namespaced_deployment(
                namespace=namespace,
                label_selector=label_selector
            )
            
            result = []
            for deploy in deployments.items:
                containers = []
                for container in deploy.spec.template.spec.containers:
                    container_info = {
                        "name": container.name,
                        "image": container.image
                    }
                    containers.append(container_info)
                
                deployment_info = {
                    "name": deploy.metadata.name,
                    "namespace": deploy.metadata.namespace,
                    "replicas": f"{deploy.status.ready_replicas or 0}/{deploy.spec.replicas}",
                    "strategy": deploy.spec.strategy.type,
                    "selectors": deploy.spec.selector.match_labels,
                    "containers": containers,
                    "conditions": [
                        {
                            "type": condition.type,
                            "status": condition.status,
                            "reason": condition.reason
                        } for condition in (deploy.status.conditions or [])
                    ],
                    "age": str(deploy.metadata.creation_timestamp)
                }
                result.append(deployment_info)
                
            return {
                "status": "success",
                "items": result,
                "count": len(result)
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to list deployments: {e.reason}"
            }
            
    def list_nodes(self, label_selector: Optional[str] = None) -> Dict[str, Any]:
        """List all nodes in the cluster."""
        try:
            nodes = self.core_v1.list_node(label_selector=label_selector)
            
            result = []
            for node in nodes.items:
                addresses = {addr.type: addr.address for addr in node.status.addresses or []}
                node_info = {
                    "name": node.metadata.name,
                    "status": "Ready" if any(cond.type == "Ready" and cond.status == "True" 
                                          for cond in node.status.conditions or []) else "NotReady",
                    "roles": [label.replace("node-role.kubernetes.io/", "") 
                             for label in node.metadata.labels or {} 
                             if label.startswith("node-role.kubernetes.io/")],
                    "internal_ip": addresses.get("InternalIP", ""),
                    "external_ip": addresses.get("ExternalIP", ""),
                    "os_image": node.status.node_info.os_image if node.status.node_info else "",
                    "kernel_version": node.status.node_info.kernel_version if node.status.node_info else "",
                    "kubelet_version": node.status.node_info.kubelet_version if node.status.node_info else "",
                    "age": str(node.metadata.creation_timestamp)
                }
                result.append(node_info)
                
            return {
                "status": "success",
                "items": result,
                "count": len(result)
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to list nodes: {e.reason}"
            }
            
    def list_namespaces(self, label_selector: Optional[str] = None) -> Dict[str, Any]:
        """List all namespaces."""
        try:
            namespaces = self.core_v1.list_namespace(label_selector=label_selector)
            
            result = []
            for ns in namespaces.items:
                namespace_info = {
                    "name": ns.metadata.name,
                    "status": ns.status.phase,
                    "labels": ns.metadata.labels,
                    "age": str(ns.metadata.creation_timestamp)
                }
                result.append(namespace_info)
                
            return {
                "status": "success",
                "items": result,
                "count": len(result)
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to list namespaces: {e.reason}"
            }
            
    # Helm Chart Support
    def install_helm_chart(self, name: str, chart: str, namespace: str, 
                          repo: Optional[str] = None, values: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Install a Helm chart."""
        try:
            # Add the Helm repository if specified
            if repo:
                repo_name = chart.split('/')[0] if '/' in chart else "repo"
                add_repo_cmd = ["helm", "repo", "add", repo_name, repo]
                self.run_command(add_repo_cmd)
                
                # Update repos to get latest charts
                update_cmd = ["helm", "repo", "update"]
                self.run_command(update_cmd)
            
            # Create values file if values are provided
            values_file = None
            if values:
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
                    yaml.dump(values, f)
                    values_file = f.name
            
            # Build install command
            install_cmd = ["helm", "install", name, chart, "--namespace", namespace, "--create-namespace"]
            if values_file:
                install_cmd.extend(["-f", values_file])
                
            # Run the install command
            result = self.run_command(install_cmd)
            
            # Clean up values file
            if values_file:
                import os
                os.unlink(values_file)
                
            return {
                "status": "success",
                "message": f"Helm chart {chart} installed with release name {name}",
                "details": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to install Helm chart: {str(e)}"
            }
            
    def upgrade_helm_chart(self, name: str, chart: str, namespace: str, 
                          repo: Optional[str] = None, values: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Upgrade a Helm release."""
        try:
            # Add the Helm repository if specified
            if repo:
                repo_name = chart.split('/')[0] if '/' in chart else "repo"
                add_repo_cmd = ["helm", "repo", "add", repo_name, repo]
                self.run_command(add_repo_cmd)
                
                # Update repos to get latest charts
                update_cmd = ["helm", "repo", "update"]
                self.run_command(update_cmd)
            
            # Create values file if values are provided
            values_file = None
            if values:
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
                    yaml.dump(values, f)
                    values_file = f.name
            
            # Build upgrade command
            upgrade_cmd = ["helm", "upgrade", name, chart, "--namespace", namespace]
            if values_file:
                upgrade_cmd.extend(["-f", values_file])
                
            # Run the upgrade command
            result = self.run_command(upgrade_cmd)
            
            # Clean up values file
            if values_file:
                import os
                os.unlink(values_file)
                
            return {
                "status": "success",
                "message": f"Helm release {name} upgraded with chart {chart}",
                "details": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to upgrade Helm chart: {str(e)}"
            }
            
    def uninstall_helm_chart(self, name: str, namespace: str) -> Dict[str, Any]:
        """Uninstall a Helm release."""
        try:
            # Build uninstall command
            uninstall_cmd = ["helm", "uninstall", name, "--namespace", namespace]
                
            # Run the uninstall command
            result = self.run_command(uninstall_cmd)
                
            return {
                "status": "success",
                "message": f"Helm release {name} uninstalled",
                "details": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to uninstall Helm chart: {str(e)}"
            }
            
    # Kubectl Utilities
    def explain_resource(self, resource: str, api_version: Optional[str] = None, 
                        recursive: bool = False) -> Dict[str, Any]:
        """Get documentation for a Kubernetes resource."""
        try:
            cmd = ["kubectl", "explain", resource]
            
            if api_version:
                cmd.extend(["--api-version", api_version])
                
            if recursive:
                cmd.append("--recursive")
                
            result = self.run_command(cmd)
            return {
                "status": "success",
                "explanation": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to explain resource: {str(e)}"
            }
            
    def list_api_resources(self, api_group: Optional[str] = None, 
                          namespaced: Optional[bool] = None,
                          verbs: Optional[List[str]] = None) -> Dict[str, Any]:
        """List the API resources available in the cluster."""
        try:
            cmd = ["kubectl", "api-resources"]
            
            if api_group:
                cmd.extend(["--api-group", api_group])
                
            if namespaced is not None:
                cmd.extend(["--namespaced", str(namespaced).lower()])
                
            if verbs:
                cmd.extend(["--verbs", ",".join(verbs)])
                
            result = self.run_command(cmd)
            
            # Parse the output into a structured format
            lines = result.strip().split('\n')
            if len(lines) < 2:  # Need at least header and one resource
                return {
                    "status": "success",
                    "resources": [],
                    "count": 0
                }
                
            # Parse the header to get column positions
            header = lines[0]
            name_end = header.find("SHORTNAMES")
            shortnames_end = header.find("APIVERSION")
            apiversion_end = header.find("NAMESPACED")
            namespaced_end = header.find("KIND")
            
            resources = []
            for line in lines[1:]:
                if not line.strip():
                    continue
                    
                name = line[:name_end].strip()
                shortnames = line[name_end:shortnames_end].strip()
                apiversion = line[shortnames_end:apiversion_end].strip()
                namespaced = line[apiversion_end:namespaced_end].strip().lower() == "true"
                kind = line[namespaced_end:].strip()
                
                resources.append({
                    "name": name,
                    "shortnames": shortnames.split(",") if shortnames else [],
                    "apiversion": apiversion,
                    "namespaced": namespaced,
                    "kind": kind
                })
                
            return {
                "status": "success",
                "resources": resources,
                "count": len(resources)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to list API resources: {str(e)}"
            }
            
    def describe_pod(self, pod_name: str, namespace: str = "default") -> Dict[str, Any]:
        """Describe a pod in detail."""
        try:
            pod = self.core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            
            # Get pod events
            field_selector = f"involvedObject.name={pod_name}"
            events = self.core_v1.list_namespaced_event(
                namespace=namespace,
                field_selector=field_selector
            )
            
            # Format pod details
            containers = []
            for container in pod.spec.containers:
                container_status = None
                for cs in pod.status.container_statuses or []:
                    if cs.name == container.name:
                        container_status = cs
                        break
                        
                # Get container resource limits and requests
                resources = {}
                if container.resources:
                    if container.resources.limits:
                        resources["limits"] = {
                            k: v for k, v in container.resources.limits.items()
                        }
                    if container.resources.requests:
                        resources["requests"] = {
                            k: v for k, v in container.resources.requests.items()
                        }
                
                # Get container state details
                state = {}
                if container_status and container_status.state:
                    if container_status.state.running:
                        state = {
                            "status": "running",
                            "started_at": str(container_status.state.running.started_at)
                        }
                    elif container_status.state.waiting:
                        state = {
                            "status": "waiting",
                            "reason": container_status.state.waiting.reason,
                            "message": container_status.state.waiting.message
                        }
                    elif container_status.state.terminated:
                        state = {
                            "status": "terminated",
                            "reason": container_status.state.terminated.reason,
                            "exit_code": container_status.state.terminated.exit_code,
                            "message": container_status.state.terminated.message
                        }
                
                # Format container information
                container_info = {
                    "name": container.name,
                    "image": container.image,
                    "ports": [{"container_port": p.container_port, "protocol": p.protocol} 
                             for p in (container.ports or [])],
                    "command": container.command,
                    "args": container.args,
                    "resources": resources,
                    "liveness_probe": bool(container.liveness_probe),
                    "readiness_probe": bool(container.readiness_probe),
                    "startup_probe": bool(container.startup_probe),
                    "environment": [{"name": env.name, "value": env.value if hasattr(env, "value") else "[secretKeyRef]"} 
                                  for env in (container.env or [])],
                    "volume_mounts": [{"name": vm.name, "mount_path": vm.mount_path, 
                                       "readonly": vm.read_only if hasattr(vm, "read_only") else False} 
                                     for vm in (container.volume_mounts or [])],
                    "state": state,
                    "ready": container_status.ready if container_status else None,
                    "restart_count": container_status.restart_count if container_status else None,
                    "image_id": container_status.image_id if container_status else None,
                    "container_id": container_status.container_id if container_status else None
                }
                containers.append(container_info)
                
            # Format pod conditions
            conditions = []
            for condition in pod.status.conditions or []:
                condition_info = {
                    "type": condition.type,
                    "status": condition.status,
                    "last_transition_time": str(condition.last_transition_time),
                    "reason": condition.reason,
                    "message": condition.message
                }
                conditions.append(condition_info)
                
            # Format volumes
            volumes = []
            for volume in pod.spec.volumes or []:
                volume_info = {
                    "name": volume.name,
                    "type": self._get_volume_type(volume)
                }
                volumes.append(volume_info)
                
            # Format pod events
            formatted_events = []
            for event in events.items:
                event_info = {
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "count": event.count,
                    "first_timestamp": str(event.first_timestamp),
                    "last_timestamp": str(event.last_timestamp)
                }
                formatted_events.append(event_info)
                
            # Build the complete pod description
            pod_description = {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "uid": pod.metadata.uid,
                "resource_version": pod.metadata.resource_version,
                "creation_timestamp": str(pod.metadata.creation_timestamp),
                "labels": pod.metadata.labels,
                "annotations": pod.metadata.annotations,
                "owner_references": [{
                    "kind": ref.kind,
                    "name": ref.name,
                    "uid": ref.uid
                } for ref in (pod.metadata.owner_references or [])],
                "status": {
                    "phase": pod.status.phase,
                    "pod_ip": pod.status.pod_ip,
                    "host_ip": pod.status.host_ip,
                    "qos_class": pod.status.qos_class,
                    "conditions": conditions,
                    "start_time": str(pod.status.start_time) if pod.status.start_time else None
                },
                "spec": {
                    "node_name": pod.spec.node_name,
                    "service_account_name": pod.spec.service_account_name,
                    "restart_policy": pod.spec.restart_policy,
                    "termination_grace_period_seconds": pod.spec.termination_grace_period_seconds,
                    "dns_policy": pod.spec.dns_policy,
                    "priority": pod.spec.priority,
                    "security_context": {
                        "run_as_user": pod.spec.security_context.run_as_user if pod.spec.security_context else None,
                        "run_as_group": pod.spec.security_context.run_as_group if pod.spec.security_context else None,
                        "fs_group": pod.spec.security_context.fs_group if pod.spec.security_context else None
                    } if pod.spec.security_context else None,
                    "volumes": volumes
                },
                "containers": containers,
                "events": formatted_events
            }
            
            return {
                "status": "success",
                "pod": pod_description
            }
        except ApiException as e:
            if e.status == 404:
                return {
                    "status": "error",
                    "error": f"Pod {pod_name} not found in namespace {namespace}"
                }
            return {
                "status": "error",
                "error": f"Failed to describe pod: {e.reason}"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to describe pod: {str(e)}"
            }
            
    def _get_volume_type(self, volume) -> str:
        """Helper to get the volume type."""
        volume_types = [
            "host_path", "empty_dir", "gce_persistent_disk", "aws_elastic_block_store",
            "secret", "nfs", "iscsi", "glusterfs", "persistent_volume_claim",
            "rbd", "flex_volume", "cinder", "ceph_fs", "flocker", "downward_api",
            "fc", "azure_file", "config_map", "vsphere_volume", "quobyte", "azure_disk",
            "photon_persistent_disk", "projected", "portworx_volume", "scaleio",
            "storageos", "csi"
        ]
        
        for vol_type in volume_types:
            if hasattr(volume, vol_type) and getattr(volume, vol_type) is not None:
                return vol_type
        
        return "unknown"

    # Helper Methods
    @staticmethod
    def _encode_secret(value: str) -> str:
        """Encode a string to base64."""
        import base64
        return base64.b64encode(value.encode()).decode()

    @staticmethod
    def _decode_secret(value: str) -> str:
        """Decode a base64 string."""
        import base64
        return base64.b64decode(value.encode()).decode()

    def explain_error(self, error_msg: str) -> Dict[str, Any]:
        """Translate Kubernetes errors into plain English."""
        common_errors = {
            "ImagePullBackOff": "The container image couldn't be pulled. Check image name, registry access, and credentials.",
            "CrashLoopBackOff": "The pod is crashing repeatedly. Check container logs for errors.",
            "CreateContainerConfigError": "Failed to create container. Check container configuration and secrets.",
            "InvalidImageName": "The container image name is invalid. Check the image reference format.",
        }

        for error_pattern, explanation in common_errors.items():
            if error_pattern.lower() in error_msg.lower():
                return {
                    "error": error_pattern,
                    "explanation": explanation,
                    "suggestions": self._get_error_suggestions(error_pattern)
                }

        return {
            "error": "Unknown error",
            "explanation": error_msg,
            "suggestions": ["Check pod logs and events for more details"]
        }

    @staticmethod
    def _get_error_suggestions(error_type: str) -> List[str]:
        """Get suggestions for fixing common errors."""
        suggestions = {
            "ImagePullBackOff": [
                "Verify the image name and tag",
                "Check if the image registry is accessible",
                "Verify registry credentials (imagePullSecrets)",
                "Try pulling the image locally to validate access"
            ],
            "CrashLoopBackOff": [
                "Check container logs: kubectl logs <pod-name>",
                "Verify container command and arguments",
                "Check resource limits and requests",
                "Verify environment variables and configurations"
            ],
            "CreateContainerConfigError": [
                "Verify ConfigMap and Secret references",
                "Check volume mount configurations",
                "Validate environment variable references",
                "Check RBAC permissions"
            ],
            "InvalidImageName": [
                "Check image name format",
                "Verify registry URL format",
                "Check for typos in image reference",
                "Validate image tag format"
            ]
        }
        return suggestions.get(error_type, ["Check pod logs and events for more details"]) 