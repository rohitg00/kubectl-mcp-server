from setuptools import setup, find_packages

setup(
    name="kubectl-mcp-tool",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "mcp",
        "pydantic>=2.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "kubernetes>=28.1.0",
        "rich>=13.0.0",
        "aiohttp>=3.8.0",
        "aiohttp-sse>=2.1.0",
    ],
    entry_points={
        "console_scripts": [
            "kubectl-mcp=kubectl_mcp_tool.cli:main",
        ],
    },
)
