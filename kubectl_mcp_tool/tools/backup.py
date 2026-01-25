"""Backup toolset for kubectl-mcp-server (Velero backups and restores)."""

import subprocess
import json
from typing import Dict, Any, List
from datetime import datetime

try:
    from fastmcp import FastMCP
    from fastmcp.tools import ToolAnnotations
except ImportError:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

from ..crd_detector import crd_exists
from .utils import run_kubectl, get_resources


VELERO_BACKUP_CRD = "backups.velero.io"
VELERO_RESTORE_CRD = "restores.velero.io"
VELERO_SCHEDULE_CRD = "schedules.velero.io"
VELERO_BSL_CRD = "backupstoragelocations.velero.io"
VELERO_VSL_CRD = "volumesnapshotlocations.velero.io"


def _velero_cli_available() -> bool:
    """Check if velero CLI is available."""
    try:
        result = subprocess.run(["velero", "version", "--client-only"],
                                capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def _run_velero(args: List[str], context: str = "") -> Dict[str, Any]:
    """Run velero CLI command if available."""
    if not _velero_cli_available():
        return {"success": False, "error": "Velero CLI not available"}

    cmd = ["velero"] + args
    if context:
        cmd.extend(["--kubecontext", context])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        return {"success": False, "error": result.stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def backup_list(
    namespace: str = "velero",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Velero backups.

    Args:
        namespace: Velero namespace (default: velero)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter backups

    Returns:
        List of backups with their status
    """
    if not crd_exists(VELERO_BACKUP_CRD, context):
        return {
            "success": False,
            "error": "Velero is not installed (backups.velero.io CRD not found)"
        }

    backups = []
    for item in get_resources("backups.velero.io", namespace, context, label_selector):
        status = item.get("status", {})
        spec = item.get("spec", {})
        progress = status.get("progress", {})

        backups.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "phase": status.get("phase", "Unknown"),
            "started": status.get("startTimestamp", ""),
            "completed": status.get("completionTimestamp", ""),
            "expiration": status.get("expiration", ""),
            "errors": status.get("errors", 0),
            "warnings": status.get("warnings", 0),
            "items_backed_up": progress.get("itemsBackedUp", 0),
            "total_items": progress.get("totalItems", 0),
            "included_namespaces": spec.get("includedNamespaces", []),
            "excluded_namespaces": spec.get("excludedNamespaces", []),
            "storage_location": spec.get("storageLocation", ""),
            "ttl": spec.get("ttl", ""),
        })

    completed = sum(1 for b in backups if b["phase"] == "Completed")
    failed = sum(1 for b in backups if b["phase"] == "Failed")

    return {
        "context": context or "current",
        "total": len(backups),
        "completed": completed,
        "failed": failed,
        "backups": backups,
    }


def backup_get(
    name: str,
    namespace: str = "velero",
    context: str = ""
) -> Dict[str, Any]:
    """Get detailed information about a backup.

    Args:
        name: Name of the backup
        namespace: Velero namespace (default: velero)
        context: Kubernetes context to use (optional)

    Returns:
        Detailed backup information
    """
    if not crd_exists(VELERO_BACKUP_CRD, context):
        return {"success": False, "error": "Velero is not installed"}

    args = ["get", "backups.velero.io", name, "-n", namespace, "-o", "json"]
    result = run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "backup": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def backup_create(
    name: str = "",
    namespace: str = "velero",
    included_namespaces: List[str] = None,
    excluded_namespaces: List[str] = None,
    included_resources: List[str] = None,
    excluded_resources: List[str] = None,
    label_selector: str = "",
    storage_location: str = "",
    ttl: str = "720h",
    snapshot_volumes: bool = True,
    context: str = ""
) -> Dict[str, Any]:
    """Create a new Velero backup.

    Args:
        name: Backup name (auto-generated if empty)
        namespace: Velero namespace (default: velero)
        included_namespaces: Namespaces to include
        excluded_namespaces: Namespaces to exclude
        included_resources: Resources to include
        excluded_resources: Resources to exclude
        label_selector: Label selector for resources
        storage_location: Backup storage location
        ttl: Time to live (default: 720h / 30 days)
        snapshot_volumes: Whether to snapshot volumes
        context: Kubernetes context to use (optional)

    Returns:
        Backup creation result
    """
    if not crd_exists(VELERO_BACKUP_CRD, context):
        return {"success": False, "error": "Velero is not installed"}

    if not name:
        name = f"backup-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    if _velero_cli_available():
        args = ["backup", "create", name, "-n", namespace]

        if included_namespaces:
            args.extend(["--include-namespaces", ",".join(included_namespaces)])
        if excluded_namespaces:
            args.extend(["--exclude-namespaces", ",".join(excluded_namespaces)])
        if included_resources:
            args.extend(["--include-resources", ",".join(included_resources)])
        if excluded_resources:
            args.extend(["--exclude-resources", ",".join(excluded_resources)])
        if label_selector:
            args.extend(["--selector", label_selector])
        if storage_location:
            args.extend(["--storage-location", storage_location])
        if ttl:
            args.extend(["--ttl", ttl])
        if not snapshot_volumes:
            args.append("--snapshot-volumes=false")

        result = _run_velero(args, context)
        if result["success"]:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Backup '{name}' created",
                "backup_name": name,
                "output": result["output"],
            }
        return result

    backup_spec = {
        "apiVersion": "velero.io/v1",
        "kind": "Backup",
        "metadata": {
            "name": name,
            "namespace": namespace,
        },
        "spec": {
            "ttl": ttl,
            "snapshotVolumes": snapshot_volumes,
        }
    }

    if included_namespaces:
        backup_spec["spec"]["includedNamespaces"] = included_namespaces
    if excluded_namespaces:
        backup_spec["spec"]["excludedNamespaces"] = excluded_namespaces
    if included_resources:
        backup_spec["spec"]["includedResources"] = included_resources
    if excluded_resources:
        backup_spec["spec"]["excludedResources"] = excluded_resources
    if label_selector:
        # Validate and sanitize label_selector
        parsed_labels = {}
        for segment in label_selector.split(","):
            segment = segment.strip()
            if not segment:
                continue
            if segment.count("=") != 1:
                return {"success": False, "error": f"Invalid label selector segment: '{segment}'. Expected format: key=value"}
            key, value = segment.split("=")
            key, value = key.strip(), value.strip()
            if not key:
                return {"success": False, "error": f"Invalid label selector: empty key in '{segment}'"}
            parsed_labels[key] = value
        if parsed_labels:
            backup_spec["spec"]["labelSelector"] = {"matchLabels": parsed_labels}
    if storage_location:
        backup_spec["spec"]["storageLocation"] = storage_location

    args = ["apply", "-f", "-"]
    cmd = ["kubectl"] + _get_kubectl_context_args(context) + args

    try:
        result = subprocess.run(
            cmd,
            input=json.dumps(backup_spec),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Backup '{name}' created",
                "backup_name": name,
            }
        return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}


def backup_delete(
    name: str,
    namespace: str = "velero",
    context: str = ""
) -> Dict[str, Any]:
    """Delete a Velero backup.

    Args:
        name: Name of the backup to delete
        namespace: Velero namespace (default: velero)
        context: Kubernetes context to use (optional)

    Returns:
        Deletion result
    """
    if not crd_exists(VELERO_BACKUP_CRD, context):
        return {"success": False, "error": "Velero is not installed"}

    if _velero_cli_available():
        result = _run_velero(["backup", "delete", name, "-n", namespace, "--confirm"], context)
        if result["success"]:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Backup '{name}' deletion requested",
            }
        return result

    args = ["delete", "backups.velero.io", name, "-n", namespace]
    result = run_kubectl(args, context)

    if result["success"]:
        return {
            "success": True,
            "context": context or "current",
            "message": f"Backup '{name}' deleted",
        }

    return {"success": False, "error": result.get("error", "Failed to delete backup")}


def restore_list(
    namespace: str = "velero",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Velero restores.

    Args:
        namespace: Velero namespace (default: velero)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter restores

    Returns:
        List of restores with their status
    """
    if not crd_exists(VELERO_RESTORE_CRD, context):
        return {
            "success": False,
            "error": "Velero is not installed (restores.velero.io CRD not found)"
        }

    restores = []
    for item in get_resources("restores.velero.io", namespace, context, label_selector):
        status = item.get("status", {})
        spec = item.get("spec", {})
        progress = status.get("progress", {})

        restores.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "phase": status.get("phase", "Unknown"),
            "backup_name": spec.get("backupName", ""),
            "started": status.get("startTimestamp", ""),
            "completed": status.get("completionTimestamp", ""),
            "errors": status.get("errors", 0),
            "warnings": status.get("warnings", 0),
            "items_restored": progress.get("itemsRestored", 0),
            "total_items": progress.get("totalItems", 0),
            "included_namespaces": spec.get("includedNamespaces", []),
            "excluded_namespaces": spec.get("excludedNamespaces", []),
        })

    completed = sum(1 for r in restores if r["phase"] == "Completed")
    failed = sum(1 for r in restores if r["phase"] == "Failed")

    return {
        "context": context or "current",
        "total": len(restores),
        "completed": completed,
        "failed": failed,
        "restores": restores,
    }


def restore_create(
    backup_name: str,
    name: str = "",
    namespace: str = "velero",
    included_namespaces: List[str] = None,
    excluded_namespaces: List[str] = None,
    included_resources: List[str] = None,
    excluded_resources: List[str] = None,
    namespace_mappings: Dict[str, str] = None,
    restore_pvs: bool = True,
    context: str = ""
) -> Dict[str, Any]:
    """Create a restore from a backup.

    Args:
        backup_name: Name of the backup to restore from
        name: Restore name (auto-generated if empty)
        namespace: Velero namespace (default: velero)
        included_namespaces: Namespaces to restore
        excluded_namespaces: Namespaces to exclude
        included_resources: Resources to restore
        excluded_resources: Resources to exclude
        namespace_mappings: Map source namespaces to target namespaces
        restore_pvs: Whether to restore persistent volumes
        context: Kubernetes context to use (optional)

    Returns:
        Restore creation result
    """
    if not crd_exists(VELERO_RESTORE_CRD, context):
        return {"success": False, "error": "Velero is not installed"}

    if not name:
        name = f"restore-{backup_name}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    if _velero_cli_available():
        args = ["restore", "create", name, "--from-backup", backup_name, "-n", namespace]

        if included_namespaces:
            args.extend(["--include-namespaces", ",".join(included_namespaces)])
        if excluded_namespaces:
            args.extend(["--exclude-namespaces", ",".join(excluded_namespaces)])
        if included_resources:
            args.extend(["--include-resources", ",".join(included_resources)])
        if excluded_resources:
            args.extend(["--exclude-resources", ",".join(excluded_resources)])
        if namespace_mappings:
            for src, dst in namespace_mappings.items():
                args.extend(["--namespace-mappings", f"{src}:{dst}"])
        if not restore_pvs:
            args.append("--restore-volumes=false")

        result = _run_velero(args, context)
        if result["success"]:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Restore '{name}' created from backup '{backup_name}'",
                "restore_name": name,
                "output": result["output"],
            }
        return result

    restore_spec = {
        "apiVersion": "velero.io/v1",
        "kind": "Restore",
        "metadata": {
            "name": name,
            "namespace": namespace,
        },
        "spec": {
            "backupName": backup_name,
            "restorePVs": restore_pvs,
        }
    }

    if included_namespaces:
        restore_spec["spec"]["includedNamespaces"] = included_namespaces
    if excluded_namespaces:
        restore_spec["spec"]["excludedNamespaces"] = excluded_namespaces
    if included_resources:
        restore_spec["spec"]["includedResources"] = included_resources
    if excluded_resources:
        restore_spec["spec"]["excludedResources"] = excluded_resources
    if namespace_mappings:
        restore_spec["spec"]["namespaceMapping"] = namespace_mappings

    args = ["apply", "-f", "-"]
    cmd = ["kubectl"] + _get_kubectl_context_args(context) + args

    try:
        result = subprocess.run(
            cmd,
            input=json.dumps(restore_spec),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Restore '{name}' created from backup '{backup_name}'",
                "restore_name": name,
            }
        return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}


