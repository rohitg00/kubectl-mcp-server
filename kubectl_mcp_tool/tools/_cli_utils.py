import shlex
import subprocess
from functools import lru_cache
from typing import Any, Dict, List, Optional


@lru_cache(maxsize=16)
def cli_available(binary: str) -> bool:
    """Check if a CLI binary is available (cached)."""
    try:
        result = subprocess.run(
            [binary, "version"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


@lru_cache(maxsize=16)
def get_cli_version(binary: str) -> Optional[str]:
    """Get CLI binary version string (cached)."""
    try:
        result = subprocess.run(
            [binary, "version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None


def run_cli(
    binary: str,
    args: List[str],
    timeout: int = 300,
    capture_output: bool = True
) -> Dict[str, Any]:
    """Run a CLI command and return a standardized result dict.

    Args:
        binary: CLI binary name (e.g., "kind", "vcluster", "helm")
        args: Command arguments (without the binary prefix)
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr

    Returns:
        Dict with success status and output/error
    """
    cmd = [binary] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            output = result.stdout.strip() if capture_output else ""
            return {"success": True, "output": output}
        return {
            "success": False,
            "error": result.stderr.strip() if capture_output else f"Command failed with exit code {result.returncode}"
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout} seconds"}
    except FileNotFoundError:
        return {"success": False, "error": f"{binary} CLI not available"}
    except Exception as e:
        return {"success": False, "error": str(e)}
