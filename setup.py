from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kubectl-mcp-tool",
    version="1.1.0",
    author="Rohit Ghumare",
    author_email="your.email@example.com",
    description="A Model Context Protocol (MCP) server for Kubernetes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rohitg00/kubectl-mcp-server",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.5.0",
        "pydantic>=2.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "kubernetes>=28.1.0",
        "PyYAML>=6.0.1",
        "requests>=2.31.0",
        "urllib3>=2.1.0",
        "websocket-client>=1.7.0",
        "jsonschema>=4.20.0",
        "cryptography>=42.0.2",
        "rich>=13.0.0",
        "aiohttp>=3.8.0",
        "aiohttp-sse>=2.1.0"
    ],
    entry_points={
        "console_scripts": [
            "kubectl-mcp=kubectl_mcp_tool.cli.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
) 