def restore_get(
    name: str,
    namespace: str = "velero",
    context: str = ""
) -> Dict[str, Any]:
    """Get detailed information about a restore.

    Args:
        name: Name of the restore
        namespace: Velero namespace (default: velero)
        context: Kubernetes context to use (optional)

    Returns:
        Detailed restore information
    """
    if not crd_exists(VELERO_RESTORE_CRD, context):
        return {"success": False, "error": "Velero is not installed"}

    args = ["get", "restores.velero.io", name, "-n", namespace, "-o", "json"]
    result = run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "restore": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def backup_locations_list(
    namespace: str = "velero",
    context: str = ""
) -> Dict[str, Any]:
    """List Velero backup storage locations.

    Args:
        namespace: Velero namespace (default: velero)
        context: Kubernetes context to use (optional)

    Returns:
        List of backup storage locations
    """
    if not crd_exists(VELERO_BSL_CRD, context):
        return {
            "success": False,
            "error": "Velero is not installed"
        }

    locations = []
    for item in get_resources("backupstoragelocations.velero.io", namespace, context):
        status = item.get("status", {})
        spec = item.get("spec", {})

        locations.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "phase": status.get("phase", "Unknown"),
            "last_sync": status.get("lastSyncedTime", ""),
            "provider": spec.get("provider", ""),
            "bucket": spec.get("objectStorage", {}).get("bucket", ""),
            "prefix": spec.get("objectStorage", {}).get("prefix", ""),
            "default": spec.get("default", False),
            "access_mode": status.get("accessMode", ""),
        })

    return {
        "context": context or "current",
        "total": len(locations),
        "locations": locations,
    }


