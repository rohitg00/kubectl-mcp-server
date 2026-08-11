"""Utilities for handling kubeconfig file path lists."""

import os
from typing import List


def split_kubeconfig_paths(path_list: str) -> List[str]:
    """Split and expand an OS-specific kubeconfig path list."""
    return [
        os.path.expanduser(path)
        for path in path_list.split(os.pathsep)
        if path
    ]


def normalize_kubeconfig_path(path_list: str) -> str:
    """Normalize every entry while preserving kubeconfig merge semantics."""
    return os.pathsep.join(split_kubeconfig_paths(path_list))


def kubeconfig_path_exists(path_list: str) -> bool:
    """Return whether at least one kubeconfig file in the path list exists."""
    return any(os.path.isfile(path) for path in split_kubeconfig_paths(path_list))
