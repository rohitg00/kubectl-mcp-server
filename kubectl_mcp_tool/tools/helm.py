import json
import logging
import os
import subprocess
import tempfile
from typing import Any, Callable, Dict, List, Optional

import yaml
from mcp.types import ToolAnnotations

logger = logging.getLogger("mcp-server")


def _get_helm_context_args(context: str) -> List[str]:
    """Get helm kube-context arguments if context is specified."""
    if context:
        return ["--kube-context", context]
    return []


def _get_kubectl_context_args(context: str) -> List[str]:
    """Get kubectl context arguments if context is specified."""
    if context:
        return ["--context", context]
    return []


def register_helm_tools(
    server,
    non_destructive: bool,
    check_helm_fn: Callable[[], bool]
):
    """Register all Helm-related tools with the MCP server.

    Args:
        server: FastMCP server instance
        non_destructive: If True, block destructive operations
        check_helm_fn: Function to check if Helm is available
    """

    @server.tool(
        annotations=ToolAnnotations(
            title="Install Helm Chart",
            destructiveHint=True,
        ),
    )
    def install_helm_chart(
        name: str,
        chart: str,
        namespace: str,
        repo: Optional[str] = None,
        values: Optional[dict] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Install a Helm chart.

        Args:
            name: Release name
            chart: Chart reference
            namespace: Target namespace
            repo: Repository in format 'repo_name=repo_url'
            values: Values to override
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        if non_destructive:
            return {"success": False, "error": "Blocked: non-destructive mode"}
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            if repo:
                try:
                    repo_parts = repo.split('=')
                    if len(repo_parts) != 2:
                        return {"success": False, "error": "Repository format should be 'repo_name=repo_url'"}

                    repo_name, repo_url = repo_parts
                    repo_add_cmd = ["helm", "repo", "add", repo_name, repo_url]
                    logger.debug(f"Running command: {' '.join(repo_add_cmd)}")
                    subprocess.check_output(repo_add_cmd, stderr=subprocess.PIPE, text=True)

                    repo_update_cmd = ["helm", "repo", "update"]
                    logger.debug(f"Running command: {' '.join(repo_update_cmd)}")
                    subprocess.check_output(repo_update_cmd, stderr=subprocess.PIPE, text=True)

                    if '/' not in chart:
                        chart = f"{repo_name}/{chart}"
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error adding Helm repo: {e.stderr if hasattr(e, 'stderr') else str(e)}")
                    return {"success": False, "error": f"Failed to add Helm repo: {e.stderr if hasattr(e, 'stderr') else str(e)}"}

            cmd = ["helm"] + _get_helm_context_args(context) + ["install", name, chart, "-n", namespace]

            try:
                ns_cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["get", "namespace", namespace]
                subprocess.check_output(ns_cmd, stderr=subprocess.PIPE, text=True)
            except subprocess.CalledProcessError:
                logger.info(f"Namespace {namespace} not found, creating it")
                create_ns_cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["create", "namespace", namespace]
                try:
                    subprocess.check_output(create_ns_cmd, stderr=subprocess.PIPE, text=True)
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error creating namespace: {e.stderr if hasattr(e, 'stderr') else str(e)}")
                    return {"success": False, "error": f"Failed to create namespace: {e.stderr if hasattr(e, 'stderr') else str(e)}"}

            values_file = None
            try:
                if values:
                    with tempfile.NamedTemporaryFile("w", delete=False) as f:
                        yaml.dump(values, f)
                        values_file = f.name
                    cmd += ["-f", values_file]

                logger.debug(f"Running command: {' '.join(cmd)}")
                result = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True)

                return {
                    "success": True,
                    "context": context or "current",
                    "message": f"Helm chart {chart} installed as {name} in {namespace}",
                    "details": result
                }
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
                logger.error(f"Error installing Helm chart: {error_msg}")
                return {"success": False, "error": f"Failed to install Helm chart: {error_msg}"}
            finally:
                if values_file and os.path.exists(values_file):
                    os.unlink(values_file)
        except Exception as e:
            logger.error(f"Unexpected error installing Helm chart: {str(e)}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    @server.tool(
        annotations=ToolAnnotations(
            title="Upgrade Helm Chart",
            destructiveHint=True,
        ),
    )
    def upgrade_helm_chart(
        name: str,
        chart: str,
        namespace: str,
        repo: Optional[str] = None,
        values: Optional[dict] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Upgrade a Helm release.

        Args:
            name: Release name
            chart: Chart reference
            namespace: Target namespace
            repo: Repository in format 'repo_name=repo_url'
            values: Values to override
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        if non_destructive:
            return {"success": False, "error": "Blocked: non-destructive mode"}
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            if repo:
                try:
                    repo_parts = repo.split('=')
                    if len(repo_parts) != 2:
                        return {"success": False, "error": "Repository format should be 'repo_name=repo_url'"}

                    repo_name, repo_url = repo_parts
                    repo_add_cmd = ["helm", "repo", "add", repo_name, repo_url]
                    logger.debug(f"Running command: {' '.join(repo_add_cmd)}")
                    subprocess.check_output(repo_add_cmd, stderr=subprocess.PIPE, text=True)

                    repo_update_cmd = ["helm", "repo", "update"]
                    logger.debug(f"Running command: {' '.join(repo_update_cmd)}")
                    subprocess.check_output(repo_update_cmd, stderr=subprocess.PIPE, text=True)

                    if '/' not in chart:
                        chart = f"{repo_name}/{chart}"
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error adding Helm repo: {e.stderr if hasattr(e, 'stderr') else str(e)}")
                    return {"success": False, "error": f"Failed to add Helm repo: {e.stderr if hasattr(e, 'stderr') else str(e)}"}

            cmd = ["helm"] + _get_helm_context_args(context) + ["upgrade", name, chart, "-n", namespace]

            values_file = None
            try:
                if values:
                    with tempfile.NamedTemporaryFile("w", delete=False) as f:
                        yaml.dump(values, f)
                        values_file = f.name
                    cmd += ["-f", values_file]

                logger.debug(f"Running command: {' '.join(cmd)}")
                result = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True)

                return {
                    "success": True,
                    "context": context or "current",
                    "message": f"Helm release {name} upgraded with chart {chart} in {namespace}",
                    "details": result
                }
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
                logger.error(f"Error upgrading Helm chart: {error_msg}")
                return {"success": False, "error": f"Failed to upgrade Helm chart: {error_msg}"}
            finally:
                if values_file and os.path.exists(values_file):
                    os.unlink(values_file)
        except Exception as e:
            logger.error(f"Unexpected error upgrading Helm chart: {str(e)}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    @server.tool(
        annotations=ToolAnnotations(
            title="Uninstall Helm Chart",
            destructiveHint=True,
        ),
    )
    def uninstall_helm_chart(name: str, namespace: str, context: str = "") -> Dict[str, Any]:
        """Uninstall a Helm release.

        Args:
            name: Release name to uninstall
            namespace: Target namespace
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        if non_destructive:
            return {"success": False, "error": "Blocked: non-destructive mode"}
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm"] + _get_helm_context_args(context) + ["uninstall", name, "-n", namespace]
            logger.debug(f"Running command: {' '.join(cmd)}")

            try:
                result = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True)
                return {
                    "success": True,
                    "context": context or "current",
                    "message": f"Helm release {name} uninstalled from {namespace}",
                    "details": result
                }
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
                logger.error(f"Error uninstalling Helm chart: {error_msg}")
                return {"success": False, "error": f"Failed to uninstall Helm chart: {error_msg}"}
        except Exception as e:
            logger.error(f"Unexpected error uninstalling Helm chart: {str(e)}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    @server.tool(
        annotations=ToolAnnotations(
            title="List Helm Releases",
            readOnlyHint=True,
        ),
    )
    def helm_list(
        namespace: Optional[str] = None,
        all_namespaces: bool = False,
        filter: Optional[str] = None,
        deployed: bool = False,
        failed: bool = False,
        pending: bool = False,
        uninstalled: bool = False,
        superseded: bool = False,
        context: str = ""
    ) -> Dict[str, Any]:
        """List Helm releases with optional filtering.

        Args:
            namespace: Target namespace (default: current namespace)
            all_namespaces: List releases across all namespaces
            filter: Filter releases by name using regex
            deployed: Show deployed releases only
            failed: Show failed releases only
            pending: Show pending releases only
            uninstalled: Show uninstalled releases (if kept with --keep-history)
            superseded: Show superseded releases only
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm"] + _get_helm_context_args(context) + ["list", "--output", "json"]

            if all_namespaces:
                cmd.append("--all-namespaces")
            elif namespace:
                cmd.extend(["-n", namespace])

            if filter:
                cmd.extend(["--filter", filter])
            if deployed:
                cmd.append("--deployed")
            if failed:
                cmd.append("--failed")
            if pending:
                cmd.append("--pending")
            if uninstalled:
                cmd.append("--uninstalled")
            if superseded:
                cmd.append("--superseded")

            if not any([deployed, failed, pending, uninstalled, superseded]):
                cmd.append("--all")

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                releases = json.loads(result.stdout) if result.stdout.strip() else []
                return {
                    "success": True,
                    "context": context or "current",
                    "releases": releases,
                    "count": len(releases)
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error listing Helm releases: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Release Status",
            readOnlyHint=True,
        ),
    )
    def helm_status(
        release_name: str,
        namespace: str = "default",
        revision: Optional[int] = None,
        show_desc: bool = False,
        show_resources: bool = False,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get the status of a Helm release.

        Args:
            release_name: Name of the release
            namespace: Kubernetes namespace
            revision: Show status for a specific revision (default: latest)
            show_desc: Show description of the release
            show_resources: Show resources created by the release
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm"] + _get_helm_context_args(context) + ["status", release_name, "-n", namespace, "--output", "json"]

            if revision:
                cmd.extend(["--revision", str(revision)])
            if show_desc:
                cmd.append("--show-desc")
            if show_resources:
                cmd.append("--show-resources")

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                status = json.loads(result.stdout) if result.stdout.strip() else {}
                return {"success": True, "context": context or "current", "status": status}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error getting Helm status: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Release History",
            readOnlyHint=True,
        ),
    )
    def helm_history(
        release_name: str,
        namespace: str = "default",
        max_revisions: int = 256,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get the revision history of a Helm release.

        Args:
            release_name: Name of the release
            namespace: Kubernetes namespace
            max_revisions: Maximum number of revisions to return
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm"] + _get_helm_context_args(context) + ["history", release_name, "-n", namespace, "--output", "json", "--max", str(max_revisions)]

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                history = json.loads(result.stdout) if result.stdout.strip() else []
                return {
                    "success": True,
                    "context": context or "current",
                    "history": history,
                    "revisions": len(history)
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error getting Helm history: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Get Values",
            readOnlyHint=True,
        ),
    )
    def helm_get_values(
        release_name: str,
        namespace: str = "default",
        all_values: bool = False,
        revision: Optional[int] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get the values used for a Helm release.

        Args:
            release_name: Name of the release
            namespace: Kubernetes namespace
            all_values: Include computed (default + user) values
            revision: Get values for a specific revision
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm"] + _get_helm_context_args(context) + ["get", "values", release_name, "-n", namespace, "--output", "yaml"]

            if all_values:
                cmd.append("--all")
            if revision:
                cmd.extend(["--revision", str(revision)])

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                values = yaml.safe_load(result.stdout) if result.stdout.strip() else {}
                return {"success": True, "context": context or "current", "values": values, "raw": result.stdout}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error getting Helm values: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Get Manifest",
            readOnlyHint=True,
        ),
    )
    def helm_get_manifest(
        release_name: str,
        namespace: str = "default",
        revision: Optional[int] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get the manifest (rendered templates) of a Helm release.

        Args:
            release_name: Name of the release
            namespace: Kubernetes namespace
            revision: Get manifest for a specific revision
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm"] + _get_helm_context_args(context) + ["get", "manifest", release_name, "-n", namespace]

            if revision:
                cmd.extend(["--revision", str(revision)])

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {"success": True, "context": context or "current", "manifest": result.stdout}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error getting Helm manifest: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Get Notes",
            readOnlyHint=True,
        ),
    )
    def helm_get_notes(
        release_name: str,
        namespace: str = "default",
        revision: Optional[int] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get the notes (post-install message) of a Helm release.

        Args:
            release_name: Name of the release
            namespace: Kubernetes namespace
            revision: Get notes for a specific revision
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm"] + _get_helm_context_args(context) + ["get", "notes", release_name, "-n", namespace]

            if revision:
                cmd.extend(["--revision", str(revision)])

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {"success": True, "context": context or "current", "notes": result.stdout}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error getting Helm notes: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Get Hooks",
            readOnlyHint=True,
        ),
    )
    def helm_get_hooks(
        release_name: str,
        namespace: str = "default",
        revision: Optional[int] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get the hooks of a Helm release.

        Args:
            release_name: Name of the release
            namespace: Kubernetes namespace
            revision: Get hooks for a specific revision
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm"] + _get_helm_context_args(context) + ["get", "hooks", release_name, "-n", namespace]

            if revision:
                cmd.extend(["--revision", str(revision)])

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {"success": True, "context": context or "current", "hooks": result.stdout}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error getting Helm hooks: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Get All",
            readOnlyHint=True,
        ),
    )
    def helm_get_all(
        release_name: str,
        namespace: str = "default",
        revision: Optional[int] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get all information about a Helm release (values, manifest, hooks, notes).

        Args:
            release_name: Name of the release
            namespace: Kubernetes namespace
            revision: Get info for a specific revision
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm"] + _get_helm_context_args(context) + ["get", "all", release_name, "-n", namespace]

            if revision:
                cmd.extend(["--revision", str(revision)])

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return {"success": True, "context": context or "current", "release_info": result.stdout}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error getting all Helm info: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Show Chart",
            readOnlyHint=True,
        ),
    )
    def helm_show_chart(
        chart: str,
        repo: Optional[str] = None,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Show the chart definition (Chart.yaml).

        Args:
            chart: Chart reference (e.g., 'nginx', 'bitnami/nginx', or local path)
            repo: Repository URL (for OCI or HTTP repos)
            version: Specific chart version
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "show", "chart", chart]

            if repo:
                cmd.extend(["--repo", repo])
            if version:
                cmd.extend(["--version", version])

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                chart_info = yaml.safe_load(result.stdout) if result.stdout.strip() else {}
                return {"success": True, "chart": chart_info, "raw": result.stdout}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error showing chart: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Show Values",
            readOnlyHint=True,
        ),
    )
    def helm_show_values(
        chart: str,
        repo: Optional[str] = None,
        version: Optional[str] = None,
        jsonpath: Optional[str] = None
    ) -> Dict[str, Any]:
        """Show the chart's default values.yaml.

        Args:
            chart: Chart reference (e.g., 'nginx', 'bitnami/nginx', or local path)
            repo: Repository URL
            version: Specific chart version
            jsonpath: JSONPath expression to filter values
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "show", "values", chart]

            if repo:
                cmd.extend(["--repo", repo])
            if version:
                cmd.extend(["--version", version])
            if jsonpath:
                cmd.extend(["--jsonpath", jsonpath])

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                values = yaml.safe_load(result.stdout) if result.stdout.strip() and not jsonpath else result.stdout
                return {"success": True, "values": values, "raw": result.stdout}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error showing chart values: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Show Readme",
            readOnlyHint=True,
        ),
    )
    def helm_show_readme(
        chart: str,
        repo: Optional[str] = None,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Show the chart's README file.

        Args:
            chart: Chart reference (e.g., 'nginx', 'bitnami/nginx', or local path)
            repo: Repository URL
            version: Specific chart version
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "show", "readme", chart]

            if repo:
                cmd.extend(["--repo", repo])
            if version:
                cmd.extend(["--version", version])

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return {"success": True, "readme": result.stdout}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error showing chart readme: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Show CRDs",
            readOnlyHint=True,
        ),
    )
    def helm_show_crds(
        chart: str,
        repo: Optional[str] = None,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Show the chart's Custom Resource Definitions (CRDs).

        Args:
            chart: Chart reference
            repo: Repository URL
            version: Specific chart version
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "show", "crds", chart]

            if repo:
                cmd.extend(["--repo", repo])
            if version:
                cmd.extend(["--version", version])

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return {"success": True, "crds": result.stdout}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error showing chart CRDs: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Show All",
            readOnlyHint=True,
        ),
    )
    def helm_show_all(
        chart: str,
        repo: Optional[str] = None,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Show all chart information (chart.yaml, values, readme, crds).

        Args:
            chart: Chart reference
            repo: Repository URL
            version: Specific chart version
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "show", "all", chart]

            if repo:
                cmd.extend(["--repo", repo])
            if version:
                cmd.extend(["--version", version])

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return {"success": True, "chart_info": result.stdout}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error showing all chart info: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Search Repo",
            readOnlyHint=True,
        ),
    )
    def helm_search_repo(
        keyword: str,
        regexp: bool = False,
        versions: bool = False,
        version: Optional[str] = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """Search for charts in configured Helm repositories.

        Args:
            keyword: Search keyword
            regexp: Use regular expression for searching
            versions: Show all chart versions (not just latest)
            version: Version constraint (e.g., '>1.0.0')
            max_results: Maximum number of results
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "search", "repo", keyword, "--output", "json", "--max-col-width", "0"]

            if regexp:
                cmd.append("--regexp")
            if versions:
                cmd.append("--versions")
            if version:
                cmd.extend(["--version", version])

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                charts = json.loads(result.stdout) if result.stdout.strip() else []
                return {
                    "success": True,
                    "charts": charts[:max_results],
                    "count": len(charts[:max_results])
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error searching repos: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Search Hub",
            readOnlyHint=True,
        ),
    )
    def helm_search_hub(
        keyword: str,
        max_results: int = 50,
        list_repo_url: bool = True
    ) -> Dict[str, Any]:
        """Search for charts in Artifact Hub (https://artifacthub.io).

        Args:
            keyword: Search keyword
            max_results: Maximum number of results
            list_repo_url: Show repository URL for each chart
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "search", "hub", keyword, "--output", "json", "--max-col-width", "0"]

            if list_repo_url:
                cmd.append("--list-repo-url")

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                charts = json.loads(result.stdout) if result.stdout.strip() else []
                return {
                    "success": True,
                    "charts": charts[:max_results],
                    "count": len(charts[:max_results]),
                    "source": "Artifact Hub (artifacthub.io)"
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error searching Artifact Hub: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Repo List",
            readOnlyHint=True,
        ),
    )
    def helm_repo_list() -> Dict[str, Any]:
        """List all configured Helm repositories."""
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "repo", "list", "--output", "json"]

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                repos = json.loads(result.stdout) if result.stdout.strip() else []
                return {
                    "success": True,
                    "repositories": repos,
                    "count": len(repos)
                }
            else:
                if "no repositories to show" in result.stderr.lower():
                    return {"success": True, "repositories": [], "count": 0}
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error listing repos: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Repo Add",
            destructiveHint=False,
        ),
    )
    def helm_repo_add(
        name: str,
        url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        force_update: bool = False,
        pass_credentials: bool = False
    ) -> Dict[str, Any]:
        """Add a Helm chart repository.

        Args:
            name: Repository name (local alias)
            url: Repository URL
            username: Username for basic auth
            password: Password for basic auth
            force_update: Replace existing repo with same name
            pass_credentials: Pass credentials to all domains
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "repo", "add", name, url]

            if username:
                cmd.extend(["--username", username])
            if password:
                cmd.extend(["--password", password])
            if force_update:
                cmd.append("--force-update")
            if pass_credentials:
                cmd.append("--pass-credentials")

            logger.debug(f"Running command: {' '.join(cmd[:4])}...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Repository '{name}' added successfully",
                    "details": result.stdout.strip()
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error adding repo: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Repo Remove",
            destructiveHint=True,
        ),
    )
    def helm_repo_remove(name: str) -> Dict[str, Any]:
        """Remove a Helm chart repository.

        Args:
            name: Repository name to remove
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "repo", "remove", name]

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Repository '{name}' removed successfully",
                    "details": result.stdout.strip()
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error removing repo: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Repo Update",
            readOnlyHint=False,
        ),
    )
    def helm_repo_update(repos: Optional[List[str]] = None) -> Dict[str, Any]:
        """Update Helm repository indexes.

        Args:
            repos: Specific repositories to update (default: all)
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "repo", "update"]

            if repos:
                cmd.extend(repos)

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "Repositories updated successfully",
                    "details": result.stdout.strip()
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error updating repos: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Rollback",
            destructiveHint=True,
        ),
    )
    def helm_rollback(
        release_name: str,
        revision: int,
        namespace: str = "default",
        force: bool = False,
        recreate_pods: bool = False,
        cleanup_on_fail: bool = False,
        wait: bool = False,
        timeout: str = "5m0s",
        context: str = ""
    ) -> Dict[str, Any]:
        """Rollback a Helm release to a previous revision.

        Args:
            release_name: Name of the release
            revision: Revision number to rollback to (use helm_history to see revisions)
            namespace: Kubernetes namespace
            force: Force resource updates through delete/recreate
            recreate_pods: Force pod restarts
            cleanup_on_fail: Delete newly created resources on failure
            wait: Wait until all resources are ready
            timeout: Timeout for waiting
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        if non_destructive:
            return {"success": False, "error": "Blocked: non-destructive mode"}
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm"] + _get_helm_context_args(context) + ["rollback", release_name, str(revision), "-n", namespace]

            if force:
                cmd.append("--force")
            if recreate_pods:
                cmd.append("--recreate-pods")
            if cleanup_on_fail:
                cmd.append("--cleanup-on-fail")
            if wait:
                cmd.append("--wait")
                cmd.extend(["--timeout", timeout])

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                return {
                    "success": True,
                    "context": context or "current",
                    "message": f"Release '{release_name}' rolled back to revision {revision}",
                    "details": result.stdout.strip()
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error rolling back: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Test",
            readOnlyHint=False,
        ),
    )
    def helm_test(
        release_name: str,
        namespace: str = "default",
        timeout: str = "5m0s",
        logs: bool = True,
        filter: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Run tests for a Helm release.

        Args:
            release_name: Name of the release
            namespace: Kubernetes namespace
            timeout: Timeout for tests
            logs: Show test pod logs
            filter: Filter tests by name
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm"] + _get_helm_context_args(context) + ["test", release_name, "-n", namespace, "--timeout", timeout]

            if logs:
                cmd.append("--logs")
            if filter:
                cmd.extend(["--filter", filter])

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                return {
                    "success": True,
                    "context": context or "current",
                    "message": f"Tests passed for release '{release_name}'",
                    "output": result.stdout.strip()
                }
            else:
                return {
                    "success": False,
                    "error": "Tests failed",
                    "output": result.stdout.strip(),
                    "stderr": result.stderr.strip()
                }
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Lint",
            readOnlyHint=True,
        ),
    )
    def helm_lint(
        chart_path: str,
        values: Optional[str] = None,
        strict: bool = False,
        with_subcharts: bool = False
    ) -> Dict[str, Any]:
        """Lint a Helm chart for issues.

        Args:
            chart_path: Path to the chart directory
            values: Values file path or --set values
            strict: Fail on lint warnings
            with_subcharts: Lint dependent charts
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "lint", chart_path]

            if values:
                if values.endswith(('.yaml', '.yml', '.json')):
                    cmd.extend(["-f", values])
                else:
                    cmd.extend(["--set", values])
            if strict:
                cmd.append("--strict")
            if with_subcharts:
                cmd.append("--with-subcharts")

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "Chart linting passed",
                    "output": result.stdout.strip()
                }
            else:
                return {
                    "success": False,
                    "error": "Chart linting failed",
                    "output": result.stdout.strip(),
                    "stderr": result.stderr.strip()
                }
        except Exception as e:
            logger.error(f"Error linting chart: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Package",
            readOnlyHint=False,
        ),
    )
    def helm_package(
        chart_path: str,
        destination: Optional[str] = None,
        version: Optional[str] = None,
        app_version: Optional[str] = None,
        dependency_update: bool = False
    ) -> Dict[str, Any]:
        """Package a Helm chart into a versioned archive.

        Args:
            chart_path: Path to the chart directory
            destination: Output directory for the package
            version: Override the chart version
            app_version: Override the app version
            dependency_update: Update dependencies before packaging
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "package", chart_path]

            if destination:
                cmd.extend(["--destination", destination])
            if version:
                cmd.extend(["--version", version])
            if app_version:
                cmd.extend(["--app-version", app_version])
            if dependency_update:
                cmd.append("--dependency-update")

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "Chart packaged successfully",
                    "output": result.stdout.strip()
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error packaging chart: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Dependency Update",
            readOnlyHint=False,
        ),
    )
    def helm_dependency_update(chart_path: str, skip_refresh: bool = False) -> Dict[str, Any]:
        """Update chart dependencies (download from Chart.yaml).

        Args:
            chart_path: Path to the chart directory
            skip_refresh: Don't refresh repo cache
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "dependency", "update", chart_path]

            if skip_refresh:
                cmd.append("--skip-refresh")

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "Dependencies updated successfully",
                    "output": result.stdout.strip()
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error updating dependencies: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Dependency List",
            readOnlyHint=True,
        ),
    )
    def helm_dependency_list(chart_path: str) -> Dict[str, Any]:
        """List chart dependencies.

        Args:
            chart_path: Path to the chart directory
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "dependency", "list", chart_path]

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {
                    "success": True,
                    "dependencies": result.stdout.strip()
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error listing dependencies: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Dependency Build",
            readOnlyHint=False,
        ),
    )
    def helm_dependency_build(chart_path: str, skip_refresh: bool = False) -> Dict[str, Any]:
        """Build chart dependencies from Chart.lock.

        Args:
            chart_path: Path to the chart directory
            skip_refresh: Don't refresh repo cache
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "dependency", "build", chart_path]

            if skip_refresh:
                cmd.append("--skip-refresh")

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "Dependencies built successfully",
                    "output": result.stdout.strip()
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error building dependencies: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Pull",
            readOnlyHint=False,
        ),
    )
    def helm_pull(
        chart: str,
        repo: Optional[str] = None,
        version: Optional[str] = None,
        destination: Optional[str] = None,
        untar: bool = True
    ) -> Dict[str, Any]:
        """Download a chart from a repository.

        Args:
            chart: Chart reference (e.g., 'bitnami/nginx')
            repo: Repository URL
            version: Specific chart version
            destination: Download directory
            untar: Extract the chart archive
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "pull", chart]

            if repo:
                cmd.extend(["--repo", repo])
            if version:
                cmd.extend(["--version", version])
            if destination:
                cmd.extend(["--destination", destination])
            if untar:
                cmd.append("--untar")

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Chart '{chart}' downloaded successfully",
                    "output": result.stdout.strip() if result.stdout.strip() else "Download complete"
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error pulling chart: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Create",
            readOnlyHint=False,
        ),
    )
    def helm_create(name: str, starter: Optional[str] = None) -> Dict[str, Any]:
        """Create a new Helm chart with the given name.

        Args:
            name: Name of the chart to create
            starter: Name of the starter chart to use
        """
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "create", name]

            if starter:
                cmd.extend(["--starter", starter])

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Chart '{name}' created successfully",
                    "output": result.stdout.strip()
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Version",
            readOnlyHint=True,
        ),
    )
    def helm_version() -> Dict[str, Any]:
        """Get the Helm client version information."""
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "version", "--short"]

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return {
                    "success": True,
                    "version": result.stdout.strip()
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error getting Helm version: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Environment",
            readOnlyHint=True,
        ),
    )
    def helm_env() -> Dict[str, Any]:
        """Get Helm environment information (paths, settings)."""
        if not check_helm_fn():
            return {"success": False, "error": "Helm is not available on this system"}

        try:
            cmd = ["helm", "env"]

            logger.debug(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                env_dict = {}
                for line in result.stdout.strip().split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_dict[key] = value.strip('"')
                return {
                    "success": True,
                    "environment": env_dict,
                    "raw": result.stdout.strip()
                }
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error getting Helm environment: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Template",
            readOnlyHint=True,
        ),
    )
    def helm_template(
        chart: str,
        name: str,
        namespace: str = "default",
        repo: Optional[str] = None,
        values: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Render Helm chart templates locally without installing.

        Args:
            chart: Chart reference
            name: Release name for template
            namespace: Target namespace
            repo: Repository URL
            values: Set values on command line
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        try:
            cmd = ["helm"] + _get_helm_context_args(context) + ["template", name, chart, "-n", namespace]
            if repo:
                cmd.extend(["--repo", repo])
            if values:
                cmd.extend(["--set", values])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return {"success": True, "context": context or "current", "manifest": result.stdout}
            else:
                return {"success": False, "error": result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error templating chart: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Helm Template Apply",
            destructiveHint=True,
        ),
    )
    def helm_template_apply(
        chart: str,
        name: str,
        namespace: str = "default",
        repo: Optional[str] = None,
        values: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Render and apply Helm chart (bypasses Tiller/auth issues).

        Args:
            chart: Chart reference
            name: Release name for template
            namespace: Target namespace
            repo: Repository URL
            values: Set values on command line
            context: Kubernetes context to use (optional, uses current context if not specified)
        """
        if non_destructive:
            return {"success": False, "error": "Operation blocked: non-destructive mode enabled"}
        try:
            cmd = ["helm"] + _get_helm_context_args(context) + ["template", name, chart, "-n", namespace]
            if repo:
                cmd.extend(["--repo", repo])
            if values:
                cmd.extend(["--set", values])
            template_result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if template_result.returncode != 0:
                return {"success": False, "error": template_result.stderr.strip()}
            apply_cmd = ["kubectl"] + _get_kubectl_context_args(context) + ["apply", "-f", "-", "-n", namespace]
            apply_result = subprocess.run(apply_cmd, input=template_result.stdout, capture_output=True, text=True, timeout=60)
            if apply_result.returncode == 0:
                return {"success": True, "context": context or "current", "output": apply_result.stdout.strip()}
            else:
                return {"success": False, "error": apply_result.stderr.strip()}
        except Exception as e:
            logger.error(f"Error applying template: {e}")
            return {"success": False, "error": str(e)}