def backup_schedules_list(
    namespace: str = "velero",
    context: str = ""
) -> Dict[str, Any]:
    """List Velero backup schedules.

    Args:
        namespace: Velero namespace (default: velero)
        context: Kubernetes context to use (optional)

    Returns:
        List of backup schedules
    """
    if not crd_exists(VELERO_SCHEDULE_CRD, context):
        return {
            "success": False,
            "error": "Velero is not installed"
        }

    schedules = []
    for item in get_resources("schedules.velero.io", namespace, context):
        status = item.get("status", {})
        spec = item.get("spec", {})
        template = spec.get("template", {})

        schedules.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "phase": status.get("phase", "Unknown"),
            "schedule": spec.get("schedule", ""),
            "last_backup": status.get("lastBackup", ""),
            "paused": spec.get("paused", False),
            "included_namespaces": template.get("includedNamespaces", []),
            "excluded_namespaces": template.get("excludedNamespaces", []),
            "ttl": template.get("ttl", ""),
            "storage_location": template.get("storageLocation", ""),
        })

    return {
        "context": context or "current",
        "total": len(schedules),
        "schedules": schedules,
    }


def backup_schedule_create(
    name: str,
    schedule: str,
    namespace: str = "velero",
    included_namespaces: List[str] = None,
    excluded_namespaces: List[str] = None,
    ttl: str = "720h",
    storage_location: str = "",
    context: str = ""
) -> Dict[str, Any]:
    """Create a backup schedule.

    Args:
        name: Schedule name
        schedule: Cron schedule (e.g., "0 1 * * *" for daily at 1am)
        namespace: Velero namespace (default: velero)
        included_namespaces: Namespaces to include
        excluded_namespaces: Namespaces to exclude
        ttl: Backup TTL (default: 720h / 30 days)
        storage_location: Backup storage location
        context: Kubernetes context to use (optional)

    Returns:
        Schedule creation result
    """
    if not crd_exists(VELERO_SCHEDULE_CRD, context):
        return {"success": False, "error": "Velero is not installed"}

    if _velero_cli_available():
        args = ["schedule", "create", name, "--schedule", schedule, "-n", namespace]

        if included_namespaces:
            args.extend(["--include-namespaces", ",".join(included_namespaces)])
        if excluded_namespaces:
            args.extend(["--exclude-namespaces", ",".join(excluded_namespaces)])
        if ttl:
            args.extend(["--ttl", ttl])
        if storage_location:
            args.extend(["--storage-location", storage_location])

        result = _run_velero(args, context)
        if result["success"]:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Schedule '{name}' created",
                "schedule_name": name,
            }
        return result

    schedule_spec = {
        "apiVersion": "velero.io/v1",
        "kind": "Schedule",
        "metadata": {
            "name": name,
            "namespace": namespace,
        },
        "spec": {
            "schedule": schedule,
            "template": {
                "ttl": ttl,
            }
        }
    }

    if included_namespaces:
        schedule_spec["spec"]["template"]["includedNamespaces"] = included_namespaces
    if excluded_namespaces:
        schedule_spec["spec"]["template"]["excludedNamespaces"] = excluded_namespaces
    if storage_location:
        schedule_spec["spec"]["template"]["storageLocation"] = storage_location

    args = ["apply", "-f", "-"]
    cmd = ["kubectl"] + _get_kubectl_context_args(context) + args

    try:
        result = subprocess.run(
            cmd,
            input=json.dumps(schedule_spec),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Schedule '{name}' created",
                "schedule_name": name,
            }
        return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}


