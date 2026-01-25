"""Shared utilities for kubectl-mcp-server tools."""

import subprocess
import json
from typing import Any, Dict, List

from ..k8s_config import _get_kubectl_context_args


def run_kubectl(args: List[str], context: str = "", timeout: int = 60) -> Dict[str, Any]:
    """Run kubectl command and return result."""
    cmd = ["kubectl"] + _get_kubectl_context_args(context) + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        return {"success": False, "error": result.stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_resources(kind: str, namespace: str = "", context: str = "", label_selector: str = "") -> List[Dict]:
    """Get Kubernetes resources of a specific kind."""
    args = ["get", kind, "-o", "json"]
    if namespace:
        args.extend(["-n", namespace])
    else:
        args.append("-A")
    if label_selector:
        args.extend(["-l", label_selector])

    result = run_kubectl(args, context)
    if result["success"]:
        try:
            data = json.loads(result["output"])
            return data.get("items", [])
        except json.JSONDecodeError:
            return []
    return []
