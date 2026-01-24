import logging
import subprocess
import shlex
import tempfile
import os
from typing import Any, Dict, List, Optional

from mcp.types import ToolAnnotations

logger = logging.getLogger("mcp-server")


def _get_kubectl_context_args(context: str) -> List[str]:
    """Get kubectl context arguments if context is specified."""
    if context:
        return ["--context", context]
    return []


def register_operations_tools(server, non_destructive: bool):
    """Register kubectl operations tools (apply, describe, patch, etc.)."""

    def check_destructive():
        """Check if operation is blocked in non-destructive mode."""
        if non_destructive:
            return {"success": False, "error": "Operation blocked: non-destructive mode enabled"}
        return None

    @server.tool(
        annotations=ToolAnnotations(
            title="Kubectl Apply",
            destructiveHint=True,
        ),
    )
    def kubectl_apply(manifest: str, namespace: Optional[str] = "default", context: str = "") -> Dict[str, Any]:
        """Apply a YAML manifest to the cluster.

        Args:
            manifest: YAML manifest content to apply
            namespace: Target namespace
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        blocked = check_destructive()
        if blocked:
            return blocked
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(manifest)
                temp_path = f.name

            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["apply", "-f", temp_path, "-n", namespace]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            os.unlink(temp_path)

            if result.returncode == 0:
                return {"success": True, "context": context or "current", "output": result.stdout.strip()}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error applying manifest: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Kubectl Describe",
            readOnlyHint=True,
        ),
    )
    def kubectl_describe(resource_type: str, name: str, namespace: Optional[str] = "default", context: str = "") -> Dict[str, Any]:
        """Describe a Kubernetes resource in detail.

        Args:
            resource_type: Type of resource (e.g., pod, deployment, service)
            name: Name of the resource
            namespace: Target namespace
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["describe", resource_type, name, "-n", namespace]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {"success": True, "context": context or "current", "description": result.stdout}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error describing resource: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Kubectl Generic",
            readOnlyHint=True,
        ),
    )
    def kubectl_generic(command: str, context: str = "") -> Dict[str, Any]:
        """Execute any kubectl command. Use with caution.

        Args:
            command: kubectl command to execute (without kubectl prefix)
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            # Security: validate command starts with allowed operations
            allowed_prefixes = [
                "get", "describe", "logs", "top", "explain", "api-resources",
                "config", "version", "cluster-info", "auth"
            ]
            cmd_parts = shlex.split(command)
            if not cmd_parts:
                return {"success": False, "error": "Empty command"}

            # Remove 'kubectl' prefix if present
            if cmd_parts[0] == "kubectl":
                cmd_parts = cmd_parts[1:]

            if not cmd_parts or cmd_parts[0] not in allowed_prefixes:
                return {
                    "success": False,
                    "error": f"Command not allowed. Allowed: {', '.join(allowed_prefixes)}"
                }

            full_cmd = ["kubectl"] + _get_kubectl_context_args(context) + cmd_parts
            result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)

            return {
                "success": result.returncode == 0,
                "context": context or "current",
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            logger.error(f"Error running kubectl command: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Kubectl Patch",
            destructiveHint=True,
        ),
    )
    def kubectl_patch(resource_type: str, name: str, patch: str, patch_type: str = "strategic", namespace: Optional[str] = "default", context: str = "") -> Dict[str, Any]:
        """Patch a Kubernetes resource.

        Args:
            resource_type: Type of resource to patch
            name: Name of the resource
            patch: JSON patch content
            patch_type: Type of patch (strategic, merge, json)
            namespace: Target namespace
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        blocked = check_destructive()
        if blocked:
            return blocked
        try:
            type_flag = {
                "strategic": "strategic",
                "merge": "merge",
                "json": "json"
            }.get(patch_type, "strategic")

            cmd = ["kubectl"] + _get_kubectl_context_args(context) + [
                "patch", resource_type, name,
                "-n", namespace,
                "--type", type_flag,
                "-p", patch
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {"success": True, "context": context or "current", "output": result.stdout.strip()}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error patching resource: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Kubectl Rollout",
            destructiveHint=True,
        ),
    )
    def kubectl_rollout(action: str, resource_type: str, name: str, namespace: Optional[str] = "default", context: str = "") -> Dict[str, Any]:
        """Manage rollouts (restart, status, history, undo, pause, resume).

        Args:
            action: Rollout action (status, history, restart, undo, pause, resume)
            resource_type: Type of resource (deployment, statefulset, daemonset)
            name: Name of the resource
            namespace: Target namespace
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            allowed_actions = ["status", "history", "restart", "undo", "pause", "resume"]
            if action not in allowed_actions:
                return {"success": False, "error": f"Invalid action. Allowed: {', '.join(allowed_actions)}"}

            # Destructive actions need check
            if action in ["restart", "undo", "pause", "resume"]:
                blocked = check_destructive()
                if blocked:
                    return blocked

            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["rollout", action, f"{resource_type}/{name}", "-n", namespace]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return {"success": True, "context": context or "current", "output": result.stdout.strip()}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error managing rollout: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Kubectl Create",
            destructiveHint=True,
        ),
    )
    def kubectl_create(resource_type: str, name: str, namespace: Optional[str] = "default", image: Optional[str] = None, context: str = "") -> Dict[str, Any]:
        """Create a Kubernetes resource.

        Args:
            resource_type: Type of resource to create
            name: Name of the resource
            namespace: Target namespace
            image: Container image (for deployment/pod)
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        blocked = check_destructive()
        if blocked:
            return blocked
        try:
            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["create", resource_type, name, "-n", namespace]
            if image and resource_type in ["deployment", "pod"]:
                cmd.extend(["--image", image])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {"success": True, "context": context or "current", "output": result.stdout.strip()}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error creating resource: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Delete Resource",
            destructiveHint=True,
        ),
    )
    def delete_resource(resource_type: str, name: str, namespace: Optional[str] = "default", context: str = "") -> Dict[str, Any]:
        """Delete a Kubernetes resource.

        Args:
            resource_type: Type of resource to delete
            name: Name of the resource
            namespace: Target namespace
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        blocked = check_destructive()
        if blocked:
            return blocked
        try:
            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["delete", resource_type, name, "-n", namespace]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {"success": True, "context": context or "current", "message": f"Deleted {resource_type}/{name}"}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error deleting resource: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Kubectl Copy",
            destructiveHint=True,
        ),
    )
    def kubectl_cp(source: str, destination: str, namespace: str = "default", container: Optional[str] = None, context: str = "") -> Dict[str, Any]:
        """Copy files between local filesystem and pods.

        Use pod:path format for pod paths, e.g.:
        - Local to pod: kubectl_cp("/tmp/file.txt", "mypod:/tmp/file.txt")
        - Pod to local: kubectl_cp("mypod:/tmp/file.txt", "/tmp/file.txt")

        Args:
            source: Source path (local path or pod:path)
            destination: Destination path (local path or pod:path)
            namespace: Target namespace
            container: Container name (optional)
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        blocked = check_destructive()
        if blocked:
            return blocked
        try:
            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["cp", source, destination, "-n", namespace]
            if container:
                cmd.extend(["-c", container])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                return {"success": True, "context": context or "current", "message": f"Copied {source} to {destination}"}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error copying files: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Backup Resource as YAML",
            readOnlyHint=True,
        ),
    )
    def backup_resource(resource_type: str, name: str, namespace: Optional[str] = None, context: str = "") -> Dict[str, Any]:
        """Export a resource as YAML for backup or migration.

        Args:
            resource_type: Type of resource to export
            name: Name of the resource
            namespace: Target namespace (optional)
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["get", resource_type, name, "-o", "yaml"]
            if namespace:
                cmd.extend(["-n", namespace])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip()}

            return {
                "success": True,
                "context": context or "current",
                "resource": {
                    "type": resource_type,
                    "name": name,
                    "namespace": namespace
                },
                "yaml": result.stdout,
                "hint": "Save this YAML to a file and use 'kubectl apply -f' to restore"
            }
        except Exception as e:
            logger.error(f"Error backing up resource: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Label Resource",
            destructiveHint=True,
        ),
    )
    def label_resource(
        resource_type: str,
        name: str,
        labels: Dict[str, str],
        namespace: Optional[str] = None,
        overwrite: bool = False,
        context: str = ""
    ) -> Dict[str, Any]:
        """Add or update labels on a resource.

        Args:
            resource_type: Type of resource to label
            name: Name of the resource
            labels: Labels to apply (use None value to remove a label)
            namespace: Target namespace (optional)
            overwrite: Overwrite existing labels
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        blocked = check_destructive()
        if blocked:
            return blocked
        try:
            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["label", resource_type, name]
            if namespace:
                cmd.extend(["-n", namespace])

            for key, value in labels.items():
                if value is None:
                    cmd.append(f"{key}-")  # Remove label
                else:
                    cmd.append(f"{key}={value}")

            if overwrite:
                cmd.append("--overwrite")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip()}

            return {
                "success": True,
                "context": context or "current",
                "message": result.stdout.strip(),
                "resource": {"type": resource_type, "name": name, "namespace": namespace},
                "appliedLabels": labels
            }
        except Exception as e:
            logger.error(f"Error labeling resource: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Annotate Resource",
            destructiveHint=True,
        ),
    )
    def annotate_resource(
        resource_type: str,
        name: str,
        annotations: Dict[str, str],
        namespace: Optional[str] = None,
        overwrite: bool = False,
        context: str = ""
    ) -> Dict[str, Any]:
        """Add or update annotations on a resource.

        Args:
            resource_type: Type of resource to annotate
            name: Name of the resource
            annotations: Annotations to apply (use None value to remove)
            namespace: Target namespace (optional)
            overwrite: Overwrite existing annotations
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        blocked = check_destructive()
        if blocked:
            return blocked
        try:
            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["annotate", resource_type, name]
            if namespace:
                cmd.extend(["-n", namespace])

            for key, value in annotations.items():
                if value is None:
                    cmd.append(f"{key}-")  # Remove annotation
                else:
                    cmd.append(f"{key}={value}")

            if overwrite:
                cmd.append("--overwrite")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip()}

            return {
                "success": True,
                "context": context or "current",
                "message": result.stdout.strip(),
                "resource": {"type": resource_type, "name": name, "namespace": namespace},
                "appliedAnnotations": annotations
            }
        except Exception as e:
            logger.error(f"Error annotating resource: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Taint Node",
            destructiveHint=True,
        ),
    )
    def taint_node(
        node_name: str,
        key: str,
        value: Optional[str] = None,
        effect: str = "NoSchedule",
        remove: bool = False,
        context: str = ""
    ) -> Dict[str, Any]:
        """Add or remove taints on a node.

        Args:
            node_name: Name of the node
            key: Taint key
            value: Taint value (optional)
            effect: Taint effect (NoSchedule, PreferNoSchedule, NoExecute)
            remove: Remove the taint instead of adding
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        blocked = check_destructive()
        if blocked:
            return blocked
        try:
            if effect not in ["NoSchedule", "PreferNoSchedule", "NoExecute"]:
                return {"success": False, "error": f"Invalid effect: {effect}. Must be NoSchedule, PreferNoSchedule, or NoExecute"}

            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["taint", "nodes", node_name]

            if remove:
                taint_str = f"{key}:{effect}-"
            else:
                if value:
                    taint_str = f"{key}={value}:{effect}"
                else:
                    taint_str = f"{key}:{effect}"

            cmd.append(taint_str)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip()}

            return {
                "success": True,
                "context": context or "current",
                "message": result.stdout.strip(),
                "node": node_name,
                "action": "removed" if remove else "added",
                "taint": {"key": key, "value": value, "effect": effect}
            }
        except Exception as e:
            logger.error(f"Error tainting node: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Wait for Condition",
            readOnlyHint=True,
        ),
    )
    def wait_for_condition(
        resource_type: str,
        name: str,
        condition: str,
        namespace: Optional[str] = None,
        timeout: int = 60,
        context: str = ""
    ) -> Dict[str, Any]:
        """Wait for a resource to reach a specific condition.

        Args:
            resource_type: Type of resource to wait for
            name: Name of the resource
            condition: Condition to wait for (e.g., condition=Ready, delete)
            namespace: Target namespace (optional)
            timeout: Timeout in seconds
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["wait", f"{resource_type}/{name}", f"--for={condition}", f"--timeout={timeout}s"]
            if namespace:
                cmd.extend(["-n", namespace])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)

            if result.returncode != 0:
                return {
                    "success": False,
                    "conditionMet": False,
                    "error": result.stderr.strip(),
                    "context": context or "current",
                    "resource": {"type": resource_type, "name": name, "namespace": namespace},
                    "condition": condition
                }

            return {
                "success": True,
                "conditionMet": True,
                "context": context or "current",
                "message": result.stdout.strip(),
                "resource": {"type": resource_type, "name": name, "namespace": namespace},
                "condition": condition
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "conditionMet": False,
                "error": f"Timeout waiting for condition '{condition}' after {timeout}s",
                "context": context or "current",
                "resource": {"type": resource_type, "name": name, "namespace": namespace}
            }
        except Exception as e:
            logger.error(f"Error waiting for condition: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Node Management",
            destructiveHint=True,
        ),
    )
    def node_management(action: str, node_name: str, force: bool = False, context: str = "") -> Dict[str, Any]:
        """Manage nodes: cordon, uncordon, or drain.

        Args:
            action: Action to perform (cordon, uncordon, drain)
            node_name: Name of the node
            force: Force drain (for drain action)
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        blocked = check_destructive()
        if blocked:
            return blocked
        try:
            allowed_actions = ["cordon", "uncordon", "drain"]
            if action not in allowed_actions:
                return {"success": False, "error": f"Invalid action. Allowed: {', '.join(allowed_actions)}"}

            cmd = ["kubectl"] + _get_kubectl_context_args(context) + [action, node_name]
            if action == "drain":
                cmd.extend(["--ignore-daemonsets", "--delete-emptydir-data"])
                if force:
                    cmd.append("--force")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                return {"success": True, "context": context or "current", "output": result.stdout.strip()}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error managing node: {e}")
            return {"success": False, "error": str(e)}