def backup_detect(context: str = "") -> Dict[str, Any]:
    """Detect if Velero is installed and its components.

    Args:
        context: Kubernetes context to use (optional)

    Returns:
        Detection results for Velero
    """
    return {
        "context": context or "current",
        "installed": crd_exists(VELERO_BACKUP_CRD, context),
        "cli_available": _velero_cli_available(),
        "crds": {
            "backups": crd_exists(VELERO_BACKUP_CRD, context),
            "restores": crd_exists(VELERO_RESTORE_CRD, context),
            "schedules": crd_exists(VELERO_SCHEDULE_CRD, context),
            "backup_storage_locations": crd_exists(VELERO_BSL_CRD, context),
            "volume_snapshot_locations": crd_exists(VELERO_VSL_CRD, context),
        },
    }


def register_backup_tools(mcp: FastMCP, non_destructive: bool = False):
    """Register backup tools with the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def backup_list_tool(
        namespace: str = "velero",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Velero backups."""
        return json.dumps(backup_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def backup_get_tool(
        name: str,
        namespace: str = "velero",
        context: str = ""
    ) -> str:
        """Get detailed information about a backup."""
        return json.dumps(backup_get(name, namespace, context), indent=2)

    @mcp.tool()
    def backup_create_tool(
        name: str = "",
        namespace: str = "velero",
        included_namespaces: str = "",
        excluded_namespaces: str = "",
        ttl: str = "720h",
        snapshot_volumes: bool = True,
        context: str = ""
    ) -> str:
        """Create a new Velero backup."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        inc_ns = [n.strip() for n in included_namespaces.split(",") if n.strip()] if included_namespaces else None
        exc_ns = [n.strip() for n in excluded_namespaces.split(",") if n.strip()] if excluded_namespaces else None
        return json.dumps(backup_create(name, namespace, inc_ns, exc_ns, None, None, "", "", ttl, snapshot_volumes, context), indent=2)

    @mcp.tool()
    def backup_delete_tool(
        name: str,
        namespace: str = "velero",
        context: str = ""
    ) -> str:
        """Delete a Velero backup."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(backup_delete(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def restore_list_tool(
        namespace: str = "velero",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Velero restores."""
        return json.dumps(restore_list(namespace, context, label_selector), indent=2)

    @mcp.tool()
    def restore_create_tool(
        backup_name: str,
        name: str = "",
        namespace: str = "velero",
        included_namespaces: str = "",
        excluded_namespaces: str = "",
        restore_pvs: bool = True,
        context: str = ""
    ) -> str:
        """Create a restore from a backup."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        inc_ns = [n.strip() for n in included_namespaces.split(",") if n.strip()] if included_namespaces else None
        exc_ns = [n.strip() for n in excluded_namespaces.split(",") if n.strip()] if excluded_namespaces else None
        return json.dumps(restore_create(backup_name, name, namespace, inc_ns, exc_ns, None, None, None, restore_pvs, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def restore_get_tool(
        name: str,
        namespace: str = "velero",
        context: str = ""
    ) -> str:
        """Get detailed information about a restore."""
        return json.dumps(restore_get(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def backup_locations_list_tool(
        namespace: str = "velero",
        context: str = ""
    ) -> str:
        """List Velero backup storage locations."""
        return json.dumps(backup_locations_list(namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def backup_schedules_list_tool(
        namespace: str = "velero",
        context: str = ""
    ) -> str:
        """List Velero backup schedules."""
        return json.dumps(backup_schedules_list(namespace, context), indent=2)

    @mcp.tool()
    def backup_schedule_create_tool(
        name: str,
        schedule: str,
        namespace: str = "velero",
        included_namespaces: str = "",
        excluded_namespaces: str = "",
        ttl: str = "720h",
        context: str = ""
    ) -> str:
        """Create a backup schedule."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        inc_ns = [n.strip() for n in included_namespaces.split(",") if n.strip()] if included_namespaces else None
        exc_ns = [n.strip() for n in excluded_namespaces.split(",") if n.strip()] if excluded_namespaces else None
        return json.dumps(backup_schedule_create(name, schedule, namespace, inc_ns, exc_ns, ttl, "", context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def backup_detect_tool(context: str = "") -> str:
        """Detect if Velero is installed and its components."""
        return json.dumps(backup_detect(context), indent=2)
