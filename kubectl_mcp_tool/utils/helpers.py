import logging
import os
import re
import subprocess
import shutil
import sys
from typing import List

_log_file = os.environ.get("MCP_LOG_FILE")
_log_level = logging.DEBUG if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true") else logging.INFO

_handlers: List[logging.Handler] = []
if _log_file:
    try:
        os.makedirs(os.path.dirname(_log_file), exist_ok=True)
        _handlers.append(logging.FileHandler(_log_file))
    except (OSError, ValueError):
        _handlers.append(logging.StreamHandler(sys.stderr))
else:
    _handlers.append(logging.StreamHandler(sys.stderr))

logging.basicConfig(
    level=_log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=_handlers
)

for handler in logging.root.handlers[:]:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
        logging.root.removeHandler(handler)

logger = logging.getLogger("mcp-server")


def get_logger(name: str = "mcp-server") -> logging.Logger:
    return logging.getLogger(name)


def mask_secrets(text: str) -> str:
    masked = re.sub(r'(data:\s*\n)(\s+\w+:\s*)([A-Za-z0-9+/=]{20,})', r'\1\2[MASKED]', text)
    masked = re.sub(r'(password|secret|token|key|credential)(["\s:=]+)([^\s"\n]+)', r'\1\2[MASKED]', masked, flags=re.IGNORECASE)
    return masked


def check_tool_availability(tool: str) -> bool:
    try:
        if shutil.which(tool) is None:
            return False
        if tool == "kubectl":
            subprocess.check_output(
                [tool, "version", "--client", "--output=json"],
                stderr=subprocess.PIPE,
                timeout=2
            )
        elif tool == "helm":
            subprocess.check_output(
                [tool, "version", "--short"],
                stderr=subprocess.PIPE,
                timeout=2
            )
        return True
    except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_kubectl_availability() -> bool:
    return check_tool_availability("kubectl")


def check_helm_availability() -> bool:
    return check_tool_availability("helm")


def check_dependencies() -> bool:
    all_available = True
    for tool in ["kubectl", "helm"]:
        if not check_tool_availability(tool):
            logger.warning(f"{tool} not found in PATH. Operations requiring {tool} will not work.")
            all_available = False
    return all_available
