"""Legacy package setup for kubectl-mcp-tool (alias for kubectl-mcp-server)."""

from setuptools import setup

setup(
    name="kubectl-mcp-tool",
    version="1.11.0",
    author="Rohit Ghumare",
    author_email="ghumare64@gmail.com",
    description="Alias package for kubectl-mcp-server (use kubectl-mcp-server instead)",
    long_description="""
# kubectl-mcp-tool

**This package is an alias for `kubectl-mcp-server`.**

Please use `kubectl-mcp-server` for new installations:

```bash
pip install kubectl-mcp-server
```

This package exists for backward compatibility and will install `kubectl-mcp-server` as a dependency.

For documentation, see: https://github.com/rohitg00/kubectl-mcp-server
""",
    long_description_content_type="text/markdown",
    url="https://github.com/rohitg00/kubectl-mcp-server",
    packages=[],
    install_requires=[
        "kubectl-mcp-server>=1.11.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    project_urls={
        "Bug Tracker": "https://github.com/rohitg00/kubectl-mcp-server/issues",
        "Documentation": "https://github.com/rohitg00/kubectl-mcp-server#readme",
        "Source": "https://github.com/rohitg00/kubectl-mcp-server",
    },
)
