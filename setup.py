from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kubectl-mcp-server",
    version="1.22.0",
    author="Rohit Ghumare",
    author_email="ghumare64@gmail.com",
    description="A Model Context Protocol (MCP) server for Kubernetes with 270+ tools, 8 resources, and 8 prompts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rohitg00/kubectl-mcp-server",
    packages=find_packages(),
    keywords=[
        "kubernetes",
        "mcp",
        "model-context-protocol",
        "kubectl",
        "helm",
        "ai-assistant",
        "claude",
        "cursor",
        "windsurf",
        "fastmcp",
        "devops",
        "cloud-native",
        "mcp-ui",
    ],
    install_requires=[
        "fastmcp>=3.0.0b1",  # gofastmcp.com - to revert: change to mcp>=1.8.0
        "pydantic>=2.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "starlette>=0.27.0",
        "kubernetes>=28.1.0",
        "PyYAML>=6.0.1",
        "requests>=2.31.0",
        "urllib3>=2.1.0",
        "websocket-client>=1.7.0",
        "jsonschema>=4.20.0",
        "cryptography>=42.0.2",
        "rich>=13.0.0",
        "aiohttp>=3.8.0",
        "aiohttp-sse>=2.1.0",
    ],
    extras_require={
        "ui": ["mcp-ui-server>=0.5.0"],  # Optional: MCP-UI interactive dashboards
        "all": ["mcp-ui-server>=0.5.0"],
    },
    entry_points={
        "console_scripts": [
            "kubectl-mcp=kubectl_mcp_tool.__main__:main",
            "kubectl-mcp-serve=kubectl_mcp_tool.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
    ],
    python_requires=">=3.9",
    project_urls={
        "Bug Tracker": "https://github.com/rohitg00/kubectl-mcp-server/issues",
        "Documentation": "https://github.com/rohitg00/kubectl-mcp-server#readme",
        "Source": "https://github.com/rohitg00/kubectl-mcp-server",
    },
) 