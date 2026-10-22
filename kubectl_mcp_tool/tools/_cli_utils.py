import subprocess
from functools import lru_cache


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


