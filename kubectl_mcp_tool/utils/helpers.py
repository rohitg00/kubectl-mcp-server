import json
import logging
import os
import re
import subprocess
import shutil
import sys
from typing import Any, List

import yaml

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


REDACTED = "[REDACTED]"
_LAST_APPLIED = "kubectl.kubernetes.io/last-applied-configuration"
_JWT = re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]+")
_BEARER = re.compile(r"(Bearer\s+)[A-Za-z0-9._~+/=-]{16,}")


def secret_masking_enabled() -> bool:
    return os.environ.get("MCP_MASK_SECRETS", "true").lower() not in ("0", "false", "no")


_SECRET_KIND_LINE = re.compile(r"^\s*kind:\s*[\"']?secret[\"']?\s*$", re.IGNORECASE | re.MULTILINE)
_SECRET_FIELD = re.compile(r"^(\s*[\"']?(data|stringData|kubectl\.kubernetes\.io/last-applied-configuration)[\"']?:)(.*)$")


def _may_hold_secret(text: str) -> bool:
    return "secret" in text.lower() and ("\n" in text or text.lstrip().startswith(("{", "[")))


def _kind(obj: dict) -> str:
    return str(obj.get("kind", "")).lower()


def redact_secrets(obj: Any) -> Any:
    """Return a copy of obj with the values of any Kubernetes Secret redacted."""
    if isinstance(obj, str):
        return _redact_documents(obj) if _may_hold_secret(obj) else obj
    if isinstance(obj, list):
        return [redact_secrets(item) for item in obj]
    if not isinstance(obj, dict):
        return obj
    if _kind(obj) == "secretlist" and isinstance(obj.get("items"), list):
        obj = {**obj, "items": [{"kind": "Secret", **i} if isinstance(i, dict) else i for i in obj["items"]]}
    out = {k: redact_secrets(v) for k, v in obj.items()}
    if _kind(out) == "secret":
        for field in ("data", "stringData"):
            if isinstance(out.get(field), dict):
                out[field] = {k: REDACTED for k in out[field]}
        annotations = (out.get("metadata") or {}).get("annotations")
        if isinstance(annotations, dict) and _LAST_APPLIED in annotations:
            annotations[_LAST_APPLIED] = REDACTED
    return out


def _redact_parsed(text: str) -> str:
    if text.lstrip().startswith(("{", "[")):
        try:
            data = json.loads(text)
        except ValueError:
            return text
        if not isinstance(data, (dict, list)):
            return text
        redacted = redact_secrets(data)
        return text if redacted == data else json.dumps(redacted, indent=2)
    try:
        docs = list(yaml.safe_load_all(text))
    except yaml.YAMLError:
        return text
    redacted = [redact_secrets(d) if isinstance(d, (dict, list)) else d for d in docs]
    if redacted == docs:
        return text
    return yaml.safe_dump_all(redacted, default_flow_style=False, sort_keys=False)


def _redact_secret_blocks(text: str) -> str:
    """Line-based fallback for Secret manifests embedded in text that does not parse."""
    out, block_indent, drop_block = [], None, False
    for line in text.splitlines(keepends=True):
        body, indent = line.strip(), len(line) - len(line.lstrip())
        eol = "\n" if line.endswith("\n") else ""
        if block_indent is not None and body and indent <= block_indent:
            block_indent = None
        if block_indent is not None:
            if not body:
                out.append(line)
            elif ":" in body and not drop_block:
                out.append(f'{line.split(":", 1)[0]}: "{REDACTED}"{eol}')
            continue
        match = _SECRET_FIELD.match(line)
        if match:
            block_indent = indent
            drop_block = bool(match.group(3).strip()) or match.group(2).startswith("kubectl.")
            if drop_block:
                line = f'{match.group(1)} "{REDACTED}"{eol}'
        out.append(line)
    return "".join(out)


def _redact_documents(text: str) -> str:
    redacted = _redact_parsed(text)
    if redacted is text and _SECRET_KIND_LINE.search(text):
        return _redact_secret_blocks(text)
    return redacted


def mask_secrets(text: str) -> str:
    """Redact Secret values, bearer tokens and JWTs from tool output text."""
    if not text:
        return text
    if _may_hold_secret(text):
        text = _redact_documents(text)
    text = _BEARER.sub(r"\1" + REDACTED, text)
    return _JWT.sub(REDACTED, text)


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
