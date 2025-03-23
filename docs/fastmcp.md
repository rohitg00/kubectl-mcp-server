Directory structure:
└── jlowin-fastmcp/
    ├── README.md
    ├── LICENSE
    ├── Windows_Notes.md
    ├── pyproject.toml
    ├── uv.lock
    ├── .pre-commit-config.yaml
    ├── .python-version
    ├── docs/
    │   └── assets/
    ├── examples/
    │   ├── complex_inputs.py
    │   ├── desktop.py
    │   ├── echo.py
    │   ├── memory.py
    │   ├── readme-quickstart.py
    │   ├── screenshot.py
    │   ├── simple_echo.py
    │   └── text_me.py
    ├── src/
    │   └── fastmcp/
    │       ├── __init__.py
    │       ├── exceptions.py
    │       ├── py.typed
    │       ├── server.py
    │       ├── cli/
    │       │   ├── __init__.py
    │       │   ├── claude.py
    │       │   └── cli.py
    │       ├── prompts/
    │       │   ├── __init__.py
    │       │   ├── base.py
    │       │   ├── manager.py
    │       │   └── prompt_manager.py
    │       ├── resources/
    │       │   ├── __init__.py
    │       │   ├── base.py
    │       │   ├── resource_manager.py
    │       │   ├── templates.py
    │       │   └── types.py
    │       ├── tools/
    │       │   ├── __init__.py
    │       │   ├── base.py
    │       │   └── tool_manager.py
    │       └── utilities/
    │           ├── __init__.py
    │           ├── func_metadata.py
    │           ├── logging.py
    │           └── types.py
    ├── tests/
    │   ├── __init__.py
    │   ├── test_cli.py
    │   ├── test_func_metadata.py
    │   ├── test_server.py
    │   ├── test_tool_manager.py
    │   ├── prompts/
    │   │   ├── __init__.py
    │   │   ├── test_base.py
    │   │   └── test_manager.py
    │   ├── resources/
    │   │   ├── __init__.py
    │   │   ├── test_file_resources.py
    │   │   ├── test_function_resources.py
    │   │   ├── test_resource_manager.py
    │   │   ├── test_resource_template.py
    │   │   └── test_resources.py
    │   └── servers/
    │       ├── __init__.py
    │       └── test_file_server.py
    └── .github/
        ├── ai-labeler.yml
        ├── release.yml
        └── workflows/
            ├── ai-labeler.yml
            ├── publish.yml
            ├── run-static.yml
            └── run-tests.yml


Files Content:

(Files content cropped to 300k characters, download full ingest to see more)
================================================
File: README.md
================================================
<div align="center">

### 🎉 FastMCP has been added to the official MCP SDK! 🎉

You can now find FastMCP as part of the official Model Context Protocol Python SDK:

👉 [github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)

*Please note: this repository is no longer maintained.*

---


</br></br></br>

</div>

<div align="center">

<!-- omit in toc -->
# FastMCP 🚀
<strong>The fast, Pythonic way to build MCP servers.</strong>

[![PyPI - Version](https://img.shields.io/pypi/v/fastmcp.svg)](https://pypi.org/project/fastmcp)
[![Tests](https://github.com/jlowin/fastmcp/actions/workflows/run-tests.yml/badge.svg)](https://github.com/jlowin/fastmcp/actions/workflows/run-tests.yml)
[![License](https://img.shields.io/github/license/jlowin/fastmcp.svg)](https://github.com/jlowin/fastmcp/blob/main/LICENSE)


</div>

[Model Context Protocol (MCP)](https://modelcontextprotocol.io) servers are a new, standardized way to provide context and tools to your LLMs, and FastMCP makes building MCP servers simple and intuitive. Create tools, expose resources, and define prompts with clean, Pythonic code:

```python
# demo.py

from fastmcp import FastMCP


mcp = FastMCP("Demo 🚀")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b
```

That's it! Give Claude access to the server by running:

```bash
fastmcp install demo.py
```

FastMCP handles all the complex protocol details and server management, so you can focus on building great tools. It's designed to be high-level and Pythonic - in most cases, decorating a function is all you need.


### Key features:
* **Fast**: High-level interface means less code and faster development
* **Simple**: Build MCP servers with minimal boilerplate
* **Pythonic**: Feels natural to Python developers
* **Complete***: FastMCP aims to provide a full implementation of the core MCP specification

(\*emphasis on *aims*)

🚨 🚧 🏗️ *FastMCP is under active development, as is the MCP specification itself. Core features are working but some advanced capabilities are still in progress.* 


<!-- omit in toc -->
## Table of Contents

- [Installation](#installation)
- [Quickstart](#quickstart)
- [What is MCP?](#what-is-mcp)
- [Core Concepts](#core-concepts)
  - [Server](#server)
  - [Resources](#resources)
  - [Tools](#tools)
  - [Prompts](#prompts)
  - [Images](#images)
  - [Context](#context)
- [Running Your Server](#running-your-server)
  - [Development Mode (Recommended for Building \& Testing)](#development-mode-recommended-for-building--testing)
  - [Claude Desktop Integration (For Regular Use)](#claude-desktop-integration-for-regular-use)
  - [Direct Execution (For Advanced Use Cases)](#direct-execution-for-advanced-use-cases)
  - [Server Object Names](#server-object-names)
- [Examples](#examples)
  - [Echo Server](#echo-server)
  - [SQLite Explorer](#sqlite-explorer)
- [Contributing](#contributing)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation-1)
  - [Testing](#testing)
  - [Formatting](#formatting)
  - [Opening a Pull Request](#opening-a-pull-request)

## Installation

We strongly recommend installing FastMCP with [uv](https://docs.astral.sh/uv/), as it is required for deploying servers:

```bash
uv pip install fastmcp
```

Note: on macOS, uv may need to be installed with Homebrew (`brew install uv`) in order to make it available to the Claude Desktop app.

Alternatively, to use the SDK without deploying, you may use pip:

```bash
pip install fastmcp
```

## Quickstart

Let's create a simple MCP server that exposes a calculator tool and some data:

```python
# server.py

from fastmcp import FastMCP


# Create an MCP server
mcp = FastMCP("Demo")


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"
```

You can install this server in [Claude Desktop](https://claude.ai/download) and interact with it right away by running:
```bash
fastmcp install server.py
```

Alternatively, you can test it with the MCP Inspector:
```bash
fastmcp dev server.py
```

![MCP Inspector](/docs/assets/demo-inspector.png)

## What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) lets you build servers that expose data and functionality to LLM applications in a secure, standardized way. Think of it like a web API, but specifically designed for LLM interactions. MCP servers can:

- Expose data through **Resources** (think of these sort of like GET endpoints; they are used to load information into the LLM's context)
- Provide functionality through **Tools** (sort of like POST endpoints; they are used to execute code or otherwise produce a side effect)
- Define interaction patterns through **Prompts** (reusable templates for LLM interactions)
- And more!

There is a low-level [Python SDK](https://github.com/modelcontextprotocol/python-sdk) available for implementing the protocol directly, but FastMCP aims to make that easier by providing a high-level, Pythonic interface.

## Core Concepts


### Server

The FastMCP server is your core interface to the MCP protocol. It handles connection management, protocol compliance, and message routing:

```python
from fastmcp import FastMCP

# Create a named server
mcp = FastMCP("My App")

# Specify dependencies for deployment and development
mcp = FastMCP("My App", dependencies=["pandas", "numpy"])
```

### Resources

Resources are how you expose data to LLMs. They're similar to GET endpoints in a REST API - they provide data but shouldn't perform significant computation or have side effects. Some examples:

- File contents
- Database schemas
- API responses
- System information

Resources can be static:
```python
@mcp.resource("config://app")
def get_config() -> str:
    """Static configuration data"""
    return "App configuration here"
```

Or dynamic with parameters (FastMCP automatically handles these as MCP templates):
```python
@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: str) -> str:
    """Dynamic user data"""
    return f"Profile data for user {user_id}"
```

### Tools

Tools let LLMs take actions through your server. Unlike resources, tools are expected to perform computation and have side effects. They're similar to POST endpoints in a REST API.

Simple calculation example:
```python
@mcp.tool()
def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Calculate BMI given weight in kg and height in meters"""
    return weight_kg / (height_m ** 2)
```

HTTP request example:
```python
import httpx

@mcp.tool()
async def fetch_weather(city: str) -> str:
    """Fetch current weather for a city"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.weather.com/{city}"
        )
        return response.text
```

Complex input handling example:
```python
from pydantic import BaseModel, Field
from typing import Annotated

class ShrimpTank(BaseModel):
    class Shrimp(BaseModel):
        name: Annotated[str, Field(max_length=10)]

    shrimp: list[Shrimp]

@mcp.tool()
def name_shrimp(
    tank: ShrimpTank,
    # You can use pydantic Field in function signatures for validation.
    extra_names: Annotated[list[str], Field(max_length=10)],
) -> list[str]:
    """List all shrimp names in the tank"""
    return [shrimp.name for shrimp in tank.shrimp] + extra_names
```

### Prompts

Prompts are reusable templates that help LLMs interact with your server effectively. They're like "best practices" encoded into your server. A prompt can be as simple as a string:

```python
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
```

Or a more structured sequence of messages:
```python
from fastmcp.prompts.base import UserMessage, AssistantMessage

@mcp.prompt()
def debug_error(error: str) -> list[Message]:
    return [
        UserMessage("I'm seeing this error:"),
        UserMessage(error),
        AssistantMessage("I'll help debug that. What have you tried so far?")
    ]
```


### Images

FastMCP provides an `Image` class that automatically handles image data in your server:

```python
from fastmcp import FastMCP, Image
from PIL import Image as PILImage

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    
    # FastMCP automatically handles conversion and MIME types
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def load_image(path: str) -> Image:
    """Load an image from disk"""
    # FastMCP handles reading and format detection
    return Image(path=path)
```

Images can be used as the result of both tools and resources.

### Context

The Context object gives your tools and resources access to MCP capabilities. To use it, add a parameter annotated with `fastmcp.Context`:

```python
from fastmcp import FastMCP, Context

@mcp.tool()
async def long_task(files: list[str], ctx: Context) -> str:
    """Process multiple files with progress tracking"""
    for i, file in enumerate(files):
        ctx.info(f"Processing {file}")
        await ctx.report_progress(i, len(files))
        
        # Read another resource if needed
        data = await ctx.read_resource(f"file://{file}")
        
    return "Processing complete"
```

The Context object provides:
- Progress reporting through `report_progress()`
- Logging via `debug()`, `info()`, `warning()`, and `error()`
- Resource access through `read_resource()`
- Request metadata via `request_id` and `client_id`

## Running Your Server

There are three main ways to use your FastMCP server, each suited for different stages of development:

### Development Mode (Recommended for Building & Testing)

The fastest way to test and debug your server is with the MCP Inspector:

```bash
fastmcp dev server.py
```

This launches a web interface where you can:
- Test your tools and resources interactively
- See detailed logs and error messages
- Monitor server performance
- Set environment variables for testing

During development, you can:
- Add dependencies with `--with`: 
  ```bash
  fastmcp dev server.py --with pandas --with numpy
  ```
- Mount your local code for live updates:
  ```bash
  fastmcp dev server.py --with-editable .
  ```

### Claude Desktop Integration (For Regular Use)

Once your server is ready, install it in Claude Desktop to use it with Claude:

```bash
fastmcp install server.py
```

Your server will run in an isolated environment with:
- Automatic installation of dependencies specified in your FastMCP instance:
  ```python
  mcp = FastMCP("My App", dependencies=["pandas", "numpy"])
  ```
- Custom naming via `--name`:
  ```bash
  fastmcp install server.py --name "My Analytics Server"
  ```
- Environment variable management:
  ```bash
  # Set variables individually
  fastmcp install server.py -e API_KEY=abc123 -e DB_URL=postgres://...
  
  # Or load from a .env file
  fastmcp install server.py -f .env
  ```

### Direct Execution (For Advanced Use Cases)

For advanced scenarios like custom deployments or running without Claude, you can execute your server directly:

```python
from fastmcp import FastMCP

mcp = FastMCP("My App")

if __name__ == "__main__":
    mcp.run()
```

Run it with:
```bash
# Using the FastMCP CLI
fastmcp run server.py

# Or with Python/uv directly
python server.py
uv run python server.py
```


Note: When running directly, you are responsible for ensuring all dependencies are available in your environment. Any dependencies specified on the FastMCP instance are ignored.

Choose this method when you need:
- Custom deployment configurations
- Integration with other services
- Direct control over the server lifecycle

### Server Object Names

All FastMCP commands will look for a server object called `mcp`, `app`, or `server` in your file. If you have a different object name or multiple servers in one file, use the syntax `server.py:my_server`:

```bash
# Using a standard name
fastmcp run server.py

# Using a custom name
fastmcp run server.py:my_custom_server
```

## Examples

Here are a few examples of FastMCP servers. For more, see the `examples/` directory.

### Echo Server
A simple server demonstrating resources, tools, and prompts:

```python
from fastmcp import FastMCP

mcp = FastMCP("Echo")

@mcp.resource("echo://{message}")
def echo_resource(message: str) -> str:
    """Echo a message as a resource"""
    return f"Resource echo: {message}"

@mcp.tool()
def echo_tool(message: str) -> str:
    """Echo a message as a tool"""
    return f"Tool echo: {message}"

@mcp.prompt()
def echo_prompt(message: str) -> str:
    """Create an echo prompt"""
    return f"Please process this message: {message}"
```

### SQLite Explorer
A more complex example showing database integration:

```python
from fastmcp import FastMCP
import sqlite3

mcp = FastMCP("SQLite Explorer")

@mcp.resource("schema://main")
def get_schema() -> str:
    """Provide the database schema as a resource"""
    conn = sqlite3.connect("database.db")
    schema = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return "\n".join(sql[0] for sql in schema if sql[0])

@mcp.tool()
def query_data(sql: str) -> str:
    """Execute SQL queries safely"""
    conn = sqlite3.connect("database.db")
    try:
        result = conn.execute(sql).fetchall()
        return "\n".join(str(row) for row in result)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.prompt()
def analyze_table(table: str) -> str:
    """Create a prompt template for analyzing tables"""
    return f"""Please analyze this database table:
Table: {table}
Schema: 
{get_schema()}

What insights can you provide about the structure and relationships?"""
```

## Contributing

<details>

<summary><h3>Open Developer Guide</h3></summary>

### Prerequisites

FastMCP requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

### Installation

For development, we recommend installing FastMCP with development dependencies, which includes various utilities the maintainers find useful.

```bash
git clone https://github.com/jlowin/fastmcp.git
cd fastmcp
uv sync --frozen --extra dev
```

For running tests only (e.g., in CI), you only need the testing dependencies:

```bash
uv sync --frozen --extra tests
```

### Testing

Please make sure to test any new functionality. Your tests should be simple and atomic and anticipate change rather than cement complex patterns.

Run tests from the root directory:


```bash
pytest -vv
```

### Formatting

FastMCP enforces a variety of required formats, which you can automatically enforce with pre-commit. 

Install the pre-commit hooks:

```bash
pre-commit install
```

The hooks will now run on every commit (as well as on every PR). To run them manually:

```bash
pre-commit run --all-files
```

### Opening a Pull Request

Fork the repository and create a new branch:

```bash
git checkout -b my-branch
```

Make your changes and commit them:


```bash
git add . && git commit -m "My changes"
```

Push your changes to your fork:


```bash
git push origin my-branch
```

Feel free to reach out in a GitHub issue or discussion if you have any questions!

</details>



================================================
File: LICENSE
================================================
MIT License

Copyright (c) 2024 Jeremiah Lowin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.



================================================
File: Windows_Notes.md
================================================
# Getting your development environment set up properly
To get your environment up and running properly, you'll need a slightly different set of commands that are windows specific:
```bash
uv venv
.venv\Scripts\activate
uv pip install -e ".[dev]"
```

This will install the package in editable mode, and install the development dependencies.


# Fixing `AttributeError: module 'collections' has no attribute 'Callable'`
- open `.venv\Lib\site-packages\pyreadline\py3k_compat.py`
- change `return isinstance(x, collections.Callable)` to 
``` 
from collections.abc import Callable
return isinstance(x, Callable)
```

# Helpful notes
For developing FastMCP
## Install local development version of FastMCP into a local FastMCP project server
- ensure
- change directories to your FastMCP Server location so you can install it in your .venv
- run `.venv\Scripts\activate` to activate your virtual environment
- Then run a series of commands to uninstall the old version and install the new
```bash
# First uninstall
uv pip uninstall fastmcp

# Clean any build artifacts in your fastmcp directory
cd C:\path\to\fastmcp
del /s /q *.egg-info

# Then reinstall in your weather project
cd C:\path\to\new\fastmcp_server
uv pip install --no-cache-dir -e C:\Users\justj\PycharmProjects\fastmcp

# Check that it installed properly and has the correct git hash
pip show fastmcp
```

## Running the FastMCP server with Inspector
MCP comes with a node.js application called Inspector that can be used to inspect the FastMCP server. To run the inspector, you'll need to install node.js and npm. Then you can run the following commands:
```bash
fastmcp dev server.py
```
This will launch a web app on http://localhost:5173/ that you can use to inspect the FastMCP server.

## If you start development before creating a fork - your get out of jail free card
- Add your fork as a new remote to your local repository `git remote add fork git@github.com:YOUR-USERNAME/REPOSITORY-NAME.git`
  - This will add your repo, short named 'fork', as a remote to your local repository
- Verify that it was added correctly by running `git remote -v`
- Commit your changes
- Push your changes to your fork `git push fork <branch>`
- Create your pull request on GitHub 





================================================
File: pyproject.toml
================================================
[project]
name = "fastmcp"
dynamic = ["version"]
description = "A more ergonomic interface for MCP servers"
authors = [{ name = "Jeremiah Lowin" }]
dependencies = [
    "httpx>=0.26.0",
    "mcp>=1.0.0,<2.0.0",
    "pydantic-settings>=2.6.1",
    "pydantic>=2.5.3,<3.0.0",
    "typer>=0.9.0",
    "python-dotenv>=1.0.1",
]
requires-python = ">=3.10"
readme = "README.md"
license = { text = "MIT" }

[project.scripts]
fastmcp = "fastmcp.cli:app"

[build-system]
requires = ["hatchling>=1.21.0", "hatch-vcs>=0.4.0"]
build-backend = "hatchling.build"

[project.optional-dependencies]
tests = [
    "pre-commit",
    "pyright>=1.1.389",
    "pytest>=8.3.3",
    "pytest-asyncio>=0.23.5",
    "pytest-flakefinder",
    "pytest-xdist>=3.6.1",
    "ruff",
]
dev = ["fastmcp[tests]", "copychat>=0.5.2", "ipython>=8.12.3", "pdbpp>=0.10.3"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"

[tool.hatch.version]
source = "vcs"

[tool.pyright]
include = ["src", "tests"]
exclude = ["**/node_modules", "**/__pycache__", ".venv", ".git", "dist"]
pythonVersion = "3.10"
pythonPlatform = "Darwin"
typeCheckingMode = "basic"
reportMissingImports = true
reportMissingTypeStubs = false
useLibraryCodeForTypes = true
venvPath = "."
venv = ".venv"



================================================
File: uv.lock
================================================
version = 1
requires-python = ">=3.10"

[[package]]
name = "annotated-types"
version = "0.7.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/ee/67/531ea369ba64dcff5ec9c3402f9f51bf748cec26dde048a2f973a4eea7f5/annotated_types-0.7.0.tar.gz", hash = "sha256:aff07c09a53a08bc8cfccb9c85b05f1aa9a2a6f23728d790723543408344ce89", size = 16081 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/78/b6/6307fbef88d9b5ee7421e68d78a9f162e0da4900bc5f5793f6d3d0e34fb8/annotated_types-0.7.0-py3-none-any.whl", hash = "sha256:1f02e8b43a8fbbc3f3e0d4f0f4bfc8131bcb4eebe8849b8e5c773f3a1c582a53", size = 13643 },
]

[[package]]
name = "anyio"
version = "4.6.2.post1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "exceptiongroup", marker = "python_full_version < '3.11'" },
    { name = "idna" },
    { name = "sniffio" },
    { name = "typing-extensions", marker = "python_full_version < '3.11'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/9f/09/45b9b7a6d4e45c6bcb5bf61d19e3ab87df68e0601fa8c5293de3542546cc/anyio-4.6.2.post1.tar.gz", hash = "sha256:4c8bc31ccdb51c7f7bd251f51c609e038d63e34219b44aa86e47576389880b4c", size = 173422 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/e4/f5/f2b75d2fc6f1a260f340f0e7c6a060f4dd2961cc16884ed851b0d18da06a/anyio-4.6.2.post1-py3-none-any.whl", hash = "sha256:6d170c36fba3bdd840c73d3868c1e777e33676a69c3a72cf0a0d5d6d8009b61d", size = 90377 },
]

[[package]]
name = "asttokens"
version = "3.0.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/4a/e7/82da0a03e7ba5141f05cce0d302e6eed121ae055e0456ca228bf693984bc/asttokens-3.0.0.tar.gz", hash = "sha256:0dcd8baa8d62b0c1d118b399b2ddba3c4aff271d0d7a9e0d4c1681c79035bbc7", size = 61978 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/25/8a/c46dcc25341b5bce5472c718902eb3d38600a903b14fa6aeecef3f21a46f/asttokens-3.0.0-py3-none-any.whl", hash = "sha256:e3078351a059199dd5138cb1c706e6430c05eff2ff136af5eb4790f9d28932e2", size = 26918 },
]

[[package]]
name = "attrs"
version = "24.2.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/fc/0f/aafca9af9315aee06a89ffde799a10a582fe8de76c563ee80bbcdc08b3fb/attrs-24.2.0.tar.gz", hash = "sha256:5cfb1b9148b5b086569baec03f20d7b6bf3bcacc9a42bebf87ffaaca362f6346", size = 792678 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/6a/21/5b6702a7f963e95456c0de2d495f67bf5fd62840ac655dc451586d23d39a/attrs-24.2.0-py3-none-any.whl", hash = "sha256:81921eb96de3191c8258c199618104dd27ac608d9366f5e35d011eae1867ede2", size = 63001 },
]

[[package]]
name = "certifi"
version = "2024.8.30"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/b0/ee/9b19140fe824b367c04c5e1b369942dd754c4c5462d5674002f75c4dedc1/certifi-2024.8.30.tar.gz", hash = "sha256:bec941d2aa8195e248a60b31ff9f0558284cf01a52591ceda73ea9afffd69fd9", size = 168507 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/12/90/3c9ff0512038035f59d279fddeb79f5f1eccd8859f06d6163c58798b9487/certifi-2024.8.30-py3-none-any.whl", hash = "sha256:922820b53db7a7257ffbda3f597266d435245903d80737e34f8a45ff3e3230d8", size = 167321 },
]

[[package]]
name = "cfgv"
version = "3.4.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/11/74/539e56497d9bd1d484fd863dd69cbbfa653cd2aa27abfe35653494d85e94/cfgv-3.4.0.tar.gz", hash = "sha256:e52591d4c5f5dead8e0f673fb16db7949d2cfb3f7da4582893288f0ded8fe560", size = 7114 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/c5/55/51844dd50c4fc7a33b653bfaba4c2456f06955289ca770a5dbd5fd267374/cfgv-3.4.0-py2.py3-none-any.whl", hash = "sha256:b7265b1f29fd3316bfcd2b330d63d024f2bfd8bcb8b0272f8e19a504856c48f9", size = 7249 },
]

[[package]]
name = "charset-normalizer"
version = "3.4.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/f2/4f/e1808dc01273379acc506d18f1504eb2d299bd4131743b9fc54d7be4df1e/charset_normalizer-3.4.0.tar.gz", hash = "sha256:223217c3d4f82c3ac5e29032b3f1c2eb0fb591b72161f86d93f5719079dae93e", size = 106620 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/69/8b/825cc84cf13a28bfbcba7c416ec22bf85a9584971be15b21dd8300c65b7f/charset_normalizer-3.4.0-cp310-cp310-macosx_10_9_universal2.whl", hash = "sha256:4f9fc98dad6c2eaa32fc3af1417d95b5e3d08aff968df0cd320066def971f9a6", size = 196363 },
    { url = "https://files.pythonhosted.org/packages/23/81/d7eef6a99e42c77f444fdd7bc894b0ceca6c3a95c51239e74a722039521c/charset_normalizer-3.4.0-cp310-cp310-macosx_10_9_x86_64.whl", hash = "sha256:0de7b687289d3c1b3e8660d0741874abe7888100efe14bd0f9fd7141bcbda92b", size = 125639 },
    { url = "https://files.pythonhosted.org/packages/21/67/b4564d81f48042f520c948abac7079356e94b30cb8ffb22e747532cf469d/charset_normalizer-3.4.0-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:5ed2e36c3e9b4f21dd9422f6893dec0abf2cca553af509b10cd630f878d3eb99", size = 120451 },
    { url = "https://files.pythonhosted.org/packages/c2/72/12a7f0943dd71fb5b4e7b55c41327ac0a1663046a868ee4d0d8e9c369b85/charset_normalizer-3.4.0-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:40d3ff7fc90b98c637bda91c89d51264a3dcf210cade3a2c6f838c7268d7a4ca", size = 140041 },
    { url = "https://files.pythonhosted.org/packages/67/56/fa28c2c3e31217c4c52158537a2cf5d98a6c1e89d31faf476c89391cd16b/charset_normalizer-3.4.0-cp310-cp310-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:1110e22af8ca26b90bd6364fe4c763329b0ebf1ee213ba32b68c73de5752323d", size = 150333 },
    { url = "https://files.pythonhosted.org/packages/f9/d2/466a9be1f32d89eb1554cf84073a5ed9262047acee1ab39cbaefc19635d2/charset_normalizer-3.4.0-cp310-cp310-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:86f4e8cca779080f66ff4f191a685ced73d2f72d50216f7112185dc02b90b9b7", size = 142921 },
    { url = "https://files.pythonhosted.org/packages/f8/01/344ec40cf5d85c1da3c1f57566c59e0c9b56bcc5566c08804a95a6cc8257/charset_normalizer-3.4.0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:7f683ddc7eedd742e2889d2bfb96d69573fde1d92fcb811979cdb7165bb9c7d3", size = 144785 },
    { url = "https://files.pythonhosted.org/packages/73/8b/2102692cb6d7e9f03b9a33a710e0164cadfce312872e3efc7cfe22ed26b4/charset_normalizer-3.4.0-cp310-cp310-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:27623ba66c183eca01bf9ff833875b459cad267aeeb044477fedac35e19ba907", size = 146631 },
    { url = "https://files.pythonhosted.org/packages/d8/96/cc2c1b5d994119ce9f088a9a0c3ebd489d360a2eb058e2c8049f27092847/charset_normalizer-3.4.0-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:f606a1881d2663630ea5b8ce2efe2111740df4b687bd78b34a8131baa007f79b", size = 140867 },
    { url = "https://files.pythonhosted.org/packages/c9/27/cde291783715b8ec30a61c810d0120411844bc4c23b50189b81188b273db/charset_normalizer-3.4.0-cp310-cp310-musllinux_1_2_i686.whl", hash = "sha256:0b309d1747110feb25d7ed6b01afdec269c647d382c857ef4663bbe6ad95a912", size = 149273 },
    { url = "https://files.pythonhosted.org/packages/3a/a4/8633b0fc1a2d1834d5393dafecce4a1cc56727bfd82b4dc18fc92f0d3cc3/charset_normalizer-3.4.0-cp310-cp310-musllinux_1_2_ppc64le.whl", hash = "sha256:136815f06a3ae311fae551c3df1f998a1ebd01ddd424aa5603a4336997629e95", size = 152437 },
    { url = "https://files.pythonhosted.org/packages/64/ea/69af161062166b5975ccbb0961fd2384853190c70786f288684490913bf5/charset_normalizer-3.4.0-cp310-cp310-musllinux_1_2_s390x.whl", hash = "sha256:14215b71a762336254351b00ec720a8e85cada43b987da5a042e4ce3e82bd68e", size = 150087 },
    { url = "https://files.pythonhosted.org/packages/3b/fd/e60a9d9fd967f4ad5a92810138192f825d77b4fa2a557990fd575a47695b/charset_normalizer-3.4.0-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:79983512b108e4a164b9c8d34de3992f76d48cadc9554c9e60b43f308988aabe", size = 145142 },
    { url = "https://files.pythonhosted.org/packages/6d/02/8cb0988a1e49ac9ce2eed1e07b77ff118f2923e9ebd0ede41ba85f2dcb04/charset_normalizer-3.4.0-cp310-cp310-win32.whl", hash = "sha256:c94057af19bc953643a33581844649a7fdab902624d2eb739738a30e2b3e60fc", size = 94701 },
    { url = "https://files.pythonhosted.org/packages/d6/20/f1d4670a8a723c46be695dff449d86d6092916f9e99c53051954ee33a1bc/charset_normalizer-3.4.0-cp310-cp310-win_amd64.whl", hash = "sha256:55f56e2ebd4e3bc50442fbc0888c9d8c94e4e06a933804e2af3e89e2f9c1c749", size = 102191 },
    { url = "https://files.pythonhosted.org/packages/9c/61/73589dcc7a719582bf56aae309b6103d2762b526bffe189d635a7fcfd998/charset_normalizer-3.4.0-cp311-cp311-macosx_10_9_universal2.whl", hash = "sha256:0d99dd8ff461990f12d6e42c7347fd9ab2532fb70e9621ba520f9e8637161d7c", size = 193339 },
    { url = "https://files.pythonhosted.org/packages/77/d5/8c982d58144de49f59571f940e329ad6e8615e1e82ef84584c5eeb5e1d72/charset_normalizer-3.4.0-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:c57516e58fd17d03ebe67e181a4e4e2ccab1168f8c2976c6a334d4f819fe5944", size = 124366 },
    { url = "https://files.pythonhosted.org/packages/bf/19/411a64f01ee971bed3231111b69eb56f9331a769072de479eae7de52296d/charset_normalizer-3.4.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:6dba5d19c4dfab08e58d5b36304b3f92f3bd5d42c1a3fa37b5ba5cdf6dfcbcee", size = 118874 },
    { url = "https://files.pythonhosted.org/packages/4c/92/97509850f0d00e9f14a46bc751daabd0ad7765cff29cdfb66c68b6dad57f/charset_normalizer-3.4.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:bf4475b82be41b07cc5e5ff94810e6a01f276e37c2d55571e3fe175e467a1a1c", size = 138243 },
    { url = "https://files.pythonhosted.org/packages/e2/29/d227805bff72ed6d6cb1ce08eec707f7cfbd9868044893617eb331f16295/charset_normalizer-3.4.0-cp311-cp311-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:ce031db0408e487fd2775d745ce30a7cd2923667cf3b69d48d219f1d8f5ddeb6", size = 148676 },
    { url = "https://files.pythonhosted.org/packages/13/bc/87c2c9f2c144bedfa62f894c3007cd4530ba4b5351acb10dc786428a50f0/charset_normalizer-3.4.0-cp311-cp311-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:8ff4e7cdfdb1ab5698e675ca622e72d58a6fa2a8aa58195de0c0061288e6e3ea", size = 141289 },
    { url = "https://files.pythonhosted.org/packages/eb/5b/6f10bad0f6461fa272bfbbdf5d0023b5fb9bc6217c92bf068fa5a99820f5/charset_normalizer-3.4.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:3710a9751938947e6327ea9f3ea6332a09bf0ba0c09cae9cb1f250bd1f1549bc", size = 142585 },
    { url = "https://files.pythonhosted.org/packages/3b/a0/a68980ab8a1f45a36d9745d35049c1af57d27255eff8c907e3add84cf68f/charset_normalizer-3.4.0-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:82357d85de703176b5587dbe6ade8ff67f9f69a41c0733cf2425378b49954de5", size = 144408 },
    { url = "https://files.pythonhosted.org/packages/d7/a1/493919799446464ed0299c8eef3c3fad0daf1c3cd48bff9263c731b0d9e2/charset_normalizer-3.4.0-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:47334db71978b23ebcf3c0f9f5ee98b8d65992b65c9c4f2d34c2eaf5bcaf0594", size = 139076 },
    { url = "https://files.pythonhosted.org/packages/fb/9d/9c13753a5a6e0db4a0a6edb1cef7aee39859177b64e1a1e748a6e3ba62c2/charset_normalizer-3.4.0-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:8ce7fd6767a1cc5a92a639b391891bf1c268b03ec7e021c7d6d902285259685c", size = 146874 },
    { url = "https://files.pythonhosted.org/packages/75/d2/0ab54463d3410709c09266dfb416d032a08f97fd7d60e94b8c6ef54ae14b/charset_normalizer-3.4.0-cp311-cp311-musllinux_1_2_ppc64le.whl", hash = "sha256:f1a2f519ae173b5b6a2c9d5fa3116ce16e48b3462c8b96dfdded11055e3d6365", size = 150871 },
    { url = "https://files.pythonhosted.org/packages/8d/c9/27e41d481557be53d51e60750b85aa40eaf52b841946b3cdeff363105737/charset_normalizer-3.4.0-cp311-cp311-musllinux_1_2_s390x.whl", hash = "sha256:63bc5c4ae26e4bc6be6469943b8253c0fd4e4186c43ad46e713ea61a0ba49129", size = 148546 },
    { url = "https://files.pythonhosted.org/packages/ee/44/4f62042ca8cdc0cabf87c0fc00ae27cd8b53ab68be3605ba6d071f742ad3/charset_normalizer-3.4.0-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:bcb4f8ea87d03bc51ad04add8ceaf9b0f085ac045ab4d74e73bbc2dc033f0236", size = 143048 },
    { url = "https://files.pythonhosted.org/packages/01/f8/38842422988b795220eb8038745d27a675ce066e2ada79516c118f291f07/charset_normalizer-3.4.0-cp311-cp311-win32.whl", hash = "sha256:9ae4ef0b3f6b41bad6366fb0ea4fc1d7ed051528e113a60fa2a65a9abb5b1d99", size = 94389 },
    { url = "https://files.pythonhosted.org/packages/0b/6e/b13bd47fa9023b3699e94abf565b5a2f0b0be6e9ddac9812182596ee62e4/charset_normalizer-3.4.0-cp311-cp311-win_amd64.whl", hash = "sha256:cee4373f4d3ad28f1ab6290684d8e2ebdb9e7a1b74fdc39e4c211995f77bec27", size = 101752 },
    { url = "https://files.pythonhosted.org/packages/d3/0b/4b7a70987abf9b8196845806198975b6aab4ce016632f817ad758a5aa056/charset_normalizer-3.4.0-cp312-cp312-macosx_10_13_universal2.whl", hash = "sha256:0713f3adb9d03d49d365b70b84775d0a0d18e4ab08d12bc46baa6132ba78aaf6", size = 194445 },
    { url = "https://files.pythonhosted.org/packages/50/89/354cc56cf4dd2449715bc9a0f54f3aef3dc700d2d62d1fa5bbea53b13426/charset_normalizer-3.4.0-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:de7376c29d95d6719048c194a9cf1a1b0393fbe8488a22008610b0361d834ecf", size = 125275 },
    { url = "https://files.pythonhosted.org/packages/fa/44/b730e2a2580110ced837ac083d8ad222343c96bb6b66e9e4e706e4d0b6df/charset_normalizer-3.4.0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:4a51b48f42d9358460b78725283f04bddaf44a9358197b889657deba38f329db", size = 119020 },
    { url = "https://files.pythonhosted.org/packages/9d/e4/9263b8240ed9472a2ae7ddc3e516e71ef46617fe40eaa51221ccd4ad9a27/charset_normalizer-3.4.0-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:b295729485b06c1a0683af02a9e42d2caa9db04a373dc38a6a58cdd1e8abddf1", size = 139128 },
    { url = "https://files.pythonhosted.org/packages/6b/e3/9f73e779315a54334240353eaea75854a9a690f3f580e4bd85d977cb2204/charset_normalizer-3.4.0-cp312-cp312-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:ee803480535c44e7f5ad00788526da7d85525cfefaf8acf8ab9a310000be4b03", size = 149277 },
    { url = "https://files.pythonhosted.org/packages/1a/cf/f1f50c2f295312edb8a548d3fa56a5c923b146cd3f24114d5adb7e7be558/charset_normalizer-3.4.0-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:3d59d125ffbd6d552765510e3f31ed75ebac2c7470c7274195b9161a32350284", size = 142174 },
    { url = "https://files.pythonhosted.org/packages/16/92/92a76dc2ff3a12e69ba94e7e05168d37d0345fa08c87e1fe24d0c2a42223/charset_normalizer-3.4.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:8cda06946eac330cbe6598f77bb54e690b4ca93f593dee1568ad22b04f347c15", size = 143838 },
    { url = "https://files.pythonhosted.org/packages/a4/01/2117ff2b1dfc61695daf2babe4a874bca328489afa85952440b59819e9d7/charset_normalizer-3.4.0-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:07afec21bbbbf8a5cc3651aa96b980afe2526e7f048fdfb7f1014d84acc8b6d8", size = 146149 },
    { url = "https://files.pythonhosted.org/packages/f6/9b/93a332b8d25b347f6839ca0a61b7f0287b0930216994e8bf67a75d050255/charset_normalizer-3.4.0-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:6b40e8d38afe634559e398cc32b1472f376a4099c75fe6299ae607e404c033b2", size = 140043 },
    { url = "https://files.pythonhosted.org/packages/ab/f6/7ac4a01adcdecbc7a7587767c776d53d369b8b971382b91211489535acf0/charset_normalizer-3.4.0-cp312-cp312-musllinux_1_2_i686.whl", hash = "sha256:b8dcd239c743aa2f9c22ce674a145e0a25cb1566c495928440a181ca1ccf6719", size = 148229 },
    { url = "https://files.pythonhosted.org/packages/9d/be/5708ad18161dee7dc6a0f7e6cf3a88ea6279c3e8484844c0590e50e803ef/charset_normalizer-3.4.0-cp312-cp312-musllinux_1_2_ppc64le.whl", hash = "sha256:84450ba661fb96e9fd67629b93d2941c871ca86fc38d835d19d4225ff946a631", size = 151556 },
    { url = "https://files.pythonhosted.org/packages/5a/bb/3d8bc22bacb9eb89785e83e6723f9888265f3a0de3b9ce724d66bd49884e/charset_normalizer-3.4.0-cp312-cp312-musllinux_1_2_s390x.whl", hash = "sha256:44aeb140295a2f0659e113b31cfe92c9061622cadbc9e2a2f7b8ef6b1e29ef4b", size = 149772 },
    { url = "https://files.pythonhosted.org/packages/f7/fa/d3fc622de05a86f30beea5fc4e9ac46aead4731e73fd9055496732bcc0a4/charset_normalizer-3.4.0-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:1db4e7fefefd0f548d73e2e2e041f9df5c59e178b4c72fbac4cc6f535cfb1565", size = 144800 },
    { url = "https://files.pythonhosted.org/packages/9a/65/bdb9bc496d7d190d725e96816e20e2ae3a6fa42a5cac99c3c3d6ff884118/charset_normalizer-3.4.0-cp312-cp312-win32.whl", hash = "sha256:5726cf76c982532c1863fb64d8c6dd0e4c90b6ece9feb06c9f202417a31f7dd7", size = 94836 },
    { url = "https://files.pythonhosted.org/packages/3e/67/7b72b69d25b89c0b3cea583ee372c43aa24df15f0e0f8d3982c57804984b/charset_normalizer-3.4.0-cp312-cp312-win_amd64.whl", hash = "sha256:b197e7094f232959f8f20541ead1d9862ac5ebea1d58e9849c1bf979255dfac9", size = 102187 },
    { url = "https://files.pythonhosted.org/packages/f3/89/68a4c86f1a0002810a27f12e9a7b22feb198c59b2f05231349fbce5c06f4/charset_normalizer-3.4.0-cp313-cp313-macosx_10_13_universal2.whl", hash = "sha256:dd4eda173a9fcccb5f2e2bd2a9f423d180194b1bf17cf59e3269899235b2a114", size = 194617 },
    { url = "https://files.pythonhosted.org/packages/4f/cd/8947fe425e2ab0aa57aceb7807af13a0e4162cd21eee42ef5b053447edf5/charset_normalizer-3.4.0-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:e9e3c4c9e1ed40ea53acf11e2a386383c3304212c965773704e4603d589343ed", size = 125310 },
    { url = "https://files.pythonhosted.org/packages/5b/f0/b5263e8668a4ee9becc2b451ed909e9c27058337fda5b8c49588183c267a/charset_normalizer-3.4.0-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:92a7e36b000bf022ef3dbb9c46bfe2d52c047d5e3f3343f43204263c5addc250", size = 119126 },
    { url = "https://files.pythonhosted.org/packages/ff/6e/e445afe4f7fda27a533f3234b627b3e515a1b9429bc981c9a5e2aa5d97b6/charset_normalizer-3.4.0-cp313-cp313-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:54b6a92d009cbe2fb11054ba694bc9e284dad30a26757b1e372a1fdddaf21920", size = 139342 },
    { url = "https://files.pythonhosted.org/packages/a1/b2/4af9993b532d93270538ad4926c8e37dc29f2111c36f9c629840c57cd9b3/charset_normalizer-3.4.0-cp313-cp313-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:1ffd9493de4c922f2a38c2bf62b831dcec90ac673ed1ca182fe11b4d8e9f2a64", size = 149383 },
    { url = "https://files.pythonhosted.org/packages/fb/6f/4e78c3b97686b871db9be6f31d64e9264e889f8c9d7ab33c771f847f79b7/charset_normalizer-3.4.0-cp313-cp313-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:35c404d74c2926d0287fbd63ed5d27eb911eb9e4a3bb2c6d294f3cfd4a9e0c23", size = 142214 },
    { url = "https://files.pythonhosted.org/packages/2b/c9/1c8fe3ce05d30c87eff498592c89015b19fade13df42850aafae09e94f35/charset_normalizer-3.4.0-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:4796efc4faf6b53a18e3d46343535caed491776a22af773f366534056c4e1fbc", size = 144104 },
    { url = "https://files.pythonhosted.org/packages/ee/68/efad5dcb306bf37db7db338338e7bb8ebd8cf38ee5bbd5ceaaaa46f257e6/charset_normalizer-3.4.0-cp313-cp313-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:e7fdd52961feb4c96507aa649550ec2a0d527c086d284749b2f582f2d40a2e0d", size = 146255 },
    { url = "https://files.pythonhosted.org/packages/0c/75/1ed813c3ffd200b1f3e71121c95da3f79e6d2a96120163443b3ad1057505/charset_normalizer-3.4.0-cp313-cp313-musllinux_1_2_aarch64.whl", hash = "sha256:92db3c28b5b2a273346bebb24857fda45601aef6ae1c011c0a997106581e8a88", size = 140251 },
    { url = "https://files.pythonhosted.org/packages/7d/0d/6f32255c1979653b448d3c709583557a4d24ff97ac4f3a5be156b2e6a210/charset_normalizer-3.4.0-cp313-cp313-musllinux_1_2_i686.whl", hash = "sha256:ab973df98fc99ab39080bfb0eb3a925181454d7c3ac8a1e695fddfae696d9e90", size = 148474 },
    { url = "https://files.pythonhosted.org/packages/ac/a0/c1b5298de4670d997101fef95b97ac440e8c8d8b4efa5a4d1ef44af82f0d/charset_normalizer-3.4.0-cp313-cp313-musllinux_1_2_ppc64le.whl", hash = "sha256:4b67fdab07fdd3c10bb21edab3cbfe8cf5696f453afce75d815d9d7223fbe88b", size = 151849 },
    { url = "https://files.pythonhosted.org/packages/04/4f/b3961ba0c664989ba63e30595a3ed0875d6790ff26671e2aae2fdc28a399/charset_normalizer-3.4.0-cp313-cp313-musllinux_1_2_s390x.whl", hash = "sha256:aa41e526a5d4a9dfcfbab0716c7e8a1b215abd3f3df5a45cf18a12721d31cb5d", size = 149781 },
    { url = "https://files.pythonhosted.org/packages/d8/90/6af4cd042066a4adad58ae25648a12c09c879efa4849c705719ba1b23d8c/charset_normalizer-3.4.0-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:ffc519621dce0c767e96b9c53f09c5d215578e10b02c285809f76509a3931482", size = 144970 },
    { url = "https://files.pythonhosted.org/packages/cc/67/e5e7e0cbfefc4ca79025238b43cdf8a2037854195b37d6417f3d0895c4c2/charset_normalizer-3.4.0-cp313-cp313-win32.whl", hash = "sha256:f19c1585933c82098c2a520f8ec1227f20e339e33aca8fa6f956f6691b784e67", size = 94973 },
    { url = "https://files.pythonhosted.org/packages/65/97/fc9bbc54ee13d33dc54a7fcf17b26368b18505500fc01e228c27b5222d80/charset_normalizer-3.4.0-cp313-cp313-win_amd64.whl", hash = "sha256:707b82d19e65c9bd28b81dde95249b07bf9f5b90ebe1ef17d9b57473f8a64b7b", size = 102308 },
    { url = "https://files.pythonhosted.org/packages/bf/9b/08c0432272d77b04803958a4598a51e2a4b51c06640af8b8f0f908c18bf2/charset_normalizer-3.4.0-py3-none-any.whl", hash = "sha256:fe9f97feb71aa9896b81973a7bbada8c49501dc73e58a10fcef6663af95e5079", size = 49446 },
]

[[package]]
name = "click"
version = "8.1.7"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "colorama", marker = "platform_system == 'Windows'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/96/d3/f04c7bfcf5c1862a2a5b845c6b2b360488cf47af55dfa79c98f6a6bf98b5/click-8.1.7.tar.gz", hash = "sha256:ca9853ad459e787e2192211578cc907e7594e294c7ccc834310722b41b9ca6de", size = 336121 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/00/2e/d53fa4befbf2cfa713304affc7ca780ce4fc1fd8710527771b58311a3229/click-8.1.7-py3-none-any.whl", hash = "sha256:ae74fb96c20a0277a1d615f1e4d73c8414f5a98db8b799a7931d1582f3390c28", size = 97941 },
]

[[package]]
name = "colorama"
version = "0.4.6"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/d8/53/6f443c9a4a8358a93a6792e2acffb9d9d5cb0a5cfd8802644b7b1c9a02e4/colorama-0.4.6.tar.gz", hash = "sha256:08695f5cb7ed6e0531a20572697297273c47b8cae5a63ffc6d6ed5c201be6e44", size = 27697 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/d1/d6/3965ed04c63042e047cb6a3e6ed1a63a35087b6a609aa3a15ed8ac56c221/colorama-0.4.6-py2.py3-none-any.whl", hash = "sha256:4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6", size = 25335 },
]

[[package]]
name = "copychat"
version = "0.5.2"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "gitpython" },
    { name = "pathspec" },
    { name = "pyperclip" },
    { name = "rich" },
    { name = "tiktoken" },
    { name = "typer" },
]
sdist = { url = "https://files.pythonhosted.org/packages/b4/fb/6001a67d1c072bc1082ee18f5ed67dc4338d78c3053b37f337bfd03b17d0/copychat-0.5.2.tar.gz", hash = "sha256:a341c629e8b5179678970173b65955fd8dcd7a29c2ecbb72ebd748a838730e23", size = 53018 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/00/8a/5fba1f777bd49954636cc715bcd2e1a546e35b2a73eaea01741afc96831f/copychat-0.5.2-py3-none-any.whl", hash = "sha256:1368e5d79e4912b29e91c20e4d47de3c375c5c974fa313ee46d2c62cf68895b0", size = 15412 },
]

[[package]]
name = "decorator"
version = "5.1.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/66/0c/8d907af351aa16b42caae42f9d6aa37b900c67308052d10fdce809f8d952/decorator-5.1.1.tar.gz", hash = "sha256:637996211036b6385ef91435e4fae22989472f9d571faba8927ba8253acbc330", size = 35016 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/d5/50/83c593b07763e1161326b3b8c6686f0f4b0f24d5526546bee538c89837d6/decorator-5.1.1-py3-none-any.whl", hash = "sha256:b8c3f85900b9dc423225913c5aace94729fe1fa9763b38939a95226f02d37186", size = 9073 },
]

[[package]]
name = "distlib"
version = "0.3.9"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/0d/dd/1bec4c5ddb504ca60fc29472f3d27e8d4da1257a854e1d96742f15c1d02d/distlib-0.3.9.tar.gz", hash = "sha256:a60f20dea646b8a33f3e7772f74dc0b2d0772d2837ee1342a00645c81edf9403", size = 613923 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/91/a1/cf2472db20f7ce4a6be1253a81cfdf85ad9c7885ffbed7047fb72c24cf87/distlib-0.3.9-py2.py3-none-any.whl", hash = "sha256:47f8c22fd27c27e25a65601af709b38e4f0a45ea4fc2e710f65755fa8caaaf87", size = 468973 },
]

[[package]]
name = "exceptiongroup"
version = "1.2.2"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/09/35/2495c4ac46b980e4ca1f6ad6db102322ef3ad2410b79fdde159a4b0f3b92/exceptiongroup-1.2.2.tar.gz", hash = "sha256:47c2edf7c6738fafb49fd34290706d1a1a2f4d1c6df275526b62cbb4aa5393cc", size = 28883 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/02/cc/b7e31358aac6ed1ef2bb790a9746ac2c69bcb3c8588b41616914eb106eaf/exceptiongroup-1.2.2-py3-none-any.whl", hash = "sha256:3111b9d131c238bec2f8f516e123e14ba243563fb135d3fe885990585aa7795b", size = 16453 },
]

[[package]]
name = "execnet"
version = "2.1.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/bb/ff/b4c0dc78fbe20c3e59c0c7334de0c27eb4001a2b2017999af398bf730817/execnet-2.1.1.tar.gz", hash = "sha256:5189b52c6121c24feae288166ab41b32549c7e2348652736540b9e6e7d4e72e3", size = 166524 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/43/09/2aea36ff60d16dd8879bdb2f5b3ee0ba8d08cbbdcdfe870e695ce3784385/execnet-2.1.1-py3-none-any.whl", hash = "sha256:26dee51f1b80cebd6d0ca8e74dd8745419761d3bef34163928cbebbdc4749fdc", size = 40612 },
]

[[package]]
name = "executing"
version = "2.1.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/8c/e3/7d45f492c2c4a0e8e0fad57d081a7c8a0286cdd86372b070cca1ec0caa1e/executing-2.1.0.tar.gz", hash = "sha256:8ea27ddd260da8150fa5a708269c4a10e76161e2496ec3e587da9e3c0fe4b9ab", size = 977485 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/b5/fd/afcd0496feca3276f509df3dbd5dae726fcc756f1a08d9e25abe1733f962/executing-2.1.0-py2.py3-none-any.whl", hash = "sha256:8d63781349375b5ebccc3142f4b30350c0cd9c79f921cde38be2be4637e98eaf", size = 25805 },
]

[[package]]
name = "fancycompleter"
version = "0.9.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "pyreadline", marker = "platform_system == 'Windows'" },
    { name = "pyrepl" },
]
sdist = { url = "https://files.pythonhosted.org/packages/a9/95/649d135442d8ecf8af5c7e235550c628056423c96c4bc6787348bdae9248/fancycompleter-0.9.1.tar.gz", hash = "sha256:09e0feb8ae242abdfd7ef2ba55069a46f011814a80fe5476be48f51b00247272", size = 10866 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/38/ef/c08926112034d017633f693d3afc8343393a035134a29dfc12dcd71b0375/fancycompleter-0.9.1-py3-none-any.whl", hash = "sha256:dd076bca7d9d524cc7f25ec8f35ef95388ffef9ef46def4d3d25e9b044ad7080", size = 9681 },
]

[[package]]
name = "fastmcp"
version = "0.3.6.dev8+g3b5ae20"
source = { editable = "." }
dependencies = [
    { name = "httpx" },
    { name = "mcp" },
    { name = "pydantic" },
    { name = "pydantic-settings" },
    { name = "python-dotenv" },
    { name = "typer" },
]

[package.optional-dependencies]
dev = [
    { name = "copychat" },
    { name = "ipython" },
    { name = "pdbpp" },
    { name = "pre-commit" },
    { name = "pyright" },
    { name = "pytest" },
    { name = "pytest-asyncio" },
    { name = "pytest-flakefinder" },
    { name = "pytest-xdist" },
    { name = "ruff" },
]
tests = [
    { name = "pre-commit" },
    { name = "pyright" },
    { name = "pytest" },
    { name = "pytest-asyncio" },
    { name = "pytest-flakefinder" },
    { name = "pytest-xdist" },
    { name = "ruff" },
]

[package.metadata]
requires-dist = [
    { name = "copychat", marker = "extra == 'dev'", specifier = ">=0.5.2" },
    { name = "httpx", specifier = ">=0.26.0" },
    { name = "ipython", marker = "extra == 'dev'", specifier = ">=8.12.3" },
    { name = "mcp", specifier = ">=1.0.0,<2.0.0" },
    { name = "pdbpp", marker = "extra == 'dev'", specifier = ">=0.10.3" },
    { name = "pre-commit", marker = "extra == 'dev'" },
    { name = "pre-commit", marker = "extra == 'tests'" },
    { name = "pydantic", specifier = ">=2.5.3,<3.0.0" },
    { name = "pydantic-settings", specifier = ">=2.6.1" },
    { name = "pyright", marker = "extra == 'dev'", specifier = ">=1.1.389" },
    { name = "pyright", marker = "extra == 'tests'", specifier = ">=1.1.389" },
    { name = "pytest", marker = "extra == 'dev'", specifier = ">=8.3.3" },
    { name = "pytest", marker = "extra == 'tests'", specifier = ">=8.3.3" },
    { name = "pytest-asyncio", marker = "extra == 'dev'", specifier = ">=0.23.5" },
    { name = "pytest-asyncio", marker = "extra == 'tests'", specifier = ">=0.23.5" },
    { name = "pytest-flakefinder", marker = "extra == 'dev'" },
    { name = "pytest-flakefinder", marker = "extra == 'tests'" },
    { name = "pytest-xdist", marker = "extra == 'dev'", specifier = ">=3.6.1" },
    { name = "pytest-xdist", marker = "extra == 'tests'", specifier = ">=3.6.1" },
    { name = "python-dotenv", specifier = ">=1.0.1" },
    { name = "ruff", marker = "extra == 'dev'" },
    { name = "ruff", marker = "extra == 'tests'" },
    { name = "typer", specifier = ">=0.9.0" },
]

[[package]]
name = "filelock"
version = "3.16.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/9d/db/3ef5bb276dae18d6ec2124224403d1d67bccdbefc17af4cc8f553e341ab1/filelock-3.16.1.tar.gz", hash = "sha256:c249fbfcd5db47e5e2d6d62198e565475ee65e4831e2561c8e313fa7eb961435", size = 18037 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/b9/f8/feced7779d755758a52d1f6635d990b8d98dc0a29fa568bbe0625f18fdf3/filelock-3.16.1-py3-none-any.whl", hash = "sha256:2082e5703d51fbf98ea75855d9d5527e33d8ff23099bec374a134febee6946b0", size = 16163 },
]

[[package]]
name = "gitdb"
version = "4.0.11"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "smmap" },
]
sdist = { url = "https://files.pythonhosted.org/packages/19/0d/bbb5b5ee188dec84647a4664f3e11b06ade2bde568dbd489d9d64adef8ed/gitdb-4.0.11.tar.gz", hash = "sha256:bf5421126136d6d0af55bc1e7c1af1c397a34f5b7bd79e776cd3e89785c2b04b", size = 394469 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/fd/5b/8f0c4a5bb9fd491c277c21eff7ccae71b47d43c4446c9d0c6cff2fe8c2c4/gitdb-4.0.11-py3-none-any.whl", hash = "sha256:81a3407ddd2ee8df444cbacea00e2d038e40150acfa3001696fe0dcf1d3adfa4", size = 62721 },
]

[[package]]
name = "gitpython"
version = "3.1.43"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "gitdb" },
]
sdist = { url = "https://files.pythonhosted.org/packages/b6/a1/106fd9fa2dd989b6fb36e5893961f82992cf676381707253e0bf93eb1662/GitPython-3.1.43.tar.gz", hash = "sha256:35f314a9f878467f5453cc1fee295c3e18e52f1b99f10f6cf5b1682e968a9e7c", size = 214149 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/e9/bd/cc3a402a6439c15c3d4294333e13042b915bbeab54edc457c723931fed3f/GitPython-3.1.43-py3-none-any.whl", hash = "sha256:eec7ec56b92aad751f9912a73404bc02ba212a23adb2c7098ee668417051a1ff", size = 207337 },
]

[[package]]
name = "h11"
version = "0.14.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/f5/38/3af3d3633a34a3316095b39c8e8fb4853a28a536e55d347bd8d8e9a14b03/h11-0.14.0.tar.gz", hash = "sha256:8f19fbbe99e72420ff35c00b27a34cb9937e902a8b810e2c88300c6f0a3b699d", size = 100418 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/95/04/ff642e65ad6b90db43e668d70ffb6736436c7ce41fcc549f4e9472234127/h11-0.14.0-py3-none-any.whl", hash = "sha256:e3fe4ac4b851c468cc8363d500db52c2ead036020723024a109d37346efaa761", size = 58259 },
]

[[package]]
name = "httpcore"
version = "1.0.7"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "certifi" },
    { name = "h11" },
]
sdist = { url = "https://files.pythonhosted.org/packages/6a/41/d7d0a89eb493922c37d343b607bc1b5da7f5be7e383740b4753ad8943e90/httpcore-1.0.7.tar.gz", hash = "sha256:8551cb62a169ec7162ac7be8d4817d561f60e08eaa485234898414bb5a8a0b4c", size = 85196 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/87/f5/72347bc88306acb359581ac4d52f23c0ef445b57157adedb9aee0cd689d2/httpcore-1.0.7-py3-none-any.whl", hash = "sha256:a3fff8f43dc260d5bd363d9f9cf1830fa3a458b332856f34282de498ed420edd", size = 78551 },
]

[[package]]
name = "httpx"
version = "0.28.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "anyio" },
    { name = "certifi" },
    { name = "httpcore" },
    { name = "idna" },
]
sdist = { url = "https://files.pythonhosted.org/packages/10/df/676b7cf674dd1bdc71a64ad393c89879f75e4a0ab8395165b498262ae106/httpx-0.28.0.tar.gz", hash = "sha256:0858d3bab51ba7e386637f22a61d8ccddaeec5f3fe4209da3a6168dbb91573e0", size = 141307 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/8f/fb/a19866137577ba60c6d8b69498dc36be479b13ba454f691348ddf428f185/httpx-0.28.0-py3-none-any.whl", hash = "sha256:dc0b419a0cfeb6e8b34e85167c0da2671206f5095f1baa9663d23bcfd6b535fc", size = 73551 },
]

[[package]]
name = "httpx-sse"
version = "0.4.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/4c/60/8f4281fa9bbf3c8034fd54c0e7412e66edbab6bc74c4996bd616f8d0406e/httpx-sse-0.4.0.tar.gz", hash = "sha256:1e81a3a3070ce322add1d3529ed42eb5f70817f45ed6ec915ab753f961139721", size = 12624 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/e1/9b/a181f281f65d776426002f330c31849b86b31fc9d848db62e16f03ff739f/httpx_sse-0.4.0-py3-none-any.whl", hash = "sha256:f329af6eae57eaa2bdfd962b42524764af68075ea87370a2de920af5341e318f", size = 7819 },
]

[[package]]
name = "identify"
version = "2.6.3"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/1a/5f/05f0d167be94585d502b4adf8c7af31f1dc0b1c7e14f9938a88fdbbcf4a7/identify-2.6.3.tar.gz", hash = "sha256:62f5dae9b5fef52c84cc188514e9ea4f3f636b1d8799ab5ebc475471f9e47a02", size = 99179 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/c9/f5/09644a3ad803fae9eca8efa17e1f2aef380c7f0b02f7ec4e8d446e51d64a/identify-2.6.3-py2.py3-none-any.whl", hash = "sha256:9edba65473324c2ea9684b1f944fe3191db3345e50b6d04571d10ed164f8d7bd", size = 99049 },
]

[[package]]
name = "idna"
version = "3.10"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/f1/70/7703c29685631f5a7590aa73f1f1d3fa9a380e654b86af429e0934a32f7d/idna-3.10.tar.gz", hash = "sha256:12f65c9b470abda6dc35cf8e63cc574b1c52b11df2c86030af0ac09b01b13ea9", size = 190490 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/76/c6/c88e154df9c4e1a2a66ccf0005a88dfb2650c1dffb6f5ce603dfbd452ce3/idna-3.10-py3-none-any.whl", hash = "sha256:946d195a0d259cbba61165e88e65941f16e9b36ea6ddb97f00452bae8b1287d3", size = 70442 },
]

[[package]]
name = "iniconfig"
version = "2.0.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/d7/4b/cbd8e699e64a6f16ca3a8220661b5f83792b3017d0f79807cb8708d33913/iniconfig-2.0.0.tar.gz", hash = "sha256:2d91e135bf72d31a410b17c16da610a82cb55f6b0477d1a902134b24a455b8b3", size = 4646 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/ef/a6/62565a6e1cf69e10f5727360368e451d4b7f58beeac6173dc9db836a5b46/iniconfig-2.0.0-py3-none-any.whl", hash = "sha256:b6a85871a79d2e3b22d2d1b94ac2824226a63c6b741c88f7ae975f18b6778374", size = 5892 },
]

[[package]]
name = "ipython"
version = "8.30.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "colorama", marker = "sys_platform == 'win32'" },
    { name = "decorator" },
    { name = "exceptiongroup", marker = "python_full_version < '3.11'" },
    { name = "jedi" },
    { name = "matplotlib-inline" },
    { name = "pexpect", marker = "sys_platform != 'emscripten' and sys_platform != 'win32'" },
    { name = "prompt-toolkit" },
    { name = "pygments" },
    { name = "stack-data" },
    { name = "traitlets" },
    { name = "typing-extensions", marker = "python_full_version < '3.12'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/d8/8b/710af065ab8ed05649afa5bd1e07401637c9ec9fb7cfda9eac7e91e9fbd4/ipython-8.30.0.tar.gz", hash = "sha256:cb0a405a306d2995a5cbb9901894d240784a9f341394c6ba3f4fe8c6eb89ff6e", size = 5592205 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/1d/f3/1332ba2f682b07b304ad34cad2f003adcfeb349486103f4b632335074a7c/ipython-8.30.0-py3-none-any.whl", hash = "sha256:85ec56a7e20f6c38fce7727dcca699ae4ffc85985aa7b23635a8008f918ae321", size = 820765 },
]

[[package]]
name = "jedi"
version = "0.19.2"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "parso" },
]
sdist = { url = "https://files.pythonhosted.org/packages/72/3a/79a912fbd4d8dd6fbb02bf69afd3bb72cf0c729bb3063c6f4498603db17a/jedi-0.19.2.tar.gz", hash = "sha256:4770dc3de41bde3966b02eb84fbcf557fb33cce26ad23da12c742fb50ecb11f0", size = 1231287 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/c0/5a/9cac0c82afec3d09ccd97c8b6502d48f165f9124db81b4bcb90b4af974ee/jedi-0.19.2-py2.py3-none-any.whl", hash = "sha256:a8ef22bde8490f57fe5c7681a3c83cb58874daf72b4784de3cce5b6ef6edb5b9", size = 1572278 },
]

[[package]]
name = "markdown-it-py"
version = "3.0.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "mdurl" },
]
sdist = { url = "https://files.pythonhosted.org/packages/38/71/3b932df36c1a044d397a1f92d1cf91ee0a503d91e470cbd670aa66b07ed0/markdown-it-py-3.0.0.tar.gz", hash = "sha256:e3f60a94fa066dc52ec76661e37c851cb232d92f9886b15cb560aaada2df8feb", size = 74596 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/42/d7/1ec15b46af6af88f19b8e5ffea08fa375d433c998b8a7639e76935c14f1f/markdown_it_py-3.0.0-py3-none-any.whl", hash = "sha256:355216845c60bd96232cd8d8c40e8f9765cc86f46880e43a8fd22dc1a1a8cab1", size = 87528 },
]

[[package]]
name = "matplotlib-inline"
version = "0.1.7"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "traitlets" },
]
sdist = { url = "https://files.pythonhosted.org/packages/99/5b/a36a337438a14116b16480db471ad061c36c3694df7c2084a0da7ba538b7/matplotlib_inline-0.1.7.tar.gz", hash = "sha256:8423b23ec666be3d16e16b60bdd8ac4e86e840ebd1dd11a30b9f117f2fa0ab90", size = 8159 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/8f/8e/9ad090d3553c280a8060fbf6e24dc1c0c29704ee7d1c372f0c174aa59285/matplotlib_inline-0.1.7-py3-none-any.whl", hash = "sha256:df192d39a4ff8f21b1895d72e6a13f5fcc5099f00fa84384e0ea28c2cc0653ca", size = 9899 },
]

[[package]]
name = "mcp"
version = "1.0.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "anyio" },
    { name = "httpx" },
    { name = "httpx-sse" },
    { name = "pydantic" },
    { name = "sse-starlette" },
    { name = "starlette" },
]
sdist = { url = "https://files.pythonhosted.org/packages/97/de/a9ec0a1b6439f90ea59f89004bb2e7ec6890dfaeef809751d9e6577dca7e/mcp-1.0.0.tar.gz", hash = "sha256:dba51ce0b5c6a80e25576f606760c49a91ee90210fed805b530ca165d3bbc9b7", size = 82891 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/56/89/900c0c8445ec001d3725e475fc553b0feb2e8a51be018f3bb7de51e683db/mcp-1.0.0-py3-none-any.whl", hash = "sha256:bbe70ffa3341cd4da78b5eb504958355c68381fb29971471cea1e642a2af5b8a", size = 36361 },
]

[[package]]
name = "mdurl"
version = "0.1.2"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/d6/54/cfe61301667036ec958cb99bd3efefba235e65cdeb9c84d24a8293ba1d90/mdurl-0.1.2.tar.gz", hash = "sha256:bb413d29f5eea38f31dd4754dd7377d4465116fb207585f97bf925588687c1ba", size = 8729 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/b3/38/89ba8ad64ae25be8de66a6d463314cf1eb366222074cfda9ee839c56a4b4/mdurl-0.1.2-py3-none-any.whl", hash = "sha256:84008a41e51615a49fc9966191ff91509e3c40b939176e643fd50a5c2196b8f8", size = 9979 },
]

[[package]]
name = "nodeenv"
version = "1.9.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/43/16/fc88b08840de0e0a72a2f9d8c6bae36be573e475a6326ae854bcc549fc45/nodeenv-1.9.1.tar.gz", hash = "sha256:6ec12890a2dab7946721edbfbcd91f3319c6ccc9aec47be7c7e6b7011ee6645f", size = 47437 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/d2/1d/1b658dbd2b9fa9c4c9f32accbfc0205d532c8c6194dc0f2a4c0428e7128a/nodeenv-1.9.1-py2.py3-none-any.whl", hash = "sha256:ba11c9782d29c27c70ffbdda2d7415098754709be8a7056d79a737cd901155c9", size = 22314 },
]

[[package]]
name = "packaging"
version = "24.2"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/d0/63/68dbb6eb2de9cb10ee4c9c14a0148804425e13c4fb20d61cce69f53106da/packaging-24.2.tar.gz", hash = "sha256:c228a6dc5e932d346bc5739379109d49e8853dd8223571c7c5b55260edc0b97f", size = 163950 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/88/ef/eb23f262cca3c0c4eb7ab1933c3b1f03d021f2c48f54763065b6f0e321be/packaging-24.2-py3-none-any.whl", hash = "sha256:09abb1bccd265c01f4a3aa3f7a7db064b36514d2cba19a2f694fe6150451a759", size = 65451 },
]

[[package]]
name = "parso"
version = "0.8.4"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/66/94/68e2e17afaa9169cf6412ab0f28623903be73d1b32e208d9e8e541bb086d/parso-0.8.4.tar.gz", hash = "sha256:eb3a7b58240fb99099a345571deecc0f9540ea5f4dd2fe14c2a99d6b281ab92d", size = 400609 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/c6/ac/dac4a63f978e4dcb3c6d3a78c4d8e0192a113d288502a1216950c41b1027/parso-0.8.4-py2.py3-none-any.whl", hash = "sha256:a418670a20291dacd2dddc80c377c5c3791378ee1e8d12bffc35420643d43f18", size = 103650 },
]

[[package]]
name = "pathspec"
version = "0.12.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/ca/bc/f35b8446f4531a7cb215605d100cd88b7ac6f44ab3fc94870c120ab3adbf/pathspec-0.12.1.tar.gz", hash = "sha256:a482d51503a1ab33b1c67a6c3813a26953dbdc71c31dacaef9a838c4e29f5712", size = 51043 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/cc/20/ff623b09d963f88bfde16306a54e12ee5ea43e9b597108672ff3a408aad6/pathspec-0.12.1-py3-none-any.whl", hash = "sha256:a0d503e138a4c123b27490a4f7beda6a01c6f288df0e4a8b79c7eb0dc7b4cc08", size = 31191 },
]

[[package]]
name = "pdbpp"
version = "0.10.3"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "fancycompleter" },
    { name = "pygments" },
    { name = "wmctrl" },
]
sdist = { url = "https://files.pythonhosted.org/packages/1f/a3/c4bd048256fd4b7d28767ca669c505e156f24d16355505c62e6fce3314df/pdbpp-0.10.3.tar.gz", hash = "sha256:d9e43f4fda388eeb365f2887f4e7b66ac09dce9b6236b76f63616530e2f669f5", size = 68116 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/93/ee/491e63a57fffa78b9de1c337b06c97d0cd0753e88c00571c7b011680332a/pdbpp-0.10.3-py2.py3-none-any.whl", hash = "sha256:79580568e33eb3d6f6b462b1187f53e10cd8e4538f7d31495c9181e2cf9665d1", size = 23961 },
]

[[package]]
name = "pexpect"
version = "4.9.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "ptyprocess" },
]
sdist = { url = "https://files.pythonhosted.org/packages/42/92/cc564bf6381ff43ce1f4d06852fc19a2f11d180f23dc32d9588bee2f149d/pexpect-4.9.0.tar.gz", hash = "sha256:ee7d41123f3c9911050ea2c2dac107568dc43b2d3b0c7557a33212c398ead30f", size = 166450 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/9e/c3/059298687310d527a58bb01f3b1965787ee3b40dce76752eda8b44e9a2c5/pexpect-4.9.0-py2.py3-none-any.whl", hash = "sha256:7236d1e080e4936be2dc3e326cec0af72acf9212a7e1d060210e70a47e253523", size = 63772 },
]

[[package]]
name = "platformdirs"
version = "4.3.6"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/13/fc/128cc9cb8f03208bdbf93d3aa862e16d376844a14f9a0ce5cf4507372de4/platformdirs-4.3.6.tar.gz", hash = "sha256:357fb2acbc885b0419afd3ce3ed34564c13c9b95c89360cd9563f73aa5e2b907", size = 21302 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/3c/a6/bc1012356d8ece4d66dd75c4b9fc6c1f6650ddd5991e421177d9f8f671be/platformdirs-4.3.6-py3-none-any.whl", hash = "sha256:73e575e1408ab8103900836b97580d5307456908a03e92031bab39e4554cc3fb", size = 18439 },
]

[[package]]
name = "pluggy"
version = "1.5.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/96/2d/02d4312c973c6050a18b314a5ad0b3210edb65a906f868e31c111dede4a6/pluggy-1.5.0.tar.gz", hash = "sha256:2cffa88e94fdc978c4c574f15f9e59b7f4201d439195c3715ca9e2486f1d0cf1", size = 67955 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/88/5f/e351af9a41f866ac3f1fac4ca0613908d9a41741cfcf2228f4ad853b697d/pluggy-1.5.0-py3-none-any.whl", hash = "sha256:44e1ad92c8ca002de6377e165f3e0f1be63266ab4d554740532335b9d75ea669", size = 20556 },
]

[[package]]
name = "pre-commit"
version = "4.0.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "cfgv" },
    { name = "identify" },
    { name = "nodeenv" },
    { name = "pyyaml" },
    { name = "virtualenv" },
]
sdist = { url = "https://files.pythonhosted.org/packages/2e/c8/e22c292035f1bac8b9f5237a2622305bc0304e776080b246f3df57c4ff9f/pre_commit-4.0.1.tar.gz", hash = "sha256:80905ac375958c0444c65e9cebebd948b3cdb518f335a091a670a89d652139d2", size = 191678 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/16/8f/496e10d51edd6671ebe0432e33ff800aa86775d2d147ce7d43389324a525/pre_commit-4.0.1-py2.py3-none-any.whl", hash = "sha256:efde913840816312445dc98787724647c65473daefe420785f885e8ed9a06878", size = 218713 },
]

[[package]]
name = "prompt-toolkit"
version = "3.0.48"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "wcwidth" },
]
sdist = { url = "https://files.pythonhosted.org/packages/2d/4f/feb5e137aff82f7c7f3248267b97451da3644f6cdc218edfe549fb354127/prompt_toolkit-3.0.48.tar.gz", hash = "sha256:d6623ab0477a80df74e646bdbc93621143f5caf104206aa29294d53de1a03d90", size = 424684 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/a9/6a/fd08d94654f7e67c52ca30523a178b3f8ccc4237fce4be90d39c938a831a/prompt_toolkit-3.0.48-py3-none-any.whl", hash = "sha256:f49a827f90062e411f1ce1f854f2aedb3c23353244f8108b89283587397ac10e", size = 386595 },
]

[[package]]
name = "ptyprocess"
version = "0.7.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/20/e5/16ff212c1e452235a90aeb09066144d0c5a6a8c0834397e03f5224495c4e/ptyprocess-0.7.0.tar.gz", hash = "sha256:5c5d0a3b48ceee0b48485e0c26037c0acd7d29765ca3fbb5cb3831d347423220", size = 70762 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/22/a6/858897256d0deac81a172289110f31629fc4cee19b6f01283303e18c8db3/ptyprocess-0.7.0-py2.py3-none-any.whl", hash = "sha256:4b41f3967fce3af57cc7e94b888626c18bf37a083e3651ca8feeb66d492fef35", size = 13993 },
]

[[package]]
name = "pure-eval"
version = "0.2.3"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/cd/05/0a34433a064256a578f1783a10da6df098ceaa4a57bbeaa96a6c0352786b/pure_eval-0.2.3.tar.gz", hash = "sha256:5f4e983f40564c576c7c8635ae88db5956bb2229d7e9237d03b3c0b0190eaf42", size = 19752 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/8e/37/efad0257dc6e593a18957422533ff0f87ede7c9c6ea010a2177d738fb82f/pure_eval-0.2.3-py3-none-any.whl", hash = "sha256:1db8e35b67b3d218d818ae653e27f06c3aa420901fa7b081ca98cbedc874e0d0", size = 11842 },
]

[[package]]
name = "pydantic"
version = "2.10.2"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "annotated-types" },
    { name = "pydantic-core" },
    { name = "typing-extensions" },
]
sdist = { url = "https://files.pythonhosted.org/packages/41/86/a03390cb12cf64e2a8df07c267f3eb8d5035e0f9a04bb20fb79403d2a00e/pydantic-2.10.2.tar.gz", hash = "sha256:2bc2d7f17232e0841cbba4641e65ba1eb6fafb3a08de3a091ff3ce14a197c4fa", size = 785401 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/d5/74/da832196702d0c56eb86b75bfa346db9238617e29b0b7ee3b8b4eccfe654/pydantic-2.10.2-py3-none-any.whl", hash = "sha256:cfb96e45951117c3024e6b67b25cdc33a3cb7b2fa62e239f7af1378358a1d99e", size = 456364 },
]

[[package]]
name = "pydantic-core"
version = "2.27.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "typing-extensions" },
]
sdist = { url = "https://files.pythonhosted.org/packages/a6/9f/7de1f19b6aea45aeb441838782d68352e71bfa98ee6fa048d5041991b33e/pydantic_core-2.27.1.tar.gz", hash = "sha256:62a763352879b84aa31058fc931884055fd75089cccbd9d58bb6afd01141b235", size = 412785 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/6e/ce/60fd96895c09738648c83f3f00f595c807cb6735c70d3306b548cc96dd49/pydantic_core-2.27.1-cp310-cp310-macosx_10_12_x86_64.whl", hash = "sha256:71a5e35c75c021aaf400ac048dacc855f000bdfed91614b4a726f7432f1f3d6a", size = 1897984 },
    { url = "https://files.pythonhosted.org/packages/fd/b9/84623d6b6be98cc209b06687d9bca5a7b966ffed008d15225dd0d20cce2e/pydantic_core-2.27.1-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:f82d068a2d6ecfc6e054726080af69a6764a10015467d7d7b9f66d6ed5afa23b", size = 1807491 },
    { url = "https://files.pythonhosted.org/packages/01/72/59a70165eabbc93b1111d42df9ca016a4aa109409db04304829377947028/pydantic_core-2.27.1-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:121ceb0e822f79163dd4699e4c54f5ad38b157084d97b34de8b232bcaad70278", size = 1831953 },
    { url = "https://files.pythonhosted.org/packages/7c/0c/24841136476adafd26f94b45bb718a78cb0500bd7b4f8d667b67c29d7b0d/pydantic_core-2.27.1-cp310-cp310-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:4603137322c18eaf2e06a4495f426aa8d8388940f3c457e7548145011bb68e05", size = 1856071 },
    { url = "https://files.pythonhosted.org/packages/53/5e/c32957a09cceb2af10d7642df45d1e3dbd8596061f700eac93b801de53c0/pydantic_core-2.27.1-cp310-cp310-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:a33cd6ad9017bbeaa9ed78a2e0752c5e250eafb9534f308e7a5f7849b0b1bfb4", size = 2038439 },
    { url = "https://files.pythonhosted.org/packages/e4/8f/979ab3eccd118b638cd6d8f980fea8794f45018255a36044dea40fe579d4/pydantic_core-2.27.1-cp310-cp310-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:15cc53a3179ba0fcefe1e3ae50beb2784dede4003ad2dfd24f81bba4b23a454f", size = 2787416 },
    { url = "https://files.pythonhosted.org/packages/02/1d/00f2e4626565b3b6d3690dab4d4fe1a26edd6a20e53749eb21ca892ef2df/pydantic_core-2.27.1-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:45d9c5eb9273aa50999ad6adc6be5e0ecea7e09dbd0d31bd0c65a55a2592ca08", size = 2134548 },
    { url = "https://files.pythonhosted.org/packages/9d/46/3112621204128b90898adc2e721a3cd6cf5626504178d6f32c33b5a43b79/pydantic_core-2.27.1-cp310-cp310-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:8bf7b66ce12a2ac52d16f776b31d16d91033150266eb796967a7e4621707e4f6", size = 1989882 },
    { url = "https://files.pythonhosted.org/packages/49/ec/557dd4ff5287ffffdf16a31d08d723de6762bb1b691879dc4423392309bc/pydantic_core-2.27.1-cp310-cp310-musllinux_1_1_aarch64.whl", hash = "sha256:655d7dd86f26cb15ce8a431036f66ce0318648f8853d709b4167786ec2fa4807", size = 1995829 },
    { url = "https://files.pythonhosted.org/packages/6e/b2/610dbeb74d8d43921a7234555e4c091cb050a2bdb8cfea86d07791ce01c5/pydantic_core-2.27.1-cp310-cp310-musllinux_1_1_armv7l.whl", hash = "sha256:5556470f1a2157031e676f776c2bc20acd34c1990ca5f7e56f1ebf938b9ab57c", size = 2091257 },
    { url = "https://files.pythonhosted.org/packages/8c/7f/4bf8e9d26a9118521c80b229291fa9558a07cdd9a968ec2d5c1026f14fbc/pydantic_core-2.27.1-cp310-cp310-musllinux_1_1_x86_64.whl", hash = "sha256:f69ed81ab24d5a3bd93861c8c4436f54afdf8e8cc421562b0c7504cf3be58206", size = 2143894 },
    { url = "https://files.pythonhosted.org/packages/1f/1c/875ac7139c958f4390f23656fe696d1acc8edf45fb81e4831960f12cd6e4/pydantic_core-2.27.1-cp310-none-win32.whl", hash = "sha256:f5a823165e6d04ccea61a9f0576f345f8ce40ed533013580e087bd4d7442b52c", size = 1816081 },
    { url = "https://files.pythonhosted.org/packages/d7/41/55a117acaeda25ceae51030b518032934f251b1dac3704a53781383e3491/pydantic_core-2.27.1-cp310-none-win_amd64.whl", hash = "sha256:57866a76e0b3823e0b56692d1a0bf722bffb324839bb5b7226a7dbd6c9a40b17", size = 1981109 },
    { url = "https://files.pythonhosted.org/packages/27/39/46fe47f2ad4746b478ba89c561cafe4428e02b3573df882334bd2964f9cb/pydantic_core-2.27.1-cp311-cp311-macosx_10_12_x86_64.whl", hash = "sha256:ac3b20653bdbe160febbea8aa6c079d3df19310d50ac314911ed8cc4eb7f8cb8", size = 1895553 },
    { url = "https://files.pythonhosted.org/packages/1c/00/0804e84a78b7fdb394fff4c4f429815a10e5e0993e6ae0e0b27dd20379ee/pydantic_core-2.27.1-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:a5a8e19d7c707c4cadb8c18f5f60c843052ae83c20fa7d44f41594c644a1d330", size = 1807220 },
    { url = "https://files.pythonhosted.org/packages/01/de/df51b3bac9820d38371f5a261020f505025df732ce566c2a2e7970b84c8c/pydantic_core-2.27.1-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:7f7059ca8d64fea7f238994c97d91f75965216bcbe5f695bb44f354893f11d52", size = 1829727 },
    { url = "https://files.pythonhosted.org/packages/5f/d9/c01d19da8f9e9fbdb2bf99f8358d145a312590374d0dc9dd8dbe484a9cde/pydantic_core-2.27.1-cp311-cp311-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:bed0f8a0eeea9fb72937ba118f9db0cb7e90773462af7962d382445f3005e5a4", size = 1854282 },
    { url = "https://files.pythonhosted.org/packages/5f/84/7db66eb12a0dc88c006abd6f3cbbf4232d26adfd827a28638c540d8f871d/pydantic_core-2.27.1-cp311-cp311-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:a3cb37038123447cf0f3ea4c74751f6a9d7afef0eb71aa07bf5f652b5e6a132c", size = 2037437 },
    { url = "https://files.pythonhosted.org/packages/34/ac/a2537958db8299fbabed81167d58cc1506049dba4163433524e06a7d9f4c/pydantic_core-2.27.1-cp311-cp311-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:84286494f6c5d05243456e04223d5a9417d7f443c3b76065e75001beb26f88de", size = 2780899 },
    { url = "https://files.pythonhosted.org/packages/4a/c1/3e38cd777ef832c4fdce11d204592e135ddeedb6c6f525478a53d1c7d3e5/pydantic_core-2.27.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:acc07b2cfc5b835444b44a9956846b578d27beeacd4b52e45489e93276241025", size = 2135022 },
    { url = "https://files.pythonhosted.org/packages/7a/69/b9952829f80fd555fe04340539d90e000a146f2a003d3fcd1e7077c06c71/pydantic_core-2.27.1-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:4fefee876e07a6e9aad7a8c8c9f85b0cdbe7df52b8a9552307b09050f7512c7e", size = 1987969 },
    { url = "https://files.pythonhosted.org/packages/05/72/257b5824d7988af43460c4e22b63932ed651fe98804cc2793068de7ec554/pydantic_core-2.27.1-cp311-cp311-musllinux_1_1_aarch64.whl", hash = "sha256:258c57abf1188926c774a4c94dd29237e77eda19462e5bb901d88adcab6af919", size = 1994625 },
    { url = "https://files.pythonhosted.org/packages/73/c3/78ed6b7f3278a36589bcdd01243189ade7fc9b26852844938b4d7693895b/pydantic_core-2.27.1-cp311-cp311-musllinux_1_1_armv7l.whl", hash = "sha256:35c14ac45fcfdf7167ca76cc80b2001205a8d5d16d80524e13508371fb8cdd9c", size = 2090089 },
    { url = "https://files.pythonhosted.org/packages/8d/c8/b4139b2f78579960353c4cd987e035108c93a78371bb19ba0dc1ac3b3220/pydantic_core-2.27.1-cp311-cp311-musllinux_1_1_x86_64.whl", hash = "sha256:d1b26e1dff225c31897696cab7d4f0a315d4c0d9e8666dbffdb28216f3b17fdc", size = 2142496 },
    { url = "https://files.pythonhosted.org/packages/3e/f8/171a03e97eb36c0b51981efe0f78460554a1d8311773d3d30e20c005164e/pydantic_core-2.27.1-cp311-none-win32.whl", hash = "sha256:2cdf7d86886bc6982354862204ae3b2f7f96f21a3eb0ba5ca0ac42c7b38598b9", size = 1811758 },
    { url = "https://files.pythonhosted.org/packages/6a/fe/4e0e63c418c1c76e33974a05266e5633e879d4061f9533b1706a86f77d5b/pydantic_core-2.27.1-cp311-none-win_amd64.whl", hash = "sha256:3af385b0cee8df3746c3f406f38bcbfdc9041b5c2d5ce3e5fc6637256e60bbc5", size = 1980864 },
    { url = "https://files.pythonhosted.org/packages/50/fc/93f7238a514c155a8ec02fc7ac6376177d449848115e4519b853820436c5/pydantic_core-2.27.1-cp311-none-win_arm64.whl", hash = "sha256:81f2ec23ddc1b476ff96563f2e8d723830b06dceae348ce02914a37cb4e74b89", size = 1864327 },
    { url = "https://files.pythonhosted.org/packages/be/51/2e9b3788feb2aebff2aa9dfbf060ec739b38c05c46847601134cc1fed2ea/pydantic_core-2.27.1-cp312-cp312-macosx_10_12_x86_64.whl", hash = "sha256:9cbd94fc661d2bab2bc702cddd2d3370bbdcc4cd0f8f57488a81bcce90c7a54f", size = 1895239 },
    { url = "https://files.pythonhosted.org/packages/7b/9e/f8063952e4a7d0127f5d1181addef9377505dcce3be224263b25c4f0bfd9/pydantic_core-2.27.1-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:5f8c4718cd44ec1580e180cb739713ecda2bdee1341084c1467802a417fe0f02", size = 1805070 },
    { url = "https://files.pythonhosted.org/packages/2c/9d/e1d6c4561d262b52e41b17a7ef8301e2ba80b61e32e94520271029feb5d8/pydantic_core-2.27.1-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:15aae984e46de8d376df515f00450d1522077254ef6b7ce189b38ecee7c9677c", size = 1828096 },
    { url = "https://files.pythonhosted.org/packages/be/65/80ff46de4266560baa4332ae3181fffc4488ea7d37282da1a62d10ab89a4/pydantic_core-2.27.1-cp312-cp312-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:1ba5e3963344ff25fc8c40da90f44b0afca8cfd89d12964feb79ac1411a260ac", size = 1857708 },
    { url = "https://files.pythonhosted.org/packages/d5/ca/3370074ad758b04d9562b12ecdb088597f4d9d13893a48a583fb47682cdf/pydantic_core-2.27.1-cp312-cp312-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:992cea5f4f3b29d6b4f7f1726ed8ee46c8331c6b4eed6db5b40134c6fe1768bb", size = 2037751 },
    { url = "https://files.pythonhosted.org/packages/b1/e2/4ab72d93367194317b99d051947c071aef6e3eb95f7553eaa4208ecf9ba4/pydantic_core-2.27.1-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:0325336f348dbee6550d129b1627cb8f5351a9dc91aad141ffb96d4937bd9529", size = 2733863 },
    { url = "https://files.pythonhosted.org/packages/8a/c6/8ae0831bf77f356bb73127ce5a95fe115b10f820ea480abbd72d3cc7ccf3/pydantic_core-2.27.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:7597c07fbd11515f654d6ece3d0e4e5093edc30a436c63142d9a4b8e22f19c35", size = 2161161 },
    { url = "https://files.pythonhosted.org/packages/f1/f4/b2fe73241da2429400fc27ddeaa43e35562f96cf5b67499b2de52b528cad/pydantic_core-2.27.1-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:3bbd5d8cc692616d5ef6fbbbd50dbec142c7e6ad9beb66b78a96e9c16729b089", size = 1993294 },
    { url = "https://files.pythonhosted.org/packages/77/29/4bb008823a7f4cc05828198153f9753b3bd4c104d93b8e0b1bfe4e187540/pydantic_core-2.27.1-cp312-cp312-musllinux_1_1_aarch64.whl", hash = "sha256:dc61505e73298a84a2f317255fcc72b710b72980f3a1f670447a21efc88f8381", size = 2001468 },
    { url = "https://files.pythonhosted.org/packages/f2/a9/0eaceeba41b9fad851a4107e0cf999a34ae8f0d0d1f829e2574f3d8897b0/pydantic_core-2.27.1-cp312-cp312-musllinux_1_1_armv7l.whl", hash = "sha256:e1f735dc43da318cad19b4173dd1ffce1d84aafd6c9b782b3abc04a0d5a6f5bb", size = 2091413 },
    { url = "https://files.pythonhosted.org/packages/d8/36/eb8697729725bc610fd73940f0d860d791dc2ad557faaefcbb3edbd2b349/pydantic_core-2.27.1-cp312-cp312-musllinux_1_1_x86_64.whl", hash = "sha256:f4e5658dbffe8843a0f12366a4c2d1c316dbe09bb4dfbdc9d2d9cd6031de8aae", size = 2154735 },
    { url = "https://files.pythonhosted.org/packages/52/e5/4f0fbd5c5995cc70d3afed1b5c754055bb67908f55b5cb8000f7112749bf/pydantic_core-2.27.1-cp312-none-win32.whl", hash = "sha256:672ebbe820bb37988c4d136eca2652ee114992d5d41c7e4858cdd90ea94ffe5c", size = 1833633 },
    { url = "https://files.pythonhosted.org/packages/ee/f2/c61486eee27cae5ac781305658779b4a6b45f9cc9d02c90cb21b940e82cc/pydantic_core-2.27.1-cp312-none-win_amd64.whl", hash = "sha256:66ff044fd0bb1768688aecbe28b6190f6e799349221fb0de0e6f4048eca14c16", size = 1986973 },
    { url = "https://files.pythonhosted.org/packages/df/a6/e3f12ff25f250b02f7c51be89a294689d175ac76e1096c32bf278f29ca1e/pydantic_core-2.27.1-cp312-none-win_arm64.whl", hash = "sha256:9a3b0793b1bbfd4146304e23d90045f2a9b5fd5823aa682665fbdaf2a6c28f3e", size = 1883215 },
    { url = "https://files.pythonhosted.org/packages/0f/d6/91cb99a3c59d7b072bded9959fbeab0a9613d5a4935773c0801f1764c156/pydantic_core-2.27.1-cp313-cp313-macosx_10_12_x86_64.whl", hash = "sha256:f216dbce0e60e4d03e0c4353c7023b202d95cbaeff12e5fd2e82ea0a66905073", size = 1895033 },
    { url = "https://files.pythonhosted.org/packages/07/42/d35033f81a28b27dedcade9e967e8a40981a765795c9ebae2045bcef05d3/pydantic_core-2.27.1-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:a2e02889071850bbfd36b56fd6bc98945e23670773bc7a76657e90e6b6603c08", size = 1807542 },
    { url = "https://files.pythonhosted.org/packages/41/c2/491b59e222ec7e72236e512108ecad532c7f4391a14e971c963f624f7569/pydantic_core-2.27.1-cp313-cp313-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:42b0e23f119b2b456d07ca91b307ae167cc3f6c846a7b169fca5326e32fdc6cf", size = 1827854 },
    { url = "https://files.pythonhosted.org/packages/e3/f3/363652651779113189cefdbbb619b7b07b7a67ebb6840325117cc8cc3460/pydantic_core-2.27.1-cp313-cp313-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:764be71193f87d460a03f1f7385a82e226639732214b402f9aa61f0d025f0737", size = 1857389 },
    { url = "https://files.pythonhosted.org/packages/5f/97/be804aed6b479af5a945daec7538d8bf358d668bdadde4c7888a2506bdfb/pydantic_core-2.27.1-cp313-cp313-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:1c00666a3bd2f84920a4e94434f5974d7bbc57e461318d6bb34ce9cdbbc1f6b2", size = 2037934 },
    { url = "https://files.pythonhosted.org/packages/42/01/295f0bd4abf58902917e342ddfe5f76cf66ffabfc57c2e23c7681a1a1197/pydantic_core-2.27.1-cp313-cp313-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:3ccaa88b24eebc0f849ce0a4d09e8a408ec5a94afff395eb69baf868f5183107", size = 2735176 },
    { url = "https://files.pythonhosted.org/packages/9d/a0/cd8e9c940ead89cc37812a1a9f310fef59ba2f0b22b4e417d84ab09fa970/pydantic_core-2.27.1-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:c65af9088ac534313e1963443d0ec360bb2b9cba6c2909478d22c2e363d98a51", size = 2160720 },
    { url = "https://files.pythonhosted.org/packages/73/ae/9d0980e286627e0aeca4c352a60bd760331622c12d576e5ea4441ac7e15e/pydantic_core-2.27.1-cp313-cp313-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:206b5cf6f0c513baffaeae7bd817717140770c74528f3e4c3e1cec7871ddd61a", size = 1992972 },
    { url = "https://files.pythonhosted.org/packages/bf/ba/ae4480bc0292d54b85cfb954e9d6bd226982949f8316338677d56541b85f/pydantic_core-2.27.1-cp313-cp313-musllinux_1_1_aarch64.whl", hash = "sha256:062f60e512fc7fff8b8a9d680ff0ddaaef0193dba9fa83e679c0c5f5fbd018bc", size = 2001477 },
    { url = "https://files.pythonhosted.org/packages/55/b7/e26adf48c2f943092ce54ae14c3c08d0d221ad34ce80b18a50de8ed2cba8/pydantic_core-2.27.1-cp313-cp313-musllinux_1_1_armv7l.whl", hash = "sha256:a0697803ed7d4af5e4c1adf1670af078f8fcab7a86350e969f454daf598c4960", size = 2091186 },
    { url = "https://files.pythonhosted.org/packages/ba/cc/8491fff5b608b3862eb36e7d29d36a1af1c945463ca4c5040bf46cc73f40/pydantic_core-2.27.1-cp313-cp313-musllinux_1_1_x86_64.whl", hash = "sha256:58ca98a950171f3151c603aeea9303ef6c235f692fe555e883591103da709b23", size = 2154429 },
    { url = "https://files.pythonhosted.org/packages/78/d8/c080592d80edd3441ab7f88f865f51dae94a157fc64283c680e9f32cf6da/pydantic_core-2.27.1-cp313-none-win32.whl", hash = "sha256:8065914ff79f7eab1599bd80406681f0ad08f8e47c880f17b416c9f8f7a26d05", size = 1833713 },
    { url = "https://files.pythonhosted.org/packages/83/84/5ab82a9ee2538ac95a66e51f6838d6aba6e0a03a42aa185ad2fe404a4e8f/pydantic_core-2.27.1-cp313-none-win_amd64.whl", hash = "sha256:ba630d5e3db74c79300d9a5bdaaf6200172b107f263c98a0539eeecb857b2337", size = 1987897 },
    { url = "https://files.pythonhosted.org/packages/df/c3/b15fb833926d91d982fde29c0624c9f225da743c7af801dace0d4e187e71/pydantic_core-2.27.1-cp313-none-win_arm64.whl", hash = "sha256:45cf8588c066860b623cd11c4ba687f8d7175d5f7ef65f7129df8a394c502de5", size = 1882983 },
    { url = "https://files.pythonhosted.org/packages/7c/60/e5eb2d462595ba1f622edbe7b1d19531e510c05c405f0b87c80c1e89d5b1/pydantic_core-2.27.1-pp310-pypy310_pp73-macosx_10_12_x86_64.whl", hash = "sha256:3fa80ac2bd5856580e242dbc202db873c60a01b20309c8319b5c5986fbe53ce6", size = 1894016 },
    { url = "https://files.pythonhosted.org/packages/61/20/da7059855225038c1c4326a840908cc7ca72c7198cb6addb8b92ec81c1d6/pydantic_core-2.27.1-pp310-pypy310_pp73-macosx_11_0_arm64.whl", hash = "sha256:d950caa237bb1954f1b8c9227b5065ba6875ac9771bb8ec790d956a699b78676", size = 1771648 },
    { url = "https://files.pythonhosted.org/packages/8f/fc/5485cf0b0bb38da31d1d292160a4d123b5977841ddc1122c671a30b76cfd/pydantic_core-2.27.1-pp310-pypy310_pp73-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:0e4216e64d203e39c62df627aa882f02a2438d18a5f21d7f721621f7a5d3611d", size = 1826929 },
    { url = "https://files.pythonhosted.org/packages/a1/ff/fb1284a210e13a5f34c639efc54d51da136074ffbe25ec0c279cf9fbb1c4/pydantic_core-2.27.1-pp310-pypy310_pp73-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:02a3d637bd387c41d46b002f0e49c52642281edacd2740e5a42f7017feea3f2c", size = 1980591 },
    { url = "https://files.pythonhosted.org/packages/f1/14/77c1887a182d05af74f6aeac7b740da3a74155d3093ccc7ee10b900cc6b5/pydantic_core-2.27.1-pp310-pypy310_pp73-manylinux_2_5_i686.manylinux1_i686.whl", hash = "sha256:161c27ccce13b6b0c8689418da3885d3220ed2eae2ea5e9b2f7f3d48f1d52c27", size = 1981326 },
    { url = "https://files.pythonhosted.org/packages/06/aa/6f1b2747f811a9c66b5ef39d7f02fbb200479784c75e98290d70004b1253/pydantic_core-2.27.1-pp310-pypy310_pp73-musllinux_1_1_aarch64.whl", hash = "sha256:19910754e4cc9c63bc1c7f6d73aa1cfee82f42007e407c0f413695c2f7ed777f", size = 1989205 },
    { url = "https://files.pythonhosted.org/packages/7a/d2/8ce2b074d6835f3c88d85f6d8a399790043e9fdb3d0e43455e72d19df8cc/pydantic_core-2.27.1-pp310-pypy310_pp73-musllinux_1_1_armv7l.whl", hash = "sha256:e173486019cc283dc9778315fa29a363579372fe67045e971e89b6365cc035ed", size = 2079616 },
    { url = "https://files.pythonhosted.org/packages/65/71/af01033d4e58484c3db1e5d13e751ba5e3d6b87cc3368533df4c50932c8b/pydantic_core-2.27.1-pp310-pypy310_pp73-musllinux_1_1_x86_64.whl", hash = "sha256:af52d26579b308921b73b956153066481f064875140ccd1dfd4e77db89dbb12f", size = 2133265 },
    { url = "https://files.pythonhosted.org/packages/33/72/f881b5e18fbb67cf2fb4ab253660de3c6899dbb2dba409d0b757e3559e3d/pydantic_core-2.27.1-pp310-pypy310_pp73-win_amd64.whl", hash = "sha256:981fb88516bd1ae8b0cbbd2034678a39dedc98752f264ac9bc5839d3923fa04c", size = 2001864 },
]

[[package]]
name = "pydantic-settings"
version = "2.6.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "pydantic" },
    { name = "python-dotenv" },
]
sdist = { url = "https://files.pythonhosted.org/packages/b5/d4/9dfbe238f45ad8b168f5c96ee49a3df0598ce18a0795a983b419949ce65b/pydantic_settings-2.6.1.tar.gz", hash = "sha256:e0f92546d8a9923cb8941689abf85d6601a8c19a23e97a34b2964a2e3f813ca0", size = 75646 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/5e/f9/ff95fd7d760af42f647ea87f9b8a383d891cdb5e5dbd4613edaeb094252a/pydantic_settings-2.6.1-py3-none-any.whl", hash = "sha256:7fb0637c786a558d3103436278a7c4f1cfd29ba8973238a50c5bb9a55387da87", size = 28595 },
]

[[package]]
name = "pygments"
version = "2.18.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/8e/62/8336eff65bcbc8e4cb5d05b55faf041285951b6e80f33e2bff2024788f31/pygments-2.18.0.tar.gz", hash = "sha256:786ff802f32e91311bff3889f6e9a86e81505fe99f2735bb6d60ae0c5004f199", size = 4891905 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/f7/3f/01c8b82017c199075f8f788d0d906b9ffbbc5a47dc9918a945e13d5a2bda/pygments-2.18.0-py3-none-any.whl", hash = "sha256:b8e6aca0523f3ab76fee51799c488e38782ac06eafcf95e7ba832985c8e7b13a", size = 1205513 },
]

[[package]]
name = "pyperclip"
version = "1.9.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/30/23/2f0a3efc4d6a32f3b63cdff36cd398d9701d26cda58e3ab97ac79fb5e60d/pyperclip-1.9.0.tar.gz", hash = "sha256:b7de0142ddc81bfc5c7507eea19da920b92252b548b96186caf94a5e2527d310", size = 20961 }

[[package]]
name = "pyreadline"
version = "2.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/bc/7c/d724ef1ec3ab2125f38a1d53285745445ec4a8f19b9bb0761b4064316679/pyreadline-2.1.zip", hash = "sha256:4530592fc2e85b25b1a9f79664433da09237c1a270e4d78ea5aa3a2c7229e2d1", size = 109189 }

[[package]]
name = "pyrepl"
version = "0.9.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/05/1b/ea40363be0056080454cdbabe880773c3c5bd66d7b13f0c8b8b8c8da1e0c/pyrepl-0.9.0.tar.gz", hash = "sha256:292570f34b5502e871bbb966d639474f2b57fbfcd3373c2d6a2f3d56e681a775", size = 48744 }

[[package]]
name = "pyright"
version = "1.1.389"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "nodeenv" },
    { name = "typing-extensions" },
]
sdist = { url = "https://files.pythonhosted.org/packages/72/4e/9a5ab8745e7606b88c2c7ca223449ac9d82a71fd5e31df47b453f2cb39a1/pyright-1.1.389.tar.gz", hash = "sha256:716bf8cc174ab8b4dcf6828c3298cac05c5ed775dda9910106a5dcfe4c7fe220", size = 21940 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/1b/26/c288cabf8cfc5a27e1aa9e5029b7682c0f920b8074f45d22bf844314d66a/pyright-1.1.389-py3-none-any.whl", hash = "sha256:41e9620bba9254406dc1f621a88ceab5a88af4c826feb4f614d95691ed243a60", size = 18581 },
]

[[package]]
name = "pytest"
version = "8.3.3"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "colorama", marker = "sys_platform == 'win32'" },
    { name = "exceptiongroup", marker = "python_full_version < '3.11'" },
    { name = "iniconfig" },
    { name = "packaging" },
    { name = "pluggy" },
    { name = "tomli", marker = "python_full_version < '3.11'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/8b/6c/62bbd536103af674e227c41a8f3dcd022d591f6eed5facb5a0f31ee33bbc/pytest-8.3.3.tar.gz", hash = "sha256:70b98107bd648308a7952b06e6ca9a50bc660be218d53c257cc1fc94fda10181", size = 1442487 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/6b/77/7440a06a8ead44c7757a64362dd22df5760f9b12dc5f11b6188cd2fc27a0/pytest-8.3.3-py3-none-any.whl", hash = "sha256:a6853c7375b2663155079443d2e45de913a911a11d669df02a50814944db57b2", size = 342341 },
]

[[package]]
name = "pytest-asyncio"
version = "0.24.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "pytest" },
]
sdist = { url = "https://files.pythonhosted.org/packages/52/6d/c6cf50ce320cf8611df7a1254d86233b3df7cc07f9b5f5cbcb82e08aa534/pytest_asyncio-0.24.0.tar.gz", hash = "sha256:d081d828e576d85f875399194281e92bf8a68d60d72d1a2faf2feddb6c46b276", size = 49855 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/96/31/6607dab48616902f76885dfcf62c08d929796fc3b2d2318faf9fd54dbed9/pytest_asyncio-0.24.0-py3-none-any.whl", hash = "sha256:a811296ed596b69bf0b6f3dc40f83bcaf341b155a269052d82efa2b25ac7037b", size = 18024 },
]

[[package]]
name = "pytest-flakefinder"
version = "1.1.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "pytest" },
]
sdist = { url = "https://files.pythonhosted.org/packages/ec/53/69c56a93ea057895b5761c5318455804873a6cd9d796d7c55d41c2358125/pytest-flakefinder-1.1.0.tar.gz", hash = "sha256:e2412a1920bdb8e7908783b20b3d57e9dad590cc39a93e8596ffdd493b403e0e", size = 6795 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/33/8b/06787150d0fd0cbd3a8054262b56f91631c7778c1bc91bf4637e47f909ad/pytest_flakefinder-1.1.0-py2.py3-none-any.whl", hash = "sha256:741e0e8eea427052f5b8c89c2b3c3019a50c39a59ce4df6a305a2c2d9ba2bd13", size = 4644 },
]

[[package]]
name = "pytest-xdist"
version = "3.6.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "execnet" },
    { name = "pytest" },
]
sdist = { url = "https://files.pythonhosted.org/packages/41/c4/3c310a19bc1f1e9ef50075582652673ef2bfc8cd62afef9585683821902f/pytest_xdist-3.6.1.tar.gz", hash = "sha256:ead156a4db231eec769737f57668ef58a2084a34b2e55c4a8fa20d861107300d", size = 84060 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/6d/82/1d96bf03ee4c0fdc3c0cbe61470070e659ca78dc0086fb88b66c185e2449/pytest_xdist-3.6.1-py3-none-any.whl", hash = "sha256:9ed4adfb68a016610848639bb7e02c9352d5d9f03d04809919e2dafc3be4cca7", size = 46108 },
]

[[package]]
name = "python-dotenv"
version = "1.0.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/bc/57/e84d88dfe0aec03b7a2d4327012c1627ab5f03652216c63d49846d7a6c58/python-dotenv-1.0.1.tar.gz", hash = "sha256:e324ee90a023d808f1959c46bcbc04446a10ced277783dc6ee09987c37ec10ca", size = 39115 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/6a/3e/b68c118422ec867fa7ab88444e1274aa40681c606d59ac27de5a5588f082/python_dotenv-1.0.1-py3-none-any.whl", hash = "sha256:f7b63ef50f1b690dddf550d03497b66d609393b40b564ed0d674909a68ebf16a", size = 19863 },
]

[[package]]
name = "pyyaml"
version = "6.0.2"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/54/ed/79a089b6be93607fa5cdaedf301d7dfb23af5f25c398d5ead2525b063e17/pyyaml-6.0.2.tar.gz", hash = "sha256:d584d9ec91ad65861cc08d42e834324ef890a082e591037abe114850ff7bbc3e", size = 130631 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/9b/95/a3fac87cb7158e231b5a6012e438c647e1a87f09f8e0d123acec8ab8bf71/PyYAML-6.0.2-cp310-cp310-macosx_10_9_x86_64.whl", hash = "sha256:0a9a2848a5b7feac301353437eb7d5957887edbf81d56e903999a75a3d743086", size = 184199 },
    { url = "https://files.pythonhosted.org/packages/c7/7a/68bd47624dab8fd4afbfd3c48e3b79efe09098ae941de5b58abcbadff5cb/PyYAML-6.0.2-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:29717114e51c84ddfba879543fb232a6ed60086602313ca38cce623c1d62cfbf", size = 171758 },
    { url = "https://files.pythonhosted.org/packages/49/ee/14c54df452143b9ee9f0f29074d7ca5516a36edb0b4cc40c3f280131656f/PyYAML-6.0.2-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:8824b5a04a04a047e72eea5cec3bc266db09e35de6bdfe34c9436ac5ee27d237", size = 718463 },
    { url = "https://files.pythonhosted.org/packages/4d/61/de363a97476e766574650d742205be468921a7b532aa2499fcd886b62530/PyYAML-6.0.2-cp310-cp310-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:7c36280e6fb8385e520936c3cb3b8042851904eba0e58d277dca80a5cfed590b", size = 719280 },
    { url = "https://files.pythonhosted.org/packages/6b/4e/1523cb902fd98355e2e9ea5e5eb237cbc5f3ad5f3075fa65087aa0ecb669/PyYAML-6.0.2-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:ec031d5d2feb36d1d1a24380e4db6d43695f3748343d99434e6f5f9156aaa2ed", size = 751239 },
    { url = "https://files.pythonhosted.org/packages/b7/33/5504b3a9a4464893c32f118a9cc045190a91637b119a9c881da1cf6b7a72/PyYAML-6.0.2-cp310-cp310-musllinux_1_1_aarch64.whl", hash = "sha256:936d68689298c36b53b29f23c6dbb74de12b4ac12ca6cfe0e047bedceea56180", size = 695802 },
    { url = "https://files.pythonhosted.org/packages/5c/20/8347dcabd41ef3a3cdc4f7b7a2aff3d06598c8779faa189cdbf878b626a4/PyYAML-6.0.2-cp310-cp310-musllinux_1_1_x86_64.whl", hash = "sha256:23502f431948090f597378482b4812b0caae32c22213aecf3b55325e049a6c68", size = 720527 },
    { url = "https://files.pythonhosted.org/packages/be/aa/5afe99233fb360d0ff37377145a949ae258aaab831bde4792b32650a4378/PyYAML-6.0.2-cp310-cp310-win32.whl", hash = "sha256:2e99c6826ffa974fe6e27cdb5ed0021786b03fc98e5ee3c5bfe1fd5015f42b99", size = 144052 },
    { url = "https://files.pythonhosted.org/packages/b5/84/0fa4b06f6d6c958d207620fc60005e241ecedceee58931bb20138e1e5776/PyYAML-6.0.2-cp310-cp310-win_amd64.whl", hash = "sha256:a4d3091415f010369ae4ed1fc6b79def9416358877534caf6a0fdd2146c87a3e", size = 161774 },
    { url = "https://files.pythonhosted.org/packages/f8/aa/7af4e81f7acba21a4c6be026da38fd2b872ca46226673c89a758ebdc4fd2/PyYAML-6.0.2-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:cc1c1159b3d456576af7a3e4d1ba7e6924cb39de8f67111c735f6fc832082774", size = 184612 },
    { url = "https://files.pythonhosted.org/packages/8b/62/b9faa998fd185f65c1371643678e4d58254add437edb764a08c5a98fb986/PyYAML-6.0.2-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:1e2120ef853f59c7419231f3bf4e7021f1b936f6ebd222406c3b60212205d2ee", size = 172040 },
    { url = "https://files.pythonhosted.org/packages/ad/0c/c804f5f922a9a6563bab712d8dcc70251e8af811fce4524d57c2c0fd49a4/PyYAML-6.0.2-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:5d225db5a45f21e78dd9358e58a98702a0302f2659a3c6cd320564b75b86f47c", size = 736829 },
    { url = "https://files.pythonhosted.org/packages/51/16/6af8d6a6b210c8e54f1406a6b9481febf9c64a3109c541567e35a49aa2e7/PyYAML-6.0.2-cp311-cp311-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:5ac9328ec4831237bec75defaf839f7d4564be1e6b25ac710bd1a96321cc8317", size = 764167 },
    { url = "https://files.pythonhosted.org/packages/75/e4/2c27590dfc9992f73aabbeb9241ae20220bd9452df27483b6e56d3975cc5/PyYAML-6.0.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:3ad2a3decf9aaba3d29c8f537ac4b243e36bef957511b4766cb0057d32b0be85", size = 762952 },
    { url = "https://files.pythonhosted.org/packages/9b/97/ecc1abf4a823f5ac61941a9c00fe501b02ac3ab0e373c3857f7d4b83e2b6/PyYAML-6.0.2-cp311-cp311-musllinux_1_1_aarch64.whl", hash = "sha256:ff3824dc5261f50c9b0dfb3be22b4567a6f938ccce4587b38952d85fd9e9afe4", size = 735301 },
    { url = "https://files.pythonhosted.org/packages/45/73/0f49dacd6e82c9430e46f4a027baa4ca205e8b0a9dce1397f44edc23559d/PyYAML-6.0.2-cp311-cp311-musllinux_1_1_x86_64.whl", hash = "sha256:797b4f722ffa07cc8d62053e4cff1486fa6dc094105d13fea7b1de7d8bf71c9e", size = 756638 },
    { url = "https://files.pythonhosted.org/packages/22/5f/956f0f9fc65223a58fbc14459bf34b4cc48dec52e00535c79b8db361aabd/PyYAML-6.0.2-cp311-cp311-win32.whl", hash = "sha256:11d8f3dd2b9c1207dcaf2ee0bbbfd5991f571186ec9cc78427ba5bd32afae4b5", size = 143850 },
    { url = "https://files.pythonhosted.org/packages/ed/23/8da0bbe2ab9dcdd11f4f4557ccaf95c10b9811b13ecced089d43ce59c3c8/PyYAML-6.0.2-cp311-cp311-win_amd64.whl", hash = "sha256:e10ce637b18caea04431ce14fabcf5c64a1c61ec9c56b071a4b7ca131ca52d44", size = 161980 },
    { url = "https://files.pythonhosted.org/packages/86/0c/c581167fc46d6d6d7ddcfb8c843a4de25bdd27e4466938109ca68492292c/PyYAML-6.0.2-cp312-cp312-macosx_10_9_x86_64.whl", hash = "sha256:c70c95198c015b85feafc136515252a261a84561b7b1d51e3384e0655ddf25ab", size = 183873 },
    { url = "https://files.pythonhosted.org/packages/a8/0c/38374f5bb272c051e2a69281d71cba6fdb983413e6758b84482905e29a5d/PyYAML-6.0.2-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:ce826d6ef20b1bc864f0a68340c8b3287705cae2f8b4b1d932177dcc76721725", size = 173302 },
    { url = "https://files.pythonhosted.org/packages/c3/93/9916574aa8c00aa06bbac729972eb1071d002b8e158bd0e83a3b9a20a1f7/PyYAML-6.0.2-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:1f71ea527786de97d1a0cc0eacd1defc0985dcf6b3f17bb77dcfc8c34bec4dc5", size = 739154 },
    { url = "https://files.pythonhosted.org/packages/95/0f/b8938f1cbd09739c6da569d172531567dbcc9789e0029aa070856f123984/PyYAML-6.0.2-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:9b22676e8097e9e22e36d6b7bda33190d0d400f345f23d4065d48f4ca7ae0425", size = 766223 },
    { url = "https://files.pythonhosted.org/packages/b9/2b/614b4752f2e127db5cc206abc23a8c19678e92b23c3db30fc86ab731d3bd/PyYAML-6.0.2-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:80bab7bfc629882493af4aa31a4cfa43a4c57c83813253626916b8c7ada83476", size = 767542 },
    { url = "https://files.pythonhosted.org/packages/d4/00/dd137d5bcc7efea1836d6264f049359861cf548469d18da90cd8216cf05f/PyYAML-6.0.2-cp312-cp312-musllinux_1_1_aarch64.whl", hash = "sha256:0833f8694549e586547b576dcfaba4a6b55b9e96098b36cdc7ebefe667dfed48", size = 731164 },
    { url = "https://files.pythonhosted.org/packages/c9/1f/4f998c900485e5c0ef43838363ba4a9723ac0ad73a9dc42068b12aaba4e4/PyYAML-6.0.2-cp312-cp312-musllinux_1_1_x86_64.whl", hash = "sha256:8b9c7197f7cb2738065c481a0461e50ad02f18c78cd75775628afb4d7137fb3b", size = 756611 },
    { url = "https://files.pythonhosted.org/packages/df/d1/f5a275fdb252768b7a11ec63585bc38d0e87c9e05668a139fea92b80634c/PyYAML-6.0.2-cp312-cp312-win32.whl", hash = "sha256:ef6107725bd54b262d6dedcc2af448a266975032bc85ef0172c5f059da6325b4", size = 140591 },
    { url = "https://files.pythonhosted.org/packages/0c/e8/4f648c598b17c3d06e8753d7d13d57542b30d56e6c2dedf9c331ae56312e/PyYAML-6.0.2-cp312-cp312-win_amd64.whl", hash = "sha256:7e7401d0de89a9a855c839bc697c079a4af81cf878373abd7dc625847d25cbd8", size = 156338 },
    { url = "https://files.pythonhosted.org/packages/ef/e3/3af305b830494fa85d95f6d95ef7fa73f2ee1cc8ef5b495c7c3269fb835f/PyYAML-6.0.2-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:efdca5630322a10774e8e98e1af481aad470dd62c3170801852d752aa7a783ba", size = 181309 },
    { url = "https://files.pythonhosted.org/packages/45/9f/3b1c20a0b7a3200524eb0076cc027a970d320bd3a6592873c85c92a08731/PyYAML-6.0.2-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:50187695423ffe49e2deacb8cd10510bc361faac997de9efef88badc3bb9e2d1", size = 171679 },
    { url = "https://files.pythonhosted.org/packages/7c/9a/337322f27005c33bcb656c655fa78325b730324c78620e8328ae28b64d0c/PyYAML-6.0.2-cp313-cp313-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:0ffe8360bab4910ef1b9e87fb812d8bc0a308b0d0eef8c8f44e0254ab3b07133", size = 733428 },
    { url = "https://files.pythonhosted.org/packages/a3/69/864fbe19e6c18ea3cc196cbe5d392175b4cf3d5d0ac1403ec3f2d237ebb5/PyYAML-6.0.2-cp313-cp313-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:17e311b6c678207928d649faa7cb0d7b4c26a0ba73d41e99c4fff6b6c3276484", size = 763361 },
    { url = "https://files.pythonhosted.org/packages/04/24/b7721e4845c2f162d26f50521b825fb061bc0a5afcf9a386840f23ea19fa/PyYAML-6.0.2-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:70b189594dbe54f75ab3a1acec5f1e3faa7e8cf2f1e08d9b561cb41b845f69d5", size = 759523 },
    { url = "https://files.pythonhosted.org/packages/2b/b2/e3234f59ba06559c6ff63c4e10baea10e5e7df868092bf9ab40e5b9c56b6/PyYAML-6.0.2-cp313-cp313-musllinux_1_1_aarch64.whl", hash = "sha256:41e4e3953a79407c794916fa277a82531dd93aad34e29c2a514c2c0c5fe971cc", size = 726660 },
    { url = "https://files.pythonhosted.org/packages/fe/0f/25911a9f080464c59fab9027482f822b86bf0608957a5fcc6eaac85aa515/PyYAML-6.0.2-cp313-cp313-musllinux_1_1_x86_64.whl", hash = "sha256:68ccc6023a3400877818152ad9a1033e3db8625d899c72eacb5a668902e4d652", size = 751597 },
    { url = "https://files.pythonhosted.org/packages/14/0d/e2c3b43bbce3cf6bd97c840b46088a3031085179e596d4929729d8d68270/PyYAML-6.0.2-cp313-cp313-win32.whl", hash = "sha256:bc2fa7c6b47d6bc618dd7fb02ef6fdedb1090ec036abab80d4681424b84c1183", size = 140527 },
    { url = "https://files.pythonhosted.org/packages/fa/de/02b54f42487e3d3c6efb3f89428677074ca7bf43aae402517bc7cca949f3/PyYAML-6.0.2-cp313-cp313-win_amd64.whl", hash = "sha256:8388ee1976c416731879ac16da0aff3f63b286ffdd57cdeb95f3f2e085687563", size = 156446 },
]

[[package]]
name = "regex"
version = "2024.11.6"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/8e/5f/bd69653fbfb76cf8604468d3b4ec4c403197144c7bfe0e6a5fc9e02a07cb/regex-2024.11.6.tar.gz", hash = "sha256:7ab159b063c52a0333c884e4679f8d7a85112ee3078fe3d9004b2dd875585519", size = 399494 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/95/3c/4651f6b130c6842a8f3df82461a8950f923925db8b6961063e82744bddcc/regex-2024.11.6-cp310-cp310-macosx_10_9_universal2.whl", hash = "sha256:ff590880083d60acc0433f9c3f713c51f7ac6ebb9adf889c79a261ecf541aa91", size = 482674 },
    { url = "https://files.pythonhosted.org/packages/15/51/9f35d12da8434b489c7b7bffc205c474a0a9432a889457026e9bc06a297a/regex-2024.11.6-cp310-cp310-macosx_10_9_x86_64.whl", hash = "sha256:658f90550f38270639e83ce492f27d2c8d2cd63805c65a13a14d36ca126753f0", size = 287684 },
    { url = "https://files.pythonhosted.org/packages/bd/18/b731f5510d1b8fb63c6b6d3484bfa9a59b84cc578ac8b5172970e05ae07c/regex-2024.11.6-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:164d8b7b3b4bcb2068b97428060b2a53be050085ef94eca7f240e7947f1b080e", size = 284589 },
    { url = "https://files.pythonhosted.org/packages/78/a2/6dd36e16341ab95e4c6073426561b9bfdeb1a9c9b63ab1b579c2e96cb105/regex-2024.11.6-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:d3660c82f209655a06b587d55e723f0b813d3a7db2e32e5e7dc64ac2a9e86fde", size = 782511 },
    { url = "https://files.pythonhosted.org/packages/1b/2b/323e72d5d2fd8de0d9baa443e1ed70363ed7e7b2fb526f5950c5cb99c364/regex-2024.11.6-cp310-cp310-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:d22326fcdef5e08c154280b71163ced384b428343ae16a5ab2b3354aed12436e", size = 821149 },
    { url = "https://files.pythonhosted.org/packages/90/30/63373b9ea468fbef8a907fd273e5c329b8c9535fee36fc8dba5fecac475d/regex-2024.11.6-cp310-cp310-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:f1ac758ef6aebfc8943560194e9fd0fa18bcb34d89fd8bd2af18183afd8da3a2", size = 809707 },
    { url = "https://files.pythonhosted.org/packages/f2/98/26d3830875b53071f1f0ae6d547f1d98e964dd29ad35cbf94439120bb67a/regex-2024.11.6-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:997d6a487ff00807ba810e0f8332c18b4eb8d29463cfb7c820dc4b6e7562d0cf", size = 781702 },
    { url = "https://files.pythonhosted.org/packages/87/55/eb2a068334274db86208ab9d5599ffa63631b9f0f67ed70ea7c82a69bbc8/regex-2024.11.6-cp310-cp310-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:02a02d2bb04fec86ad61f3ea7f49c015a0681bf76abb9857f945d26159d2968c", size = 771976 },
    { url = "https://files.pythonhosted.org/packages/74/c0/be707bcfe98254d8f9d2cff55d216e946f4ea48ad2fd8cf1428f8c5332ba/regex-2024.11.6-cp310-cp310-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_12_x86_64.manylinux2010_x86_64.whl", hash = "sha256:f02f93b92358ee3f78660e43b4b0091229260c5d5c408d17d60bf26b6c900e86", size = 697397 },
    { url = "https://files.pythonhosted.org/packages/49/dc/bb45572ceb49e0f6509f7596e4ba7031f6819ecb26bc7610979af5a77f45/regex-2024.11.6-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:06eb1be98df10e81ebaded73fcd51989dcf534e3c753466e4b60c4697a003b67", size = 768726 },
    { url = "https://files.pythonhosted.org/packages/5a/db/f43fd75dc4c0c2d96d0881967897926942e935d700863666f3c844a72ce6/regex-2024.11.6-cp310-cp310-musllinux_1_2_i686.whl", hash = "sha256:040df6fe1a5504eb0f04f048e6d09cd7c7110fef851d7c567a6b6e09942feb7d", size = 775098 },
    { url = "https://files.pythonhosted.org/packages/99/d7/f94154db29ab5a89d69ff893159b19ada89e76b915c1293e98603d39838c/regex-2024.11.6-cp310-cp310-musllinux_1_2_ppc64le.whl", hash = "sha256:fdabbfc59f2c6edba2a6622c647b716e34e8e3867e0ab975412c5c2f79b82da2", size = 839325 },
    { url = "https://files.pythonhosted.org/packages/f7/17/3cbfab1f23356fbbf07708220ab438a7efa1e0f34195bf857433f79f1788/regex-2024.11.6-cp310-cp310-musllinux_1_2_s390x.whl", hash = "sha256:8447d2d39b5abe381419319f942de20b7ecd60ce86f16a23b0698f22e1b70008", size = 843277 },
    { url = "https://files.pythonhosted.org/packages/7e/f2/48b393b51900456155de3ad001900f94298965e1cad1c772b87f9cfea011/regex-2024.11.6-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:da8f5fc57d1933de22a9e23eec290a0d8a5927a5370d24bda9a6abe50683fe62", size = 773197 },
    { url = "https://files.pythonhosted.org/packages/45/3f/ef9589aba93e084cd3f8471fded352826dcae8489b650d0b9b27bc5bba8a/regex-2024.11.6-cp310-cp310-win32.whl", hash = "sha256:b489578720afb782f6ccf2840920f3a32e31ba28a4b162e13900c3e6bd3f930e", size = 261714 },
    { url = "https://files.pythonhosted.org/packages/42/7e/5f1b92c8468290c465fd50c5318da64319133231415a8aa6ea5ab995a815/regex-2024.11.6-cp310-cp310-win_amd64.whl", hash = "sha256:5071b2093e793357c9d8b2929dfc13ac5f0a6c650559503bb81189d0a3814519", size = 274042 },
    { url = "https://files.pythonhosted.org/packages/58/58/7e4d9493a66c88a7da6d205768119f51af0f684fe7be7bac8328e217a52c/regex-2024.11.6-cp311-cp311-macosx_10_9_universal2.whl", hash = "sha256:5478c6962ad548b54a591778e93cd7c456a7a29f8eca9c49e4f9a806dcc5d638", size = 482669 },
    { url = "https://files.pythonhosted.org/packages/34/4c/8f8e631fcdc2ff978609eaeef1d6994bf2f028b59d9ac67640ed051f1218/regex-2024.11.6-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:2c89a8cc122b25ce6945f0423dc1352cb9593c68abd19223eebbd4e56612c5b7", size = 287684 },
    { url = "https://files.pythonhosted.org/packages/c5/1b/f0e4d13e6adf866ce9b069e191f303a30ab1277e037037a365c3aad5cc9c/regex-2024.11.6-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:94d87b689cdd831934fa3ce16cc15cd65748e6d689f5d2b8f4f4df2065c9fa20", size = 284589 },
    { url = "https://files.pythonhosted.org/packages/25/4d/ab21047f446693887f25510887e6820b93f791992994f6498b0318904d4a/regex-2024.11.6-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:1062b39a0a2b75a9c694f7a08e7183a80c63c0d62b301418ffd9c35f55aaa114", size = 792121 },
    { url = "https://files.pythonhosted.org/packages/45/ee/c867e15cd894985cb32b731d89576c41a4642a57850c162490ea34b78c3b/regex-2024.11.6-cp311-cp311-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:167ed4852351d8a750da48712c3930b031f6efdaa0f22fa1933716bfcd6bf4a3", size = 831275 },
    { url = "https://files.pythonhosted.org/packages/b3/12/b0f480726cf1c60f6536fa5e1c95275a77624f3ac8fdccf79e6727499e28/regex-2024.11.6-cp311-cp311-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:2d548dafee61f06ebdb584080621f3e0c23fff312f0de1afc776e2a2ba99a74f", size = 818257 },
    { url = "https://files.pythonhosted.org/packages/bf/ce/0d0e61429f603bac433910d99ef1a02ce45a8967ffbe3cbee48599e62d88/regex-2024.11.6-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:f2a19f302cd1ce5dd01a9099aaa19cae6173306d1302a43b627f62e21cf18ac0", size = 792727 },
    { url = "https://files.pythonhosted.org/packages/e4/c1/243c83c53d4a419c1556f43777ccb552bccdf79d08fda3980e4e77dd9137/regex-2024.11.6-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:bec9931dfb61ddd8ef2ebc05646293812cb6b16b60cf7c9511a832b6f1854b55", size = 780667 },
    { url = "https://files.pythonhosted.org/packages/c5/f4/75eb0dd4ce4b37f04928987f1d22547ddaf6c4bae697623c1b05da67a8aa/regex-2024.11.6-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:9714398225f299aa85267fd222f7142fcb5c769e73d7733344efc46f2ef5cf89", size = 776963 },
    { url = "https://files.pythonhosted.org/packages/16/5d/95c568574e630e141a69ff8a254c2f188b4398e813c40d49228c9bbd9875/regex-2024.11.6-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:202eb32e89f60fc147a41e55cb086db2a3f8cb82f9a9a88440dcfc5d37faae8d", size = 784700 },
    { url = "https://files.pythonhosted.org/packages/8e/b5/f8495c7917f15cc6fee1e7f395e324ec3e00ab3c665a7dc9d27562fd5290/regex-2024.11.6-cp311-cp311-musllinux_1_2_ppc64le.whl", hash = "sha256:4181b814e56078e9b00427ca358ec44333765f5ca1b45597ec7446d3a1ef6e34", size = 848592 },
    { url = "https://files.pythonhosted.org/packages/1c/80/6dd7118e8cb212c3c60b191b932dc57db93fb2e36fb9e0e92f72a5909af9/regex-2024.11.6-cp311-cp311-musllinux_1_2_s390x.whl", hash = "sha256:068376da5a7e4da51968ce4c122a7cd31afaaec4fccc7856c92f63876e57b51d", size = 852929 },
    { url = "https://files.pythonhosted.org/packages/11/9b/5a05d2040297d2d254baf95eeeb6df83554e5e1df03bc1a6687fc4ba1f66/regex-2024.11.6-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:ac10f2c4184420d881a3475fb2c6f4d95d53a8d50209a2500723d831036f7c45", size = 781213 },
    { url = "https://files.pythonhosted.org/packages/26/b7/b14e2440156ab39e0177506c08c18accaf2b8932e39fb092074de733d868/regex-2024.11.6-cp311-cp311-win32.whl", hash = "sha256:c36f9b6f5f8649bb251a5f3f66564438977b7ef8386a52460ae77e6070d309d9", size = 261734 },
    { url = "https://files.pythonhosted.org/packages/80/32/763a6cc01d21fb3819227a1cc3f60fd251c13c37c27a73b8ff4315433a8e/regex-2024.11.6-cp311-cp311-win_amd64.whl", hash = "sha256:02e28184be537f0e75c1f9b2f8847dc51e08e6e171c6bde130b2687e0c33cf60", size = 274052 },
    { url = "https://files.pythonhosted.org/packages/ba/30/9a87ce8336b172cc232a0db89a3af97929d06c11ceaa19d97d84fa90a8f8/regex-2024.11.6-cp312-cp312-macosx_10_13_universal2.whl", hash = "sha256:52fb28f528778f184f870b7cf8f225f5eef0a8f6e3778529bdd40c7b3920796a", size = 483781 },
    { url = "https://files.pythonhosted.org/packages/01/e8/00008ad4ff4be8b1844786ba6636035f7ef926db5686e4c0f98093612add/regex-2024.11.6-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:fdd6028445d2460f33136c55eeb1f601ab06d74cb3347132e1c24250187500d9", size = 288455 },
    { url = "https://files.pythonhosted.org/packages/60/85/cebcc0aff603ea0a201667b203f13ba75d9fc8668fab917ac5b2de3967bc/regex-2024.11.6-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:805e6b60c54bf766b251e94526ebad60b7de0c70f70a4e6210ee2891acb70bf2", size = 284759 },
    { url = "https://files.pythonhosted.org/packages/94/2b/701a4b0585cb05472a4da28ee28fdfe155f3638f5e1ec92306d924e5faf0/regex-2024.11.6-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:b85c2530be953a890eaffde05485238f07029600e8f098cdf1848d414a8b45e4", size = 794976 },
    { url = "https://files.pythonhosted.org/packages/4b/bf/fa87e563bf5fee75db8915f7352e1887b1249126a1be4813837f5dbec965/regex-2024.11.6-cp312-cp312-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:bb26437975da7dc36b7efad18aa9dd4ea569d2357ae6b783bf1118dabd9ea577", size = 833077 },
    { url = "https://files.pythonhosted.org/packages/a1/56/7295e6bad94b047f4d0834e4779491b81216583c00c288252ef625c01d23/regex-2024.11.6-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:abfa5080c374a76a251ba60683242bc17eeb2c9818d0d30117b4486be10c59d3", size = 823160 },
    { url = "https://files.pythonhosted.org/packages/fb/13/e3b075031a738c9598c51cfbc4c7879e26729c53aa9cca59211c44235314/regex-2024.11.6-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:70b7fa6606c2881c1db9479b0eaa11ed5dfa11c8d60a474ff0e095099f39d98e", size = 796896 },
    { url = "https://files.pythonhosted.org/packages/24/56/0b3f1b66d592be6efec23a795b37732682520b47c53da5a32c33ed7d84e3/regex-2024.11.6-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:0c32f75920cf99fe6b6c539c399a4a128452eaf1af27f39bce8909c9a3fd8cbe", size = 783997 },
    { url = "https://files.pythonhosted.org/packages/f9/a1/eb378dada8b91c0e4c5f08ffb56f25fcae47bf52ad18f9b2f33b83e6d498/regex-2024.11.6-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:982e6d21414e78e1f51cf595d7f321dcd14de1f2881c5dc6a6e23bbbbd68435e", size = 781725 },
    { url = "https://files.pythonhosted.org/packages/83/f2/033e7dec0cfd6dda93390089864732a3409246ffe8b042e9554afa9bff4e/regex-2024.11.6-cp312-cp312-musllinux_1_2_i686.whl", hash = "sha256:a7c2155f790e2fb448faed6dd241386719802296ec588a8b9051c1f5c481bc29", size = 789481 },
    { url = "https://files.pythonhosted.org/packages/83/23/15d4552ea28990a74e7696780c438aadd73a20318c47e527b47a4a5a596d/regex-2024.11.6-cp312-cp312-musllinux_1_2_ppc64le.whl", hash = "sha256:149f5008d286636e48cd0b1dd65018548944e495b0265b45e1bffecce1ef7f39", size = 852896 },
    { url = "https://files.pythonhosted.org/packages/e3/39/ed4416bc90deedbfdada2568b2cb0bc1fdb98efe11f5378d9892b2a88f8f/regex-2024.11.6-cp312-cp312-musllinux_1_2_s390x.whl", hash = "sha256:e5364a4502efca094731680e80009632ad6624084aff9a23ce8c8c6820de3e51", size = 860138 },
    { url = "https://files.pythonhosted.org/packages/93/2d/dd56bb76bd8e95bbce684326302f287455b56242a4f9c61f1bc76e28360e/regex-2024.11.6-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:0a86e7eeca091c09e021db8eb72d54751e527fa47b8d5787caf96d9831bd02ad", size = 787692 },
    { url = "https://files.pythonhosted.org/packages/0b/55/31877a249ab7a5156758246b9c59539abbeba22461b7d8adc9e8475ff73e/regex-2024.11.6-cp312-cp312-win32.whl", hash = "sha256:32f9a4c643baad4efa81d549c2aadefaeba12249b2adc5af541759237eee1c54", size = 262135 },
    { url = "https://files.pythonhosted.org/packages/38/ec/ad2d7de49a600cdb8dd78434a1aeffe28b9d6fc42eb36afab4a27ad23384/regex-2024.11.6-cp312-cp312-win_amd64.whl", hash = "sha256:a93c194e2df18f7d264092dc8539b8ffb86b45b899ab976aa15d48214138e81b", size = 273567 },
    { url = "https://files.pythonhosted.org/packages/90/73/bcb0e36614601016552fa9344544a3a2ae1809dc1401b100eab02e772e1f/regex-2024.11.6-cp313-cp313-macosx_10_13_universal2.whl", hash = "sha256:a6ba92c0bcdf96cbf43a12c717eae4bc98325ca3730f6b130ffa2e3c3c723d84", size = 483525 },
    { url = "https://files.pythonhosted.org/packages/0f/3f/f1a082a46b31e25291d830b369b6b0c5576a6f7fb89d3053a354c24b8a83/regex-2024.11.6-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:525eab0b789891ac3be914d36893bdf972d483fe66551f79d3e27146191a37d4", size = 288324 },
    { url = "https://files.pythonhosted.org/packages/09/c9/4e68181a4a652fb3ef5099e077faf4fd2a694ea6e0f806a7737aff9e758a/regex-2024.11.6-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:086a27a0b4ca227941700e0b31425e7a28ef1ae8e5e05a33826e17e47fbfdba0", size = 284617 },
    { url = "https://files.pythonhosted.org/packages/fc/fd/37868b75eaf63843165f1d2122ca6cb94bfc0271e4428cf58c0616786dce/regex-2024.11.6-cp313-cp313-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:bde01f35767c4a7899b7eb6e823b125a64de314a8ee9791367c9a34d56af18d0", size = 795023 },
    { url = "https://files.pythonhosted.org/packages/c4/7c/d4cd9c528502a3dedb5c13c146e7a7a539a3853dc20209c8e75d9ba9d1b2/regex-2024.11.6-cp313-cp313-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:b583904576650166b3d920d2bcce13971f6f9e9a396c673187f49811b2769dc7", size = 833072 },
    { url = "https://files.pythonhosted.org/packages/4f/db/46f563a08f969159c5a0f0e722260568425363bea43bb7ae370becb66a67/regex-2024.11.6-cp313-cp313-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:1c4de13f06a0d54fa0d5ab1b7138bfa0d883220965a29616e3ea61b35d5f5fc7", size = 823130 },
    { url = "https://files.pythonhosted.org/packages/db/60/1eeca2074f5b87df394fccaa432ae3fc06c9c9bfa97c5051aed70e6e00c2/regex-2024.11.6-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:3cde6e9f2580eb1665965ce9bf17ff4952f34f5b126beb509fee8f4e994f143c", size = 796857 },
    { url = "https://files.pythonhosted.org/packages/10/db/ac718a08fcee981554d2f7bb8402f1faa7e868c1345c16ab1ebec54b0d7b/regex-2024.11.6-cp313-cp313-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:0d7f453dca13f40a02b79636a339c5b62b670141e63efd511d3f8f73fba162b3", size = 784006 },
    { url = "https://files.pythonhosted.org/packages/c2/41/7da3fe70216cea93144bf12da2b87367590bcf07db97604edeea55dac9ad/regex-2024.11.6-cp313-cp313-musllinux_1_2_aarch64.whl", hash = "sha256:59dfe1ed21aea057a65c6b586afd2a945de04fc7db3de0a6e3ed5397ad491b07", size = 781650 },
    { url = "https://files.pythonhosted.org/packages/a7/d5/880921ee4eec393a4752e6ab9f0fe28009435417c3102fc413f3fe81c4e5/regex-2024.11.6-cp313-cp313-musllinux_1_2_i686.whl", hash = "sha256:b97c1e0bd37c5cd7902e65f410779d39eeda155800b65fc4d04cc432efa9bc6e", size = 789545 },
    { url = "https://files.pythonhosted.org/packages/dc/96/53770115e507081122beca8899ab7f5ae28ae790bfcc82b5e38976df6a77/regex-2024.11.6-cp313-cp313-musllinux_1_2_ppc64le.whl", hash = "sha256:f9d1e379028e0fc2ae3654bac3cbbef81bf3fd571272a42d56c24007979bafb6", size = 853045 },
    { url = "https://files.pythonhosted.org/packages/31/d3/1372add5251cc2d44b451bd94f43b2ec78e15a6e82bff6a290ef9fd8f00a/regex-2024.11.6-cp313-cp313-musllinux_1_2_s390x.whl", hash = "sha256:13291b39131e2d002a7940fb176e120bec5145f3aeb7621be6534e46251912c4", size = 860182 },
    { url = "https://files.pythonhosted.org/packages/ed/e3/c446a64984ea9f69982ba1a69d4658d5014bc7a0ea468a07e1a1265db6e2/regex-2024.11.6-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:4f51f88c126370dcec4908576c5a627220da6c09d0bff31cfa89f2523843316d", size = 787733 },
    { url = "https://files.pythonhosted.org/packages/2b/f1/e40c8373e3480e4f29f2692bd21b3e05f296d3afebc7e5dcf21b9756ca1c/regex-2024.11.6-cp313-cp313-win32.whl", hash = "sha256:63b13cfd72e9601125027202cad74995ab26921d8cd935c25f09c630436348ff", size = 262122 },
    { url = "https://files.pythonhosted.org/packages/45/94/bc295babb3062a731f52621cdc992d123111282e291abaf23faa413443ea/regex-2024.11.6-cp313-cp313-win_amd64.whl", hash = "sha256:2b3361af3198667e99927da8b84c1b010752fa4b1115ee30beaa332cabc3ef1a", size = 273545 },
]

[[package]]
name = "requests"
version = "2.32.3"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "certifi" },
    { name = "charset-normalizer" },
    { name = "idna" },
    { name = "urllib3" },
]
sdist = { url = "https://files.pythonhosted.org/packages/63/70/2bf7780ad2d390a8d301ad0b550f1581eadbd9a20f896afe06353c2a2913/requests-2.32.3.tar.gz", hash = "sha256:55365417734eb18255590a9ff9eb97e9e1da868d4ccd6402399eaf68af20a760", size = 131218 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/f9/9b/335f9764261e915ed497fcdeb11df5dfd6f7bf257d4a6a2a686d80da4d54/requests-2.32.3-py3-none-any.whl", hash = "sha256:70761cfe03c773ceb22aa2f671b4757976145175cdfca038c02654d061d6dcc6", size = 64928 },
]

[[package]]
name = "rich"
version = "13.9.4"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "markdown-it-py" },
    { name = "pygments" },
    { name = "typing-extensions", marker = "python_full_version < '3.11'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/ab/3a/0316b28d0761c6734d6bc14e770d85506c986c85ffb239e688eeaab2c2bc/rich-13.9.4.tar.gz", hash = "sha256:439594978a49a09530cff7ebc4b5c7103ef57baf48d5ea3184f21d9a2befa098", size = 223149 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/19/71/39c7c0d87f8d4e6c020a393182060eaefeeae6c01dab6a84ec346f2567df/rich-13.9.4-py3-none-any.whl", hash = "sha256:6049d5e6ec054bf2779ab3358186963bac2ea89175919d699e378b99738c2a90", size = 242424 },
]

[[package]]
name = "ruff"
version = "0.8.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/95/d0/8ff5b189d125f4260f2255d143bf2fa413b69c2610c405ace7a0a8ec81ec/ruff-0.8.1.tar.gz", hash = "sha256:3583db9a6450364ed5ca3f3b4225958b24f78178908d5c4bc0f46251ccca898f", size = 3313222 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/a2/d6/1a6314e568db88acdbb5121ed53e2c52cebf3720d3437a76f82f923bf171/ruff-0.8.1-py3-none-linux_armv6l.whl", hash = "sha256:fae0805bd514066f20309f6742f6ee7904a773eb9e6c17c45d6b1600ca65c9b5", size = 10532605 },
    { url = "https://files.pythonhosted.org/packages/89/a8/a957a8812e31facffb6a26a30be0b5b4af000a6e30c7d43a22a5232a3398/ruff-0.8.1-py3-none-macosx_10_12_x86_64.whl", hash = "sha256:b8a4f7385c2285c30f34b200ca5511fcc865f17578383db154e098150ce0a087", size = 10278243 },
    { url = "https://files.pythonhosted.org/packages/a8/23/9db40fa19c453fabf94f7a35c61c58f20e8200b4734a20839515a19da790/ruff-0.8.1-py3-none-macosx_11_0_arm64.whl", hash = "sha256:cd054486da0c53e41e0086e1730eb77d1f698154f910e0cd9e0d64274979a209", size = 9917739 },
    { url = "https://files.pythonhosted.org/packages/e2/a0/6ee2d949835d5701d832fc5acd05c0bfdad5e89cfdd074a171411f5ccad5/ruff-0.8.1-py3-none-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:2029b8c22da147c50ae577e621a5bfbc5d1fed75d86af53643d7a7aee1d23871", size = 10779153 },
    { url = "https://files.pythonhosted.org/packages/7a/25/9c11dca9404ef1eb24833f780146236131a3c7941de394bc356912ef1041/ruff-0.8.1-py3-none-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:2666520828dee7dfc7e47ee4ea0d928f40de72056d929a7c5292d95071d881d1", size = 10304387 },
    { url = "https://files.pythonhosted.org/packages/c8/b9/84c323780db1b06feae603a707d82dbbd85955c8c917738571c65d7d5aff/ruff-0.8.1-py3-none-manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:333c57013ef8c97a53892aa56042831c372e0bb1785ab7026187b7abd0135ad5", size = 11360351 },
    { url = "https://files.pythonhosted.org/packages/6b/e1/9d4bbb2ace7aad14ded20e4674a48cda5b902aed7a1b14e6b028067060c4/ruff-0.8.1-py3-none-manylinux_2_17_ppc64.manylinux2014_ppc64.whl", hash = "sha256:288326162804f34088ac007139488dcb43de590a5ccfec3166396530b58fb89d", size = 12022879 },
    { url = "https://files.pythonhosted.org/packages/75/28/752ff6120c0e7f9981bc4bc275d540c7f36db1379ba9db9142f69c88db21/ruff-0.8.1-py3-none-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:b12c39b9448632284561cbf4191aa1b005882acbc81900ffa9f9f471c8ff7e26", size = 11610354 },
    { url = "https://files.pythonhosted.org/packages/ba/8c/967b61c2cc8ebd1df877607fbe462bc1e1220b4a30ae3352648aec8c24bd/ruff-0.8.1-py3-none-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:364e6674450cbac8e998f7b30639040c99d81dfb5bbc6dfad69bc7a8f916b3d1", size = 12813976 },
    { url = "https://files.pythonhosted.org/packages/7f/29/e059f945d6bd2d90213387b8c360187f2fefc989ddcee6bbf3c241329b92/ruff-0.8.1-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:b22346f845fec132aa39cd29acb94451d030c10874408dbf776af3aaeb53284c", size = 11154564 },
    { url = "https://files.pythonhosted.org/packages/55/47/cbd05e5a62f3fb4c072bc65c1e8fd709924cad1c7ec60a1000d1e4ee8307/ruff-0.8.1-py3-none-musllinux_1_2_aarch64.whl", hash = "sha256:b2f2f7a7e7648a2bfe6ead4e0a16745db956da0e3a231ad443d2a66a105c04fa", size = 10760604 },
    { url = "https://files.pythonhosted.org/packages/bb/ee/4c3981c47147c72647a198a94202633130cfda0fc95cd863a553b6f65c6a/ruff-0.8.1-py3-none-musllinux_1_2_armv7l.whl", hash = "sha256:adf314fc458374c25c5c4a4a9270c3e8a6a807b1bec018cfa2813d6546215540", size = 10391071 },
    { url = "https://files.pythonhosted.org/packages/6b/e6/083eb61300214590b188616a8ac6ae1ef5730a0974240fb4bec9c17de78b/ruff-0.8.1-py3-none-musllinux_1_2_i686.whl", hash = "sha256:a885d68342a231b5ba4d30b8c6e1b1ee3a65cf37e3d29b3c74069cdf1ee1e3c9", size = 10896657 },
    { url = "https://files.pythonhosted.org/packages/77/bd/aacdb8285d10f1b943dbeb818968efca35459afc29f66ae3bd4596fbf954/ruff-0.8.1-py3-none-musllinux_1_2_x86_64.whl", hash = "sha256:d2c16e3508c8cc73e96aa5127d0df8913d2290098f776416a4b157657bee44c5", size = 11228362 },
    { url = "https://files.pythonhosted.org/packages/39/72/fcb7ad41947f38b4eaa702aca0a361af0e9c2bf671d7fd964480670c297e/ruff-0.8.1-py3-none-win32.whl", hash = "sha256:93335cd7c0eaedb44882d75a7acb7df4b77cd7cd0d2255c93b28791716e81790", size = 8803476 },
    { url = "https://files.pythonhosted.org/packages/e4/ea/cae9aeb0f4822c44651c8407baacdb2e5b4dcd7b31a84e1c5df33aa2cc20/ruff-0.8.1-py3-none-win_amd64.whl", hash = "sha256:2954cdbe8dfd8ab359d4a30cd971b589d335a44d444b6ca2cb3d1da21b75e4b6", size = 9614463 },
    { url = "https://files.pythonhosted.org/packages/eb/76/fbb4bd23dfb48fa7758d35b744413b650a9fd2ddd93bca77e30376864414/ruff-0.8.1-py3-none-win_arm64.whl", hash = "sha256:55873cc1a473e5ac129d15eccb3c008c096b94809d693fc7053f588b67822737", size = 8959621 },
]

[[package]]
name = "shellingham"
version = "1.5.4"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/58/15/8b3609fd3830ef7b27b655beb4b4e9c62313a4e8da8c676e142cc210d58e/shellingham-1.5.4.tar.gz", hash = "sha256:8dbca0739d487e5bd35ab3ca4b36e11c4078f3a234bfce294b0a0291363404de", size = 10310 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/e0/f9/0595336914c5619e5f28a1fb793285925a8cd4b432c9da0a987836c7f822/shellingham-1.5.4-py2.py3-none-any.whl", hash = "sha256:7ecfff8f2fd72616f7481040475a65b2bf8af90a56c89140852d1120324e8686", size = 9755 },
]

[[package]]
name = "smmap"
version = "5.0.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/88/04/b5bf6d21dc4041000ccba7eb17dd3055feb237e7ffc2c20d3fae3af62baa/smmap-5.0.1.tar.gz", hash = "sha256:dceeb6c0028fdb6734471eb07c0cd2aae706ccaecab45965ee83f11c8d3b1f62", size = 22291 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/a7/a5/10f97f73544edcdef54409f1d839f6049a0d79df68adbc1ceb24d1aaca42/smmap-5.0.1-py3-none-any.whl", hash = "sha256:e6d8668fa5f93e706934a62d7b4db19c8d9eb8cf2adbb75ef1b675aa332b69da", size = 24282 },
]

[[package]]
name = "sniffio"
version = "1.3.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/a2/87/a6771e1546d97e7e041b6ae58d80074f81b7d5121207425c964ddf5cfdbd/sniffio-1.3.1.tar.gz", hash = "sha256:f4324edc670a0f49750a81b895f35c3adb843cca46f0530f79fc1babb23789dc", size = 20372 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/e9/44/75a9c9421471a6c4805dbf2356f7c181a29c1879239abab1ea2cc8f38b40/sniffio-1.3.1-py3-none-any.whl", hash = "sha256:2f6da418d1f1e0fddd844478f41680e794e6051915791a034ff65e5f100525a2", size = 10235 },
]

[[package]]
name = "sse-starlette"
version = "2.1.3"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "anyio" },
    { name = "starlette" },
    { name = "uvicorn" },
]
sdist = { url = "https://files.pythonhosted.org/packages/72/fc/56ab9f116b2133521f532fce8d03194cf04dcac25f583cf3d839be4c0496/sse_starlette-2.1.3.tar.gz", hash = "sha256:9cd27eb35319e1414e3d2558ee7414487f9529ce3b3cf9b21434fd110e017169", size = 19678 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/52/aa/36b271bc4fa1d2796311ee7c7283a3a1c348bad426d37293609ca4300eef/sse_starlette-2.1.3-py3-none-any.whl", hash = "sha256:8ec846438b4665b9e8c560fcdea6bc8081a3abf7942faa95e5a744999d219772", size = 9383 },
]

[[package]]
name = "stack-data"
version = "0.6.3"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "asttokens" },
    { name = "executing" },
    { name = "pure-eval" },
]
sdist = { url = "https://files.pythonhosted.org/packages/28/e3/55dcc2cfbc3ca9c29519eb6884dd1415ecb53b0e934862d3559ddcb7e20b/stack_data-0.6.3.tar.gz", hash = "sha256:836a778de4fec4dcd1dcd89ed8abff8a221f58308462e1c4aa2a3cf30148f0b9", size = 44707 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/f1/7b/ce1eafaf1a76852e2ec9b22edecf1daa58175c090266e9f6c64afcd81d91/stack_data-0.6.3-py3-none-any.whl", hash = "sha256:d5558e0c25a4cb0853cddad3d77da9891a08cb85dd9f9f91b9f8cd66e511e695", size = 24521 },
]

[[package]]
name = "starlette"
version = "0.41.3"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "anyio" },
]
sdist = { url = "https://files.pythonhosted.org/packages/1a/4c/9b5764bd22eec91c4039ef4c55334e9187085da2d8a2df7bd570869aae18/starlette-0.41.3.tar.gz", hash = "sha256:0e4ab3d16522a255be6b28260b938eae2482f98ce5cc934cb08dce8dc3ba5835", size = 2574159 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/96/00/2b325970b3060c7cecebab6d295afe763365822b1306a12eeab198f74323/starlette-0.41.3-py3-none-any.whl", hash = "sha256:44cedb2b7c77a9de33a8b74b2b90e9f50d11fcf25d8270ea525ad71a25374ff7", size = 73225 },
]

[[package]]
name = "tiktoken"
version = "0.8.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "regex" },
    { name = "requests" },
]
sdist = { url = "https://files.pythonhosted.org/packages/37/02/576ff3a6639e755c4f70997b2d315f56d6d71e0d046f4fb64cb81a3fb099/tiktoken-0.8.0.tar.gz", hash = "sha256:9ccbb2740f24542534369c5635cfd9b2b3c2490754a78ac8831d99f89f94eeb2", size = 35107 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/c9/ba/a35fad753bbca8ba0cc1b0f3402a70256a110ced7ac332cf84ba89fc87ab/tiktoken-0.8.0-cp310-cp310-macosx_10_9_x86_64.whl", hash = "sha256:b07e33283463089c81ef1467180e3e00ab00d46c2c4bbcef0acab5f771d6695e", size = 1039905 },
    { url = "https://files.pythonhosted.org/packages/91/05/13dab8fd7460391c387b3e69e14bf1e51ff71fe0a202cd2933cc3ea93fb6/tiktoken-0.8.0-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:9269348cb650726f44dd3bbb3f9110ac19a8dcc8f54949ad3ef652ca22a38e21", size = 982417 },
    { url = "https://files.pythonhosted.org/packages/e9/98/18ec4a8351a6cf4537e40cd6e19a422c10cce1ef00a2fcb716e0a96af58b/tiktoken-0.8.0-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:25e13f37bc4ef2d012731e93e0fef21dc3b7aea5bb9009618de9a4026844e560", size = 1144915 },
    { url = "https://files.pythonhosted.org/packages/2e/28/cf3633018cbcc6deb7805b700ccd6085c9a5a7f72b38974ee0bffd56d311/tiktoken-0.8.0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:f13d13c981511331eac0d01a59b5df7c0d4060a8be1e378672822213da51e0a2", size = 1177221 },
    { url = "https://files.pythonhosted.org/packages/57/81/8a5be305cbd39d4e83a794f9e80c7f2c84b524587b7feb27c797b2046d51/tiktoken-0.8.0-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:6b2ddbc79a22621ce8b1166afa9f9a888a664a579350dc7c09346a3b5de837d9", size = 1237398 },
    { url = "https://files.pythonhosted.org/packages/dc/da/8d1cc3089a83f5cf11c2e489332752981435280285231924557350523a59/tiktoken-0.8.0-cp310-cp310-win_amd64.whl", hash = "sha256:d8c2d0e5ba6453a290b86cd65fc51fedf247e1ba170191715b049dac1f628005", size = 884215 },
    { url = "https://files.pythonhosted.org/packages/f6/1e/ca48e7bfeeccaf76f3a501bd84db1fa28b3c22c9d1a1f41af9fb7579c5f6/tiktoken-0.8.0-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:d622d8011e6d6f239297efa42a2657043aaed06c4f68833550cac9e9bc723ef1", size = 1039700 },
    { url = "https://files.pythonhosted.org/packages/8c/f8/f0101d98d661b34534769c3818f5af631e59c36ac6d07268fbfc89e539ce/tiktoken-0.8.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:2efaf6199717b4485031b4d6edb94075e4d79177a172f38dd934d911b588d54a", size = 982413 },
    { url = "https://files.pythonhosted.org/packages/ac/3c/2b95391d9bd520a73830469f80a96e3790e6c0a5ac2444f80f20b4b31051/tiktoken-0.8.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:5637e425ce1fc49cf716d88df3092048359a4b3bbb7da762840426e937ada06d", size = 1144242 },
    { url = "https://files.pythonhosted.org/packages/01/c4/c4a4360de845217b6aa9709c15773484b50479f36bb50419c443204e5de9/tiktoken-0.8.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:9fb0e352d1dbe15aba082883058b3cce9e48d33101bdaac1eccf66424feb5b47", size = 1176588 },
    { url = "https://files.pythonhosted.org/packages/f8/a3/ef984e976822cd6c2227c854f74d2e60cf4cd6fbfca46251199914746f78/tiktoken-0.8.0-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:56edfefe896c8f10aba372ab5706b9e3558e78db39dd497c940b47bf228bc419", size = 1237261 },
    { url = "https://files.pythonhosted.org/packages/1e/86/eea2309dc258fb86c7d9b10db536434fc16420feaa3b6113df18b23db7c2/tiktoken-0.8.0-cp311-cp311-win_amd64.whl", hash = "sha256:326624128590def898775b722ccc327e90b073714227175ea8febbc920ac0a99", size = 884537 },
    { url = "https://files.pythonhosted.org/packages/c1/22/34b2e136a6f4af186b6640cbfd6f93400783c9ef6cd550d9eab80628d9de/tiktoken-0.8.0-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:881839cfeae051b3628d9823b2e56b5cc93a9e2efb435f4cf15f17dc45f21586", size = 1039357 },
    { url = "https://files.pythonhosted.org/packages/04/d2/c793cf49c20f5855fd6ce05d080c0537d7418f22c58e71f392d5e8c8dbf7/tiktoken-0.8.0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:fe9399bdc3f29d428f16a2f86c3c8ec20be3eac5f53693ce4980371c3245729b", size = 982616 },
    { url = "https://files.pythonhosted.org/packages/b3/a1/79846e5ef911cd5d75c844de3fa496a10c91b4b5f550aad695c5df153d72/tiktoken-0.8.0-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:9a58deb7075d5b69237a3ff4bb51a726670419db6ea62bdcd8bd80c78497d7ab", size = 1144011 },
    { url = "https://files.pythonhosted.org/packages/26/32/e0e3a859136e95c85a572e4806dc58bf1ddf651108ae8b97d5f3ebe1a244/tiktoken-0.8.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:d2908c0d043a7d03ebd80347266b0e58440bdef5564f84f4d29fb235b5df3b04", size = 1175432 },
    { url = "https://files.pythonhosted.org/packages/c7/89/926b66e9025b97e9fbabeaa59048a736fe3c3e4530a204109571104f921c/tiktoken-0.8.0-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:294440d21a2a51e12d4238e68a5972095534fe9878be57d905c476017bff99fc", size = 1236576 },
    { url = "https://files.pythonhosted.org/packages/45/e2/39d4aa02a52bba73b2cd21ba4533c84425ff8786cc63c511d68c8897376e/tiktoken-0.8.0-cp312-cp312-win_amd64.whl", hash = "sha256:d8f3192733ac4d77977432947d563d7e1b310b96497acd3c196c9bddb36ed9db", size = 883824 },
    { url = "https://files.pythonhosted.org/packages/e3/38/802e79ba0ee5fcbf240cd624143f57744e5d411d2e9d9ad2db70d8395986/tiktoken-0.8.0-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:02be1666096aff7da6cbd7cdaa8e7917bfed3467cd64b38b1f112e96d3b06a24", size = 1039648 },
    { url = "https://files.pythonhosted.org/packages/b1/da/24cdbfc302c98663fbea66f5866f7fa1048405c7564ab88483aea97c3b1a/tiktoken-0.8.0-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:c94ff53c5c74b535b2cbf431d907fc13c678bbd009ee633a2aca269a04389f9a", size = 982763 },
    { url = "https://files.pythonhosted.org/packages/e4/f0/0ecf79a279dfa41fc97d00adccf976ecc2556d3c08ef3e25e45eb31f665b/tiktoken-0.8.0-cp313-cp313-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:6b231f5e8982c245ee3065cd84a4712d64692348bc609d84467c57b4b72dcbc5", size = 1144417 },
    { url = "https://files.pythonhosted.org/packages/ab/d3/155d2d4514f3471a25dc1d6d20549ef254e2aa9bb5b1060809b1d3b03d3a/tiktoken-0.8.0-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:4177faa809bd55f699e88c96d9bb4635d22e3f59d635ba6fd9ffedf7150b9953", size = 1175108 },
    { url = "https://files.pythonhosted.org/packages/19/eb/5989e16821ee8300ef8ee13c16effc20dfc26c777d05fbb6825e3c037b81/tiktoken-0.8.0-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:5376b6f8dc4753cd81ead935c5f518fa0fbe7e133d9e25f648d8c4dabdd4bad7", size = 1236520 },
    { url = "https://files.pythonhosted.org/packages/40/59/14b20465f1d1cb89cfbc96ec27e5617b2d41c79da12b5e04e96d689be2a7/tiktoken-0.8.0-cp313-cp313-win_amd64.whl", hash = "sha256:18228d624807d66c87acd8f25fc135665617cab220671eb65b50f5d70fa51f69", size = 883849 },
]

[[package]]
name = "tomli"
version = "2.2.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/18/87/302344fed471e44a87289cf4967697d07e532f2421fdaf868a303cbae4ff/tomli-2.2.1.tar.gz", hash = "sha256:cd45e1dc79c835ce60f7404ec8119f2eb06d38b1deba146f07ced3bbc44505ff", size = 17175 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/43/ca/75707e6efa2b37c77dadb324ae7d9571cb424e61ea73fad7c56c2d14527f/tomli-2.2.1-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:678e4fa69e4575eb77d103de3df8a895e1591b48e740211bd1067378c69e8249", size = 131077 },
    { url = "https://files.pythonhosted.org/packages/c7/16/51ae563a8615d472fdbffc43a3f3d46588c264ac4f024f63f01283becfbb/tomli-2.2.1-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:023aa114dd824ade0100497eb2318602af309e5a55595f76b626d6d9f3b7b0a6", size = 123429 },
    { url = "https://files.pythonhosted.org/packages/f1/dd/4f6cd1e7b160041db83c694abc78e100473c15d54620083dbd5aae7b990e/tomli-2.2.1-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:ece47d672db52ac607a3d9599a9d48dcb2f2f735c6c2d1f34130085bb12b112a", size = 226067 },
    { url = "https://files.pythonhosted.org/packages/a9/6b/c54ede5dc70d648cc6361eaf429304b02f2871a345bbdd51e993d6cdf550/tomli-2.2.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:6972ca9c9cc9f0acaa56a8ca1ff51e7af152a9f87fb64623e31d5c83700080ee", size = 236030 },
    { url = "https://files.pythonhosted.org/packages/1f/47/999514fa49cfaf7a92c805a86c3c43f4215621855d151b61c602abb38091/tomli-2.2.1-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:c954d2250168d28797dd4e3ac5cf812a406cd5a92674ee4c8f123c889786aa8e", size = 240898 },
    { url = "https://files.pythonhosted.org/packages/73/41/0a01279a7ae09ee1573b423318e7934674ce06eb33f50936655071d81a24/tomli-2.2.1-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:8dd28b3e155b80f4d54beb40a441d366adcfe740969820caf156c019fb5c7ec4", size = 229894 },
    { url = "https://files.pythonhosted.org/packages/55/18/5d8bc5b0a0362311ce4d18830a5d28943667599a60d20118074ea1b01bb7/tomli-2.2.1-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:e59e304978767a54663af13c07b3d1af22ddee3bb2fb0618ca1593e4f593a106", size = 245319 },
    { url = "https://files.pythonhosted.org/packages/92/a3/7ade0576d17f3cdf5ff44d61390d4b3febb8a9fc2b480c75c47ea048c646/tomli-2.2.1-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:33580bccab0338d00994d7f16f4c4ec25b776af3ffaac1ed74e0b3fc95e885a8", size = 238273 },
    { url = "https://files.pythonhosted.org/packages/72/6f/fa64ef058ac1446a1e51110c375339b3ec6be245af9d14c87c4a6412dd32/tomli-2.2.1-cp311-cp311-win32.whl", hash = "sha256:465af0e0875402f1d226519c9904f37254b3045fc5084697cefb9bdde1ff99ff", size = 98310 },
    { url = "https://files.pythonhosted.org/packages/6a/1c/4a2dcde4a51b81be3530565e92eda625d94dafb46dbeb15069df4caffc34/tomli-2.2.1-cp311-cp311-win_amd64.whl", hash = "sha256:2d0f2fdd22b02c6d81637a3c95f8cd77f995846af7414c5c4b8d0545afa1bc4b", size = 108309 },
    { url = "https://files.pythonhosted.org/packages/52/e1/f8af4c2fcde17500422858155aeb0d7e93477a0d59a98e56cbfe75070fd0/tomli-2.2.1-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:4a8f6e44de52d5e6c657c9fe83b562f5f4256d8ebbfe4ff922c495620a7f6cea", size = 132762 },
    { url = "https://files.pythonhosted.org/packages/03/b8/152c68bb84fc00396b83e7bbddd5ec0bd3dd409db4195e2a9b3e398ad2e3/tomli-2.2.1-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:8d57ca8095a641b8237d5b079147646153d22552f1c637fd3ba7f4b0b29167a8", size = 123453 },
    { url = "https://files.pythonhosted.org/packages/c8/d6/fc9267af9166f79ac528ff7e8c55c8181ded34eb4b0e93daa767b8841573/tomli-2.2.1-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:4e340144ad7ae1533cb897d406382b4b6fede8890a03738ff1683af800d54192", size = 233486 },
    { url = "https://files.pythonhosted.org/packages/5c/51/51c3f2884d7bab89af25f678447ea7d297b53b5a3b5730a7cb2ef6069f07/tomli-2.2.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:db2b95f9de79181805df90bedc5a5ab4c165e6ec3fe99f970d0e302f384ad222", size = 242349 },
    { url = "https://files.pythonhosted.org/packages/ab/df/bfa89627d13a5cc22402e441e8a931ef2108403db390ff3345c05253935e/tomli-2.2.1-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:40741994320b232529c802f8bc86da4e1aa9f413db394617b9a256ae0f9a7f77", size = 252159 },
    { url = "https://files.pythonhosted.org/packages/9e/6e/fa2b916dced65763a5168c6ccb91066f7639bdc88b48adda990db10c8c0b/tomli-2.2.1-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:400e720fe168c0f8521520190686ef8ef033fb19fc493da09779e592861b78c6", size = 237243 },
    { url = "https://files.pythonhosted.org/packages/b4/04/885d3b1f650e1153cbb93a6a9782c58a972b94ea4483ae4ac5cedd5e4a09/tomli-2.2.1-cp312-cp312-musllinux_1_2_i686.whl", hash = "sha256:02abe224de6ae62c19f090f68da4e27b10af2b93213d36cf44e6e1c5abd19fdd", size = 259645 },
    { url = "https://files.pythonhosted.org/packages/9c/de/6b432d66e986e501586da298e28ebeefd3edc2c780f3ad73d22566034239/tomli-2.2.1-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:b82ebccc8c8a36f2094e969560a1b836758481f3dc360ce9a3277c65f374285e", size = 244584 },
    { url = "https://files.pythonhosted.org/packages/1c/9a/47c0449b98e6e7d1be6cbac02f93dd79003234ddc4aaab6ba07a9a7482e2/tomli-2.2.1-cp312-cp312-win32.whl", hash = "sha256:889f80ef92701b9dbb224e49ec87c645ce5df3fa2cc548664eb8a25e03127a98", size = 98875 },
    { url = "https://files.pythonhosted.org/packages/ef/60/9b9638f081c6f1261e2688bd487625cd1e660d0a85bd469e91d8db969734/tomli-2.2.1-cp312-cp312-win_amd64.whl", hash = "sha256:7fc04e92e1d624a4a63c76474610238576942d6b8950a2d7f908a340494e67e4", size = 109418 },
    { url = "https://files.pythonhosted.org/packages/04/90/2ee5f2e0362cb8a0b6499dc44f4d7d48f8fff06d28ba46e6f1eaa61a1388/tomli-2.2.1-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:f4039b9cbc3048b2416cc57ab3bda989a6fcf9b36cf8937f01a6e731b64f80d7", size = 132708 },
    { url = "https://files.pythonhosted.org/packages/c0/ec/46b4108816de6b385141f082ba99e315501ccd0a2ea23db4a100dd3990ea/tomli-2.2.1-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:286f0ca2ffeeb5b9bd4fcc8d6c330534323ec51b2f52da063b11c502da16f30c", size = 123582 },
    { url = "https://files.pythonhosted.org/packages/a0/bd/b470466d0137b37b68d24556c38a0cc819e8febe392d5b199dcd7f578365/tomli-2.2.1-cp313-cp313-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:a92ef1a44547e894e2a17d24e7557a5e85a9e1d0048b0b5e7541f76c5032cb13", size = 232543 },
    { url = "https://files.pythonhosted.org/packages/d9/e5/82e80ff3b751373f7cead2815bcbe2d51c895b3c990686741a8e56ec42ab/tomli-2.2.1-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:9316dc65bed1684c9a98ee68759ceaed29d229e985297003e494aa825ebb0281", size = 241691 },
    { url = "https://files.pythonhosted.org/packages/05/7e/2a110bc2713557d6a1bfb06af23dd01e7dde52b6ee7dadc589868f9abfac/tomli-2.2.1-cp313-cp313-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:e85e99945e688e32d5a35c1ff38ed0b3f41f43fad8df0bdf79f72b2ba7bc5272", size = 251170 },
    { url = "https://files.pythonhosted.org/packages/64/7b/22d713946efe00e0adbcdfd6d1aa119ae03fd0b60ebed51ebb3fa9f5a2e5/tomli-2.2.1-cp313-cp313-musllinux_1_2_aarch64.whl", hash = "sha256:ac065718db92ca818f8d6141b5f66369833d4a80a9d74435a268c52bdfa73140", size = 236530 },
    { url = "https://files.pythonhosted.org/packages/38/31/3a76f67da4b0cf37b742ca76beaf819dca0ebef26d78fc794a576e08accf/tomli-2.2.1-cp313-cp313-musllinux_1_2_i686.whl", hash = "sha256:d920f33822747519673ee656a4b6ac33e382eca9d331c87770faa3eef562aeb2", size = 258666 },
    { url = "https://files.pythonhosted.org/packages/07/10/5af1293da642aded87e8a988753945d0cf7e00a9452d3911dd3bb354c9e2/tomli-2.2.1-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:a198f10c4d1b1375d7687bc25294306e551bf1abfa4eace6650070a5c1ae2744", size = 243954 },
    { url = "https://files.pythonhosted.org/packages/5b/b9/1ed31d167be802da0fc95020d04cd27b7d7065cc6fbefdd2f9186f60d7bd/tomli-2.2.1-cp313-cp313-win32.whl", hash = "sha256:d3f5614314d758649ab2ab3a62d4f2004c825922f9e370b29416484086b264ec", size = 98724 },
    { url = "https://files.pythonhosted.org/packages/c7/32/b0963458706accd9afcfeb867c0f9175a741bf7b19cd424230714d722198/tomli-2.2.1-cp313-cp313-win_amd64.whl", hash = "sha256:a38aa0308e754b0e3c67e344754dff64999ff9b513e691d0e786265c93583c69", size = 109383 },
    { url = "https://files.pythonhosted.org/packages/6e/c2/61d3e0f47e2b74ef40a68b9e6ad5984f6241a942f7cd3bbfbdbd03861ea9/tomli-2.2.1-py3-none-any.whl", hash = "sha256:cb55c73c5f4408779d0cf3eef9f762b9c9f147a77de7b258bef0a5628adc85cc", size = 14257 },
]

[[package]]
name = "traitlets"
version = "5.14.3"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/eb/79/72064e6a701c2183016abbbfedaba506d81e30e232a68c9f0d6f6fcd1574/traitlets-5.14.3.tar.gz", hash = "sha256:9ed0579d3502c94b4b3732ac120375cda96f923114522847de4b3bb98b96b6b7", size = 161621 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/00/c0/8f5d070730d7836adc9c9b6408dec68c6ced86b304a9b26a14df072a6e8c/traitlets-5.14.3-py3-none-any.whl", hash = "sha256:b74e89e397b1ed28cc831db7aea759ba6640cb3de13090ca145426688ff1ac4f", size = 85359 },
]

[[package]]
name = "typer"
version = "0.14.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "click" },
    { name = "rich" },
    { name = "shellingham" },
    { name = "typing-extensions" },
]
sdist = { url = "https://files.pythonhosted.org/packages/0d/7e/24af5b9aaa0872f9f6dc5dcf789dc3e57ceb23b4c570b852cd4db0d98f14/typer-0.14.0.tar.gz", hash = "sha256:af58f737f8d0c0c37b9f955a6d39000b9ff97813afcbeef56af5e37cf743b45a", size = 98836 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/bb/d8/a3ab71d5587b42b832a7ef2e65b3e51a18f8da32b6ce169637d4d21995ed/typer-0.14.0-py3-none-any.whl", hash = "sha256:f476233a25770ab3e7b2eebf7c68f3bc702031681a008b20167573a4b7018f09", size = 44707 },
]

[[package]]
name = "typing-extensions"
version = "4.12.2"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/df/db/f35a00659bc03fec321ba8bce9420de607a1d37f8342eee1863174c69557/typing_extensions-4.12.2.tar.gz", hash = "sha256:1a7ead55c7e559dd4dee8856e3a88b41225abfe1ce8df57b7c13915fe121ffb8", size = 85321 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/26/9f/ad63fc0248c5379346306f8668cda6e2e2e9c95e01216d2b8ffd9ff037d0/typing_extensions-4.12.2-py3-none-any.whl", hash = "sha256:04e5ca0351e0f3f85c6853954072df659d0d13fac324d0072316b67d7794700d", size = 37438 },
]

[[package]]
name = "urllib3"
version = "2.2.3"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/ed/63/22ba4ebfe7430b76388e7cd448d5478814d3032121827c12a2cc287e2260/urllib3-2.2.3.tar.gz", hash = "sha256:e7d814a81dad81e6caf2ec9fdedb284ecc9c73076b62654547cc64ccdcae26e9", size = 300677 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/ce/d9/5f4c13cecde62396b0d3fe530a50ccea91e7dfc1ccf0e09c228841bb5ba8/urllib3-2.2.3-py3-none-any.whl", hash = "sha256:ca899ca043dcb1bafa3e262d73aa25c465bfb49e0bd9dd5d59f1d0acba2f8fac", size = 126338 },
]

[[package]]
name = "uvicorn"
version = "0.32.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "click" },
    { name = "h11" },
    { name = "typing-extensions", marker = "python_full_version < '3.11'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/6a/3c/21dba3e7d76138725ef307e3d7ddd29b763119b3aa459d02cc05fefcff75/uvicorn-0.32.1.tar.gz", hash = "sha256:ee9519c246a72b1c084cea8d3b44ed6026e78a4a309cbedae9c37e4cb9fbb175", size = 77630 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/50/c1/2d27b0a15826c2b71dcf6e2f5402181ef85acf439617bb2f1453125ce1f3/uvicorn-0.32.1-py3-none-any.whl", hash = "sha256:82ad92fd58da0d12af7482ecdb5f2470a04c9c9a53ced65b9bbb4a205377602e", size = 63828 },
]

[[package]]
name = "virtualenv"
version = "20.28.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "distlib" },
    { name = "filelock" },
    { name = "platformdirs" },
]
sdist = { url = "https://files.pythonhosted.org/packages/bf/75/53316a5a8050069228a2f6d11f32046cfa94fbb6cc3f08703f59b873de2e/virtualenv-20.28.0.tar.gz", hash = "sha256:2c9c3262bb8e7b87ea801d715fae4495e6032450c71d2309be9550e7364049aa", size = 7650368 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/10/f9/0919cf6f1432a8c4baa62511f8f8da8225432d22e83e3476f5be1a1edc6e/virtualenv-20.28.0-py3-none-any.whl", hash = "sha256:23eae1b4516ecd610481eda647f3a7c09aea295055337331bb4e6892ecce47b0", size = 4276702 },
]

[[package]]
name = "wcwidth"
version = "0.2.13"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/6c/63/53559446a878410fc5a5974feb13d31d78d752eb18aeba59c7fef1af7598/wcwidth-0.2.13.tar.gz", hash = "sha256:72ea0c06399eb286d978fdedb6923a9eb47e1c486ce63e9b4e64fc18303972b5", size = 101301 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/fd/84/fd2ba7aafacbad3c4201d395674fc6348826569da3c0937e75505ead3528/wcwidth-0.2.13-py2.py3-none-any.whl", hash = "sha256:3da69048e4540d84af32131829ff948f1e022c1c6bdb8d6102117aac784f6859", size = 34166 },
]

[[package]]
name = "wmctrl"
version = "0.5"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "attrs" },
]
sdist = { url = "https://files.pythonhosted.org/packages/60/d9/6625ead93412c5ce86db1f8b4f2a70b8043e0a7c1d30099ba3c6a81641ff/wmctrl-0.5.tar.gz", hash = "sha256:7839a36b6fe9e2d6fd22304e5dc372dbced2116ba41283ea938b2da57f53e962", size = 5202 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/13/ca/723e3f8185738d7947f14ee7dc663b59415c6dee43bd71575f8c7f5cd6be/wmctrl-0.5-py2.py3-none-any.whl", hash = "sha256:ae695c1863a314c899e7cf113f07c0da02a394b968c4772e1936219d9234ddd7", size = 4268 },
]



================================================
File: .pre-commit-config.yaml
================================================
fail_fast: true

repos:
  - repo: https://github.com/abravalheri/validate-pyproject
    rev: v0.23
    hooks:
      - id: validate-pyproject

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        types_or: [yaml, json5]

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff-format
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]



================================================
File: .python-version
================================================
3.12




================================================
File: examples/complex_inputs.py
================================================
"""
FastMCP Complex inputs Example

Demonstrates validation via pydantic with complex models.
"""

from pydantic import BaseModel, Field
from typing import Annotated
from fastmcp.server import FastMCP

mcp = FastMCP("Shrimp Tank")


class ShrimpTank(BaseModel):
    class Shrimp(BaseModel):
        name: Annotated[str, Field(max_length=10)]

    shrimp: list[Shrimp]


@mcp.tool()
def name_shrimp(
    tank: ShrimpTank,
    # You can use pydantic Field in function signatures for validation.
    extra_names: Annotated[list[str], Field(max_length=10)],
) -> list[str]:
    """List all shrimp names in the tank"""
    return [shrimp.name for shrimp in tank.shrimp] + extra_names



================================================
File: examples/desktop.py
================================================
"""
FastMCP Desktop Example

A simple example that exposes the desktop directory as a resource.
"""

from pathlib import Path

from fastmcp.server import FastMCP

# Create server
mcp = FastMCP("Demo")


@mcp.resource("dir://desktop")
def desktop() -> list[str]:
    """List the files in the user's desktop"""
    desktop = Path.home() / "Desktop"
    return [str(f) for f in desktop.iterdir()]


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b



================================================
File: examples/echo.py
================================================
"""
FastMCP Echo Server
"""

from fastmcp import FastMCP

# Create server
mcp = FastMCP("Echo Server")


@mcp.tool()
def echo_tool(text: str) -> str:
    """Echo the input text"""
    return text


@mcp.resource("echo://static")
def echo_resource() -> str:
    return "Echo!"


@mcp.resource("echo://{text}")
def echo_template(text: str) -> str:
    """Echo the input text"""
    return f"Echo: {text}"


@mcp.prompt("echo")
def echo_prompt(text: str) -> str:
    return text



================================================
File: examples/memory.py
================================================
# /// script
# dependencies = ["pydantic-ai-slim[openai]", "asyncpg", "numpy", "pgvector", "fastmcp"]
# ///

# uv pip install 'pydantic-ai-slim[openai]' asyncpg numpy pgvector fastmcp

"""
Recursive memory system inspired by the human brain's clustering of memories.
Uses OpenAI's 'text-embedding-3-small' model and pgvector for efficient similarity search.
"""

import asyncio
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Self

import asyncpg
import numpy as np
from openai import AsyncOpenAI
from pgvector.asyncpg import register_vector  # Import register_vector
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from fastmcp import FastMCP

MAX_DEPTH = 5
SIMILARITY_THRESHOLD = 0.7
DECAY_FACTOR = 0.99
REINFORCEMENT_FACTOR = 1.1

DEFAULT_LLM_MODEL = "openai:gpt-4o"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

mcp = FastMCP(
    "memory",
    dependencies=[
        "pydantic-ai-slim[openai]",
        "asyncpg",
        "numpy",
        "pgvector",
    ],
)

DB_DSN = "postgresql://postgres:postgres@localhost:54320/memory_db"
# reset memory with rm ~/.fastmcp/{USER}/memory/*
PROFILE_DIR = (
    Path.home() / ".fastmcp" / os.environ.get("USER", "anon") / "memory"
).resolve()
PROFILE_DIR.mkdir(parents=True, exist_ok=True)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_array = np.array(a, dtype=np.float64)
    b_array = np.array(b, dtype=np.float64)
    return np.dot(a_array, b_array) / (
        np.linalg.norm(a_array) * np.linalg.norm(b_array)
    )


async def do_ai[T](
    user_prompt: str,
    system_prompt: str,
    result_type: type[T] | Annotated,
    deps=None,
) -> T:
    agent = Agent(
        DEFAULT_LLM_MODEL,
        system_prompt=system_prompt,
        result_type=result_type,
    )
    result = await agent.run(user_prompt, deps=deps)
    return result.data


@dataclass
class Deps:
    openai: AsyncOpenAI
    pool: asyncpg.Pool


async def get_db_pool() -> asyncpg.Pool:
    async def init(conn):
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        await register_vector(conn)

    pool = await asyncpg.create_pool(DB_DSN, init=init)
    return pool


class MemoryNode(BaseModel):
    id: int | None = None
    content: str
    summary: str = ""
    importance: float = 1.0
    access_count: int = 0
    timestamp: float = Field(
        default_factory=lambda: datetime.now(timezone.utc).timestamp()
    )
    embedding: list[float]

    @classmethod
    async def from_content(cls, content: str, deps: Deps):
        embedding = await get_embedding(content, deps)
        return cls(content=content, embedding=embedding)

    async def save(self, deps: Deps):
        async with deps.pool.acquire() as conn:
            if self.id is None:
                result = await conn.fetchrow(
                    """
                    INSERT INTO memories (content, summary, importance, access_count, timestamp, embedding)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                    """,
                    self.content,
                    self.summary,
                    self.importance,
                    self.access_count,
                    self.timestamp,
                    self.embedding,
                )
                self.id = result["id"]
            else:
                await conn.execute(
                    """
                    UPDATE memories
                    SET content = $1, summary = $2, importance = $3,
                        access_count = $4, timestamp = $5, embedding = $6
                    WHERE id = $7
                    """,
                    self.content,
                    self.summary,
                    self.importance,
                    self.access_count,
                    self.timestamp,
                    self.embedding,
                    self.id,
                )

    async def merge_with(self, other: Self, deps: Deps):
        self.content = await do_ai(
            f"{self.content}\n\n{other.content}",
            "Combine the following two texts into a single, coherent text.",
            str,
            deps,
        )
        self.importance += other.importance
        self.access_count += other.access_count
        self.embedding = [(a + b) / 2 for a, b in zip(self.embedding, other.embedding)]
        self.summary = await do_ai(
            self.content, "Summarize the following text concisely.", str, deps
        )
        await self.save(deps)
        # Delete the merged node from the database
        if other.id is not None:
            await delete_memory(other.id, deps)

    def get_effective_importance(self):
        return self.importance * (1 + math.log(self.access_count + 1))


async def get_embedding(text: str, deps: Deps) -> list[float]:
    embedding_response = await deps.openai.embeddings.create(
        input=text,
        model=DEFAULT_EMBEDDING_MODEL,
    )
    return embedding_response.data[0].embedding


async def delete_memory(memory_id: int, deps: Deps):
    async with deps.pool.acquire() as conn:
        await conn.execute("DELETE FROM memories WHERE id = $1", memory_id)


async def add_memory(content: str, deps: Deps):
    new_memory = await MemoryNode.from_content(content, deps)
    await new_memory.save(deps)

    similar_memories = await find_similar_memories(new_memory.embedding, deps)
    for memory in similar_memories:
        if memory.id != new_memory.id:
            await new_memory.merge_with(memory, deps)

    await update_importance(new_memory.embedding, deps)

    await prune_memories(deps)

    return f"Remembered: {content}"


async def find_similar_memories(embedding: list[float], deps: Deps) -> list[MemoryNode]:
    async with deps.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, content, summary, importance, access_count, timestamp, embedding
            FROM memories
            ORDER BY embedding <-> $1
            LIMIT 5
            """,
            embedding,
        )
    memories = [
        MemoryNode(
            id=row["id"],
            content=row["content"],
            summary=row["summary"],
            importance=row["importance"],
            access_count=row["access_count"],
            timestamp=row["timestamp"],
            embedding=row["embedding"],
        )
        for row in rows
    ]
    return memories


async def update_importance(user_embedding: list[float], deps: Deps):
    async with deps.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, importance, access_count, embedding FROM memories"
        )
        for row in rows:
            memory_embedding = row["embedding"]
            similarity = cosine_similarity(user_embedding, memory_embedding)
            if similarity > SIMILARITY_THRESHOLD:
                new_importance = row["importance"] * REINFORCEMENT_FACTOR
                new_access_count = row["access_count"] + 1
            else:
                new_importance = row["importance"] * DECAY_FACTOR
                new_access_count = row["access_count"]
            await conn.execute(
                """
                UPDATE memories
                SET importance = $1, access_count = $2
                WHERE id = $3
                """,
                new_importance,
                new_access_count,
                row["id"],
            )


async def prune_memories(deps: Deps):
    async with deps.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, importance, access_count
            FROM memories
            ORDER BY importance DESC
            OFFSET $1
            """,
            MAX_DEPTH,
        )
        for row in rows:
            await conn.execute("DELETE FROM memories WHERE id = $1", row["id"])


async def display_memory_tree(deps: Deps) -> str:
    async with deps.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT content, summary, importance, access_count
            FROM memories
            ORDER BY importance DESC
            LIMIT $1
            """,
            MAX_DEPTH,
        )
    result = ""
    for row in rows:
        effective_importance = row["importance"] * (
            1 + math.log(row["access_count"] + 1)
        )
        summary = row["summary"] or row["content"]
        result += f"- {summary} (Importance: {effective_importance:.2f})\n"
    return result


@mcp.tool()
async def remember(
    contents: list[str] = Field(
        description="List of observations or memories to store"
    ),
):
    deps = Deps(openai=AsyncOpenAI(), pool=await get_db_pool())
    try:
        return "\n".join(
            await asyncio.gather(*[add_memory(content, deps) for content in contents])
        )
    finally:
        await deps.pool.close()


@mcp.tool()
async def read_profile() -> str:
    deps = Deps(openai=AsyncOpenAI(), pool=await get_db_pool())
    profile = await display_memory_tree(deps)
    await deps.pool.close()
    return profile


async def initialize_database():
    pool = await asyncpg.create_pool(
        "postgresql://postgres:postgres@localhost:54320/postgres"
    )
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'memory_db'
                AND pid <> pg_backend_pid();
            """)
            await conn.execute("DROP DATABASE IF EXISTS memory_db;")
            await conn.execute("CREATE DATABASE memory_db;")
    finally:
        await pool.close()

    pool = await asyncpg.create_pool(DB_DSN)
    try:
        async with pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            await register_vector(conn)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    summary TEXT,
                    importance REAL NOT NULL,
                    access_count INT NOT NULL,
                    timestamp DOUBLE PRECISION NOT NULL,
                    embedding vector(1536) NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_memories_embedding ON memories USING hnsw (embedding vector_l2_ops);
            """)
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(initialize_database())



================================================
File: examples/readme-quickstart.py
================================================
from fastmcp import FastMCP


# Create an MCP server
mcp = FastMCP("Demo")


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"



================================================
File: examples/screenshot.py
================================================
"""
FastMCP Screenshot Example

Give Claude a tool to capture and view screenshots.
"""

import io
from fastmcp import FastMCP, Image


# Create server
mcp = FastMCP("Screenshot Demo", dependencies=["pyautogui", "Pillow"])


@mcp.tool()
def take_screenshot() -> Image:
    """
    Take a screenshot of the user's screen and return it as an image. Use
    this tool anytime the user wants you to look at something they're doing.
    """
    import pyautogui

    buffer = io.BytesIO()

    # if the file exceeds ~1MB, it will be rejected by Claude
    screenshot = pyautogui.screenshot()
    screenshot.convert("RGB").save(buffer, format="JPEG", quality=60, optimize=True)
    return Image(data=buffer.getvalue(), format="jpeg")



================================================
File: examples/simple_echo.py
================================================
"""
FastMCP Echo Server
"""

from fastmcp import FastMCP


# Create server
mcp = FastMCP("Echo Server")


@mcp.tool()
def echo(text: str) -> str:
    """Echo the input text"""
    return text



================================================
File: examples/text_me.py
================================================
# /// script
# dependencies = ["fastmcp"]
# ///

"""
FastMCP Text Me Server
--------------------------------
This defines a simple FastMCP server that sends a text message to a phone number via https://surgemsg.com/.

To run this example, create a `.env` file with the following values:

SURGE_API_KEY=...
SURGE_ACCOUNT_ID=...
SURGE_MY_PHONE_NUMBER=...
SURGE_MY_FIRST_NAME=...
SURGE_MY_LAST_NAME=...

Visit https://surgemsg.com/ and click "Get Started" to obtain these values.
"""

from typing import Annotated
import httpx
from pydantic import BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict

from fastmcp import FastMCP


class SurgeSettings(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(
        env_prefix="SURGE_", env_file=".env"
    )

    api_key: str
    account_id: str
    my_phone_number: Annotated[
        str, BeforeValidator(lambda v: "+" + v if not v.startswith("+") else v)
    ]
    my_first_name: str
    my_last_name: str


# Create server
mcp = FastMCP("Text me")
surge_settings = SurgeSettings()  # type: ignore


@mcp.tool(name="textme", description="Send a text message to me")
def text_me(text_content: str) -> str:
    """Send a text message to a phone number via https://surgemsg.com/"""
    with httpx.Client() as client:
        response = client.post(
            "https://api.surgemsg.com/messages",
            headers={
                "Authorization": f"Bearer {surge_settings.api_key}",
                "Surge-Account": surge_settings.account_id,
                "Content-Type": "application/json",
            },
            json={
                "body": text_content,
                "conversation": {
                    "contact": {
                        "first_name": surge_settings.my_first_name,
                        "last_name": surge_settings.my_last_name,
                        "phone_number": surge_settings.my_phone_number,
                    }
                },
            },
        )
        response.raise_for_status()
        return f"Message sent: {text_content}"



================================================
File: src/fastmcp/__init__.py
================================================
"""FastMCP - A more ergonomic interface for MCP servers."""

from importlib.metadata import version
from .server import FastMCP, Context
from .utilities.types import Image

__version__ = version("fastmcp")
__all__ = ["FastMCP", "Context", "Image"]



================================================
File: src/fastmcp/exceptions.py
================================================
"""Custom exceptions for FastMCP."""


class FastMCPError(Exception):
    """Base error for FastMCP."""


class ValidationError(FastMCPError):
    """Error in validating parameters or return values."""


class ResourceError(FastMCPError):
    """Error in resource operations."""


class ToolError(FastMCPError):
    """Error in tool operations."""


class InvalidSignature(Exception):
    """Invalid signature for use with FastMCP."""



================================================
File: src/fastmcp/py.typed
================================================



================================================
File: src/fastmcp/server.py
================================================
"""FastMCP - A more ergonomic interface for MCP servers."""

import asyncio
import functools
import inspect
import json
import re
from itertools import chain
from typing import Any, Callable, Dict, Literal, Sequence, TypeVar, ParamSpec

import pydantic_core
from pydantic import Field
import uvicorn
from mcp.server import Server as MCPServer
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from mcp.shared.context import RequestContext
from mcp.types import (
    EmbeddedResource,
    GetPromptResult,
    ImageContent,
    TextContent,
)
from mcp.types import (
    Prompt as MCPPrompt,
    PromptArgument as MCPPromptArgument,
)
from mcp.types import (
    Resource as MCPResource,
)
from mcp.types import (
    ResourceTemplate as MCPResourceTemplate,
)
from mcp.types import (
    Tool as MCPTool,
)
from pydantic import BaseModel
from pydantic.networks import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from fastmcp.exceptions import ResourceError
from fastmcp.prompts import Prompt, PromptManager
from fastmcp.prompts.base import PromptResult
from fastmcp.resources import FunctionResource, Resource, ResourceManager
from fastmcp.tools import ToolManager
from fastmcp.utilities.logging import configure_logging, get_logger
from fastmcp.utilities.types import Image

logger = get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")
R_PromptResult = TypeVar("R_PromptResult", bound=PromptResult)


class Settings(BaseSettings):
    """FastMCP server settings.

    All settings can be configured via environment variables with the prefix FASTMCP_.
    For example, FASTMCP_DEBUG=true will set debug=True.
    """

    model_config: SettingsConfigDict = SettingsConfigDict(
        env_prefix="FASTMCP_",
        env_file=".env",
        extra="ignore",
    )

    # Server settings
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # HTTP settings
    host: str = "0.0.0.0"
    port: int = 8000

    # resource settings
    warn_on_duplicate_resources: bool = True

    # tool settings
    warn_on_duplicate_tools: bool = True

    # prompt settings
    warn_on_duplicate_prompts: bool = True

    dependencies: list[str] = Field(
        default_factory=list,
        description="List of dependencies to install in the server environment",
    )


class FastMCP:
    def __init__(self, name: str | None = None, **settings: Any):
        self.settings = Settings(**settings)
        self._mcp_server = MCPServer(name=name or "FastMCP")
        self._tool_manager = ToolManager(
            warn_on_duplicate_tools=self.settings.warn_on_duplicate_tools
        )
        self._resource_manager = ResourceManager(
            warn_on_duplicate_resources=self.settings.warn_on_duplicate_resources
        )
        self._prompt_manager = PromptManager(
            warn_on_duplicate_prompts=self.settings.warn_on_duplicate_prompts
        )
        self.dependencies = self.settings.dependencies

        # Set up MCP protocol handlers
        self._setup_handlers()

        # Configure logging
        configure_logging(self.settings.log_level)

    @property
    def name(self) -> str:
        return self._mcp_server.name

    def run(self, transport: Literal["stdio", "sse"] = "stdio") -> None:
        """Run the FastMCP server. Note this is a synchronous function.

        Args:
            transport: Transport protocol to use ("stdio" or "sse")
        """
        TRANSPORTS = Literal["stdio", "sse"]
        if transport not in TRANSPORTS.__args__:  # type: ignore
            raise ValueError(f"Unknown transport: {transport}")

        if transport == "stdio":
            asyncio.run(self.run_stdio_async())
        else:  # transport == "sse"
            asyncio.run(self.run_sse_async())

    def _setup_handlers(self) -> None:
        """Set up core MCP protocol handlers."""
        self._mcp_server.list_tools()(self.list_tools)
        self._mcp_server.call_tool()(self.call_tool)
        self._mcp_server.list_resources()(self.list_resources)
        self._mcp_server.read_resource()(self.read_resource)
        self._mcp_server.list_prompts()(self.list_prompts)
        self._mcp_server.get_prompt()(self.get_prompt)
        # TODO: This has not been added to MCP yet, see https://github.com/jlowin/fastmcp/issues/10
        # self._mcp_server.list_resource_templates()(self.list_resource_templates)

    async def list_tools(self) -> list[MCPTool]:
        """List all available tools."""
        tools = self._tool_manager.list_tools()
        return [
            MCPTool(
                name=info.name,
                description=info.description,
                inputSchema=info.parameters,
            )
            for info in tools
        ]

    def get_context(self) -> "Context":
        """
        Returns a Context object. Note that the context will only be valid
        during a request; outside a request, most methods will error.
        """
        try:
            request_context = self._mcp_server.request_context
        except LookupError:
            request_context = None
        return Context(request_context=request_context, fastmcp=self)

    async def call_tool(
        self, name: str, arguments: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Call a tool by name with arguments."""
        context = self.get_context()
        result = await self._tool_manager.call_tool(name, arguments, context=context)
        converted_result = _convert_to_content(result)
        return converted_result

    async def list_resources(self) -> list[MCPResource]:
        """List all available resources."""

        resources = self._resource_manager.list_resources()
        return [
            MCPResource(
                uri=resource.uri,
                name=resource.name or "",
                description=resource.description,
                mimeType=resource.mime_type,
            )
            for resource in resources
        ]

    async def list_resource_templates(self) -> list[MCPResourceTemplate]:
        templates = self._resource_manager.list_templates()
        return [
            MCPResourceTemplate(
                uriTemplate=template.uri_template,
                name=template.name,
                description=template.description,
            )
            for template in templates
        ]

    async def read_resource(self, uri: AnyUrl | str) -> str | bytes:
        """Read a resource by URI."""
        resource = await self._resource_manager.get_resource(uri)
        if not resource:
            raise ResourceError(f"Unknown resource: {uri}")

        try:
            return await resource.read()
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            raise ResourceError(str(e))

    def add_tool(
        self,
        fn: Callable,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Add a tool to the server.

        The tool function can optionally request a Context object by adding a parameter
        with the Context type annotation. See the @tool decorator for examples.

        Args:
            fn: The function to register as a tool
            name: Optional name for the tool (defaults to function name)
            description: Optional description of what the tool does
        """
        self._tool_manager.add_tool(fn, name=name, description=description)

    def tool(
        self, name: str | None = None, description: str | None = None
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Decorator to register a tool.

        Tools can optionally request a Context object by adding a parameter with the Context type annotation.
        The context provides access to MCP capabilities like logging, progress reporting, and resource access.

        Args:
            name: Optional name for the tool (defaults to function name)
            description: Optional description of what the tool does

        Example:
            @server.tool()
            def my_tool(x: int) -> str:
                return str(x)

            @server.tool()
            def tool_with_context(x: int, ctx: Context) -> str:
                ctx.info(f"Processing {x}")
                return str(x)

            @server.tool()
            async def async_tool(x: int, context: Context) -> str:
                await context.report_progress(50, 100)
                return str(x)
        """
        # Check if user passed function directly instead of calling decorator
        if callable(name):
            raise TypeError(
                "The @tool decorator was used incorrectly. "
                "Did you forget to call it? Use @tool() instead of @tool"
            )

        def decorator(fn: Callable[P, R]) -> Callable[P, R]:
            self.add_tool(fn, name=name, description=description)
            return fn

        return decorator

    def add_resource(self, resource: Resource) -> None:
        """Add a resource to the server.

        Args:
            resource: A Resource instance to add
        """
        self._resource_manager.add_resource(resource)

    def resource(
        self,
        uri: str,
        *,
        name: str | None = None,
        description: str | None = None,
        mime_type: str | None = None,
    ) -> Callable[[Callable[P, R]], Callable[P, R]]:
        """Decorator to register a function as a resource.

        The function will be called when the resource is read to generate its content.
        The function can return:
        - str for text content
        - bytes for binary content
        - other types will be converted to JSON

        If the URI contains parameters (e.g. "resource://{param}") or the function
        has parameters, it will be registered as a template resource.

        Args:
            uri: URI for the resource (e.g. "resource://my-resource" or "resource://{param}")
            name: Optional name for the resource
            description: Optional description of the resource
            mime_type: Optional MIME type for the resource

        Example:
            @server.resource("resource://my-resource")
            def get_data() -> str:
                return "Hello, world!"

            @server.resource("resource://{city}/weather")
            def get_weather(city: str) -> str:
                return f"Weather for {city}"
        """
        # Check if user passed function directly instead of calling decorator
        if callable(uri):
            raise TypeError(
                "The @resource decorator was used incorrectly. "
                "Did you forget to call it? Use @resource('uri') instead of @resource"
            )

        def decorator(fn: Callable[P, R]) -> Callable[P, R]:
            @functools.wraps(fn)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                return fn(*args, **kwargs)

            # Check if this should be a template
            has_uri_params = "{" in uri and "}" in uri
            has_func_params = bool(inspect.signature(fn).parameters)

            if has_uri_params or has_func_params:
                # Validate that URI params match function params
                uri_params = set(re.findall(r"{(\w+)}", uri))
                func_params = set(inspect.signature(fn).parameters.keys())

                if uri_params != func_params:
                    raise ValueError(
                        f"Mismatch between URI parameters {uri_params} "
                        f"and function parameters {func_params}"
                    )

                # Register as template
                self._resource_manager.add_template(
                    wrapper,
                    uri_template=uri,
                    name=name,
                    description=description,
                    mime_type=mime_type or "text/plain",
                )
            else:
                # Register as regular resource
                resource = FunctionResource(
                    uri=AnyUrl(uri),
                    name=name,
                    description=description,
                    mime_type=mime_type or "text/plain",
                    fn=wrapper,
                )
                self.add_resource(resource)
            return wrapper

        return decorator

    def add_prompt(self, prompt: Prompt) -> None:
        """Add a prompt to the server.

        Args:
            prompt: A Prompt instance to add
        """
        self._prompt_manager.add_prompt(prompt)

    def prompt(
        self, name: str | None = None, description: str | None = None
    ) -> Callable[[Callable[P, R_PromptResult]], Callable[P, R_PromptResult]]:
        """Decorator to register a prompt.

        Args:
            name: Optional name for the prompt (defaults to function name)
            description: Optional description of what the prompt does

        Example:
            @server.prompt()
            def analyze_table(table_name: str) -> list[Message]:
                schema = read_table_schema(table_name)
                return [
                    {
                        "role": "user",
                        "content": f"Analyze this schema:\n{schema}"
                    }
                ]

            @server.prompt()
            async def analyze_file(path: str) -> list[Message]:
                content = await read_file(path)
                return [
                    {
                        "role": "user",
                        "content": {
                            "type": "resource",
                            "resource": {
                                "uri": f"file://{path}",
                                "text": content
                            }
                        }
                    }
                ]
        """
        # Check if user passed function directly instead of calling decorator
        if callable(name):
            raise TypeError(
                "The @prompt decorator was used incorrectly. "
                "Did you forget to call it? Use @prompt() instead of @prompt"
            )

        def decorator(func: Callable[P, R_PromptResult]) -> Callable[P, R_PromptResult]:
            prompt = Prompt.from_function(func, name=name, description=description)
            self.add_prompt(prompt)
            return func

        return decorator

    async def run_stdio_async(self) -> None:
        """Run the server using stdio transport."""
        async with stdio_server() as (read_stream, write_stream):
            await self._mcp_server.run(
                read_stream,
                write_stream,
                self._mcp_server.create_initialization_options(),
            )

    async def run_sse_async(self) -> None:
        """Run the server using SSE transport."""
        from starlette.applications import Starlette
        from starlette.routing import Route, Mount

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await self._mcp_server.run(
                    streams[0],
                    streams[1],
                    self._mcp_server.create_initialization_options(),
                )

        starlette_app = Starlette(
            debug=self.settings.debug,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        config = uvicorn.Config(
            starlette_app,
            host=self.settings.host,
            port=self.settings.port,
            log_level=self.settings.log_level.lower(),
        )
        server = uvicorn.Server(config)
        await server.serve()

    async def list_prompts(self) -> list[MCPPrompt]:
        """List all available prompts."""
        prompts = self._prompt_manager.list_prompts()
        return [
            MCPPrompt(
                name=prompt.name,
                description=prompt.description,
                arguments=[
                    MCPPromptArgument(
                        name=arg.name,
                        description=arg.description,
                        required=arg.required,
                    )
                    for arg in (prompt.arguments or [])
                ],
            )
            for prompt in prompts
        ]

    async def get_prompt(
        self, name: str, arguments: Dict[str, Any] | None = None
    ) -> GetPromptResult:
        """Get a prompt by name with arguments."""
        try:
            messages = await self._prompt_manager.render_prompt(name, arguments)

            return GetPromptResult(messages=pydantic_core.to_jsonable_python(messages))
        except Exception as e:
            logger.error(f"Error getting prompt {name}: {e}")
            raise ValueError(str(e))


def _convert_to_content(
    result: Any,
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Convert a result to a sequence of content objects."""
    if result is None:
        return []

    if isinstance(result, (TextContent, ImageContent, EmbeddedResource)):
        return [result]

    if isinstance(result, Image):
        return [result.to_image_content()]

    if isinstance(result, (list, tuple)):
        return list(chain.from_iterable(_convert_to_content(item) for item in result))

    if not isinstance(result, str):
        try:
            result = json.dumps(pydantic_core.to_jsonable_python(result))
        except Exception:
            result = str(result)

    return [TextContent(type="text", text=result)]


class Context(BaseModel):
    """Context object providing access to MCP capabilities.

    This provides a cleaner interface to MCP's RequestContext functionality.
    It gets injected into tool and resource functions that request it via type hints.

    To use context in a tool function, add a parameter with the Context type annotation:

    ```python
    @server.tool()
    def my_tool(x: int, ctx: Context) -> str:
        # Log messages to the client
        ctx.info(f"Processing {x}")
        ctx.debug("Debug info")
        ctx.warning("Warning message")
        ctx.error("Error message")

        # Report progress
        ctx.report_progress(50, 100)

        # Access resources
        data = ctx.read_resource("resource://data")

        # Get request info
        request_id = ctx.request_id
        client_id = ctx.client_id

        return str(x)
    ```

    The context parameter name can be anything as long as it's annotated with Context.
    The context is optional - tools that don't need it can omit the parameter.
    """

    _request_context: RequestContext | None
    _fastmcp: FastMCP | None

    def __init__(
        self,
        *,
        request_context: RequestContext | None = None,
        fastmcp: FastMCP | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._request_context = request_context
        self._fastmcp = fastmcp

    @property
    def fastmcp(self) -> FastMCP:
        """Access to the FastMCP server."""
        if self._fastmcp is None:
            raise ValueError("Context is not available outside of a request")
        return self._fastmcp

    @property
    def request_context(self) -> RequestContext:
        """Access to the underlying request context."""
        if self._request_context is None:
            raise ValueError("Context is not available outside of a request")
        return self._request_context

    async def report_progress(
        self, progress: float, total: float | None = None
    ) -> None:
        """Report progress for the current operation.

        Args:
            progress: Current progress value e.g. 24
            total: Optional total value e.g. 100
        """

        progress_token = (
            self.request_context.meta.progressToken
            if self.request_context.meta
            else None
        )

        if not progress_token:
            return

        await self.request_context.session.send_progress_notification(
            progress_token=progress_token, progress=progress, total=total
        )

    async def read_resource(self, uri: str | AnyUrl) -> str | bytes:
        """Read a resource by URI.

        Args:
            uri: Resource URI to read

        Returns:
            The resource content as either text or bytes
        """
        assert (
            self._fastmcp is not None
        ), "Context is not available outside of a request"
        return await self._fastmcp.read_resource(uri)

    def log(
        self,
        level: Literal["debug", "info", "warning", "error"],
        message: str,
        *,
        logger_name: str | None = None,
    ) -> None:
        """Send a log message to the client.

        Args:
            level: Log level (debug, info, warning, error)
            message: Log message
            logger_name: Optional logger name
            **extra: Additional structured data to include
        """
        self.request_context.session.send_log_message(
            level=level, data=message, logger=logger_name
        )

    @property
    def client_id(self) -> str | None:
        """Get the client ID if available."""
        return (
            getattr(self.request_context.meta, "client_id", None)
            if self.request_context.meta
            else None
        )

    @property
    def request_id(self) -> str:
        """Get the unique ID for this request."""
        return str(self.request_context.request_id)

    @property
    def session(self):
        """Access to the underlying session for advanced usage."""
        return self.request_context.session

    # Convenience methods for common log levels
    def debug(self, message: str, **extra: Any) -> None:
        """Send a debug log message."""
        self.log("debug", message, **extra)

    def info(self, message: str, **extra: Any) -> None:
        """Send an info log message."""
        self.log("info", message, **extra)

    def warning(self, message: str, **extra: Any) -> None:
        """Send a warning log message."""
        self.log("warning", message, **extra)

    def error(self, message: str, **extra: Any) -> None:
        """Send an error log message."""
        self.log("error", message, **extra)



================================================
File: src/fastmcp/cli/__init__.py
================================================
"""FastMCP CLI package."""

from .cli import app


if __name__ == "__main__":
    app()



================================================
File: src/fastmcp/cli/claude.py
================================================
"""Claude app integration utilities."""

import json
import sys
from pathlib import Path
from typing import Optional, Dict

from ..utilities.logging import get_logger

logger = get_logger(__name__)


def get_claude_config_path() -> Path | None:
    """Get the Claude config directory based on platform."""
    if sys.platform == "win32":
        path = Path(Path.home(), "AppData", "Roaming", "Claude")
    elif sys.platform == "darwin":
        path = Path(Path.home(), "Library", "Application Support", "Claude")
    else:
        return None

    if path.exists():
        return path
    return None


def update_claude_config(
    file_spec: str,
    server_name: str,
    *,
    with_editable: Optional[Path] = None,
    with_packages: Optional[list[str]] = None,
    env_vars: Optional[Dict[str, str]] = None,
) -> bool:
    """Add or update a FastMCP server in Claude's configuration.

    Args:
        file_spec: Path to the server file, optionally with :object suffix
        server_name: Name for the server in Claude's config
        with_editable: Optional directory to install in editable mode
        with_packages: Optional list of additional packages to install
        env_vars: Optional dictionary of environment variables. These are merged with
            any existing variables, with new values taking precedence.

    Raises:
        RuntimeError: If Claude Desktop's config directory is not found, indicating
            Claude Desktop may not be installed or properly set up.
    """
    config_dir = get_claude_config_path()
    if not config_dir:
        raise RuntimeError(
            "Claude Desktop config directory not found. Please ensure Claude Desktop "
            "is installed and has been run at least once to initialize its configuration."
        )

    config_file = config_dir / "claude_desktop_config.json"
    if not config_file.exists():
        try:
            config_file.write_text("{}")
        except Exception as e:
            logger.error(
                "Failed to create Claude config file",
                extra={
                    "error": str(e),
                    "config_file": str(config_file),
                },
            )
            return False

    try:
        config = json.loads(config_file.read_text())
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Always preserve existing env vars and merge with new ones
        if (
            server_name in config["mcpServers"]
            and "env" in config["mcpServers"][server_name]
        ):
            existing_env = config["mcpServers"][server_name]["env"]
            if env_vars:
                # New vars take precedence over existing ones
                env_vars = {**existing_env, **env_vars}
            else:
                env_vars = existing_env

        # Build uv run command
        args = ["run"]

        # Collect all packages in a set to deduplicate
        packages = {"fastmcp"}
        if with_packages:
            packages.update(pkg for pkg in with_packages if pkg)

        # Add all packages with --with
        for pkg in sorted(packages):
            args.extend(["--with", pkg])

        if with_editable:
            args.extend(["--with-editable", str(with_editable)])

        # Convert file path to absolute before adding to command
        # Split off any :object suffix first
        if ":" in file_spec:
            file_path, server_object = file_spec.rsplit(":", 1)
            file_spec = f"{Path(file_path).resolve()}:{server_object}"
        else:
            file_spec = str(Path(file_spec).resolve())

        # Add fastmcp run command
        args.extend(["fastmcp", "run", file_spec])

        server_config = {
            "command": "uv",
            "args": args,
        }

        # Add environment variables if specified
        if env_vars:
            server_config["env"] = env_vars

        config["mcpServers"][server_name] = server_config

        config_file.write_text(json.dumps(config, indent=2))
        logger.info(
            f"Added server '{server_name}' to Claude config",
            extra={"config_file": str(config_file)},
        )
        return True
    except Exception as e:
        logger.error(
            "Failed to update Claude config",
            extra={
                "error": str(e),
                "config_file": str(config_file),
            },
        )
        return False



================================================
File: src/fastmcp/cli/cli.py
================================================
"""FastMCP CLI tools."""

import importlib.metadata
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

import dotenv
import typer
from typing_extensions import Annotated

from fastmcp.cli import claude
from fastmcp.utilities.logging import get_logger

logger = get_logger("cli")

app = typer.Typer(
    name="fastmcp",
    help="FastMCP development tools",
    add_completion=False,
    no_args_is_help=True,  # Show help if no args provided
)


def _get_npx_command():
    """Get the correct npx command for the current platform."""
    if sys.platform == "win32":
        # Try both npx.cmd and npx.exe on Windows
        for cmd in ["npx.cmd", "npx.exe", "npx"]:
            try:
                subprocess.run(
                    [cmd, "--version"], check=True, capture_output=True, shell=True
                )
                return cmd
            except subprocess.CalledProcessError:
                continue
        return None
    return "npx"  # On Unix-like systems, just use npx


def _parse_env_var(env_var: str) -> Tuple[str, str]:
    """Parse environment variable string in format KEY=VALUE."""
    if "=" not in env_var:
        logger.error(
            f"Invalid environment variable format: {env_var}. Must be KEY=VALUE"
        )
        sys.exit(1)
    key, value = env_var.split("=", 1)
    return key.strip(), value.strip()


def _build_uv_command(
    file_spec: str,
    with_editable: Optional[Path] = None,
    with_packages: Optional[list[str]] = None,
) -> list[str]:
    """Build the uv run command that runs a FastMCP server through fastmcp run."""
    cmd = ["uv"]

    cmd.extend(["run", "--with", "fastmcp"])

    if with_editable:
        cmd.extend(["--with-editable", str(with_editable)])

    if with_packages:
        for pkg in with_packages:
            if pkg:
                cmd.extend(["--with", pkg])

    # Add fastmcp run command
    cmd.extend(["fastmcp", "run", file_spec])
    return cmd


def _parse_file_path(file_spec: str) -> Tuple[Path, Optional[str]]:
    """Parse a file path that may include a server object specification.

    Args:
        file_spec: Path to file, optionally with :object suffix

    Returns:
        Tuple of (file_path, server_object)
    """
    # First check if we have a Windows path (e.g., C:\...)
    has_windows_drive = len(file_spec) > 1 and file_spec[1] == ":"

    # Split on the last colon, but only if it's not part of the Windows drive letter
    # and there's actually another colon in the string after the drive letter
    if ":" in (file_spec[2:] if has_windows_drive else file_spec):
        file_str, server_object = file_spec.rsplit(":", 1)
    else:
        file_str, server_object = file_spec, None

    # Resolve the file path
    file_path = Path(file_str).expanduser().resolve()
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    if not file_path.is_file():
        logger.error(f"Not a file: {file_path}")
        sys.exit(1)

    return file_path, server_object


def _import_server(file: Path, server_object: Optional[str] = None):
    """Import a FastMCP server from a file.

    Args:
        file: Path to the file
        server_object: Optional object name in format "module:object" or just "object"

    Returns:
        The server object
    """
    # Add parent directory to Python path so imports can be resolved
    file_dir = str(file.parent)
    if file_dir not in sys.path:
        sys.path.insert(0, file_dir)

    # Import the module
    spec = importlib.util.spec_from_file_location("server_module", file)
    if not spec or not spec.loader:
        logger.error("Could not load module", extra={"file": str(file)})
        sys.exit(1)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # If no object specified, try common server names
    if not server_object:
        # Look for the most common server object names
        for name in ["mcp", "server", "app"]:
            if hasattr(module, name):
                return getattr(module, name)

        logger.error(
            f"No server object found in {file}. Please either:\n"
            "1. Use a standard variable name (mcp, server, or app)\n"
            "2. Specify the object name with file:object syntax",
            extra={"file": str(file)},
        )
        sys.exit(1)

    # Handle module:object syntax
    if ":" in server_object:
        module_name, object_name = server_object.split(":", 1)
        try:
            server_module = importlib.import_module(module_name)
            server = getattr(server_module, object_name, None)
        except ImportError:
            logger.error(
                f"Could not import module '{module_name}'",
                extra={"file": str(file)},
            )
            sys.exit(1)
    else:
        # Just object name
        server = getattr(module, server_object, None)

    if server is None:
        logger.error(
            f"Server object '{server_object}' not found",
            extra={"file": str(file)},
        )
        sys.exit(1)

    return server


@app.command()
def version() -> None:
    """Show the FastMCP version."""
    try:
        version = importlib.metadata.version("fastmcp")
        print(f"FastMCP version {version}")
    except importlib.metadata.PackageNotFoundError:
        print("FastMCP version unknown (package not installed)")
        sys.exit(1)


@app.command()
def dev(
    file_spec: str = typer.Argument(
        ...,
        help="Python file to run, optionally with :object suffix",
    ),
    with_editable: Annotated[
        Optional[Path],
        typer.Option(
            "--with-editable",
            "-e",
            help="Directory containing pyproject.toml to install in editable mode",
            exists=True,
            file_okay=False,
            resolve_path=True,
        ),
    ] = None,
    with_packages: Annotated[
        list[str],
        typer.Option(
            "--with",
            help="Additional packages to install",
        ),
    ] = [],
) -> None:
    """Run a FastMCP server with the MCP Inspector."""
    file, server_object = _parse_file_path(file_spec)

    logger.debug(
        "Starting dev server",
        extra={
            "file": str(file),
            "server_object": server_object,
            "with_editable": str(with_editable) if with_editable else None,
            "with_packages": with_packages,
        },
    )

    try:
        # Import server to get dependencies
        server = _import_server(file, server_object)
        if hasattr(server, "dependencies"):
            with_packages = list(set(with_packages + server.dependencies))

        uv_cmd = _build_uv_command(file_spec, with_editable, with_packages)

        # Get the correct npx command
        npx_cmd = _get_npx_command()
        if not npx_cmd:
            logger.error(
                "npx not found. Please ensure Node.js and npm are properly installed "
                "and added to your system PATH."
            )
            sys.exit(1)

        # Run the MCP Inspector command with shell=True on Windows
        shell = sys.platform == "win32"
        process = subprocess.run(
            [npx_cmd, "@modelcontextprotocol/inspector"] + uv_cmd,
            check=True,
            shell=shell,
            env=dict(os.environ.items()),  # Convert to list of tuples for env update
        )
        sys.exit(process.returncode)
    except subprocess.CalledProcessError as e:
        logger.error(
            "Dev server failed",
            extra={
                "file": str(file),
                "error": str(e),
                "returncode": e.returncode,
            },
        )
        sys.exit(e.returncode)
    except FileNotFoundError:
        logger.error(
            "npx not found. Please ensure Node.js and npm are properly installed "
            "and added to your system PATH. You may need to restart your terminal "
            "after installation.",
            extra={"file": str(file)},
        )
        sys.exit(1)


@app.command()
def run(
    file_spec: str = typer.Argument(
        ...,
        help="Python file to run, optionally with :object suffix",
    ),
    transport: Annotated[
        Optional[str],
        typer.Option(
            "--transport",
            "-t",
            help="Transport protocol to use (stdio or sse)",
        ),
    ] = None,
) -> None:
    """Run a FastMCP server.

    The server can be specified in two ways:
    1. Module approach: server.py - runs the module directly, expecting a server.run() call
    2. Import approach: server.py:app - imports and runs the specified server object

    Note: This command runs the server directly. You are responsible for ensuring
    all dependencies are available. For dependency management, use fastmcp install
    or fastmcp dev instead.
    """
    file, server_object = _parse_file_path(file_spec)

    logger.debug(
        "Running server",
        extra={
            "file": str(file),
            "server_object": server_object,
            "transport": transport,
        },
    )

    try:
        # Import and get server object
        server = _import_server(file, server_object)

        # Run the server
        kwargs = {}
        if transport:
            kwargs["transport"] = transport

        server.run(**kwargs)

    except Exception as e:
        logger.error(
            f"Failed to run server: {e}",
            extra={
                "file": str(file),
                "error": str(e),
            },
        )
        sys.exit(1)


@app.command()
def install(
    file_spec: str = typer.Argument(
        ...,
        help="Python file to run, optionally with :object suffix",
    ),
    server_name: Annotated[
        Optional[str],
        typer.Option(
            "--name",
            "-n",
            help="Custom name for the server (defaults to server's name attribute or file name)",
        ),
    ] = None,
    with_editable: Annotated[
        Optional[Path],
        typer.Option(
            "--with-editable",
            "-e",
            help="Directory containing pyproject.toml to install in editable mode",
            exists=True,
            file_okay=False,
            resolve_path=True,
        ),
    ] = None,
    with_packages: Annotated[
        list[str],
        typer.Option(
            "--with",
            help="Additional packages to install",
        ),
    ] = [],
    env_vars: Annotated[
        list[str],
        typer.Option(
            "--env-var",
            "-e",
            help="Environment variables in KEY=VALUE format",
        ),
    ] = [],
    env_file: Annotated[
        Optional[Path],
        typer.Option(
            "--env-file",
            "-f",
            help="Load environment variables from a .env file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
) -> None:
    """Install a FastMCP server in the Claude desktop app.

    Environment variables are preserved once added and only updated if new values
    are explicitly provided.
    """
    file, server_object = _parse_file_path(file_spec)

    logger.debug(
        "Installing server",
        extra={
            "file": str(file),
            "server_name": server_name,
            "server_object": server_object,
            "with_editable": str(with_editable) if with_editable else None,
            "with_packages": with_packages,
        },
    )

    if not claude.get_claude_config_path():
        logger.error("Claude app not found")
        sys.exit(1)

    # Try to import server to get its name, but fall back to file name if dependencies missing
    name = server_name
    server = None
    if not name:
        try:
            server = _import_server(file, server_object)
            name = server.name
        except (ImportError, ModuleNotFoundError) as e:
            logger.debug(
                "Could not import server (likely missing dependencies), using file name",
                extra={"error": str(e)},
            )
            name = file.stem

    # Get server dependencies if available
    server_dependencies = getattr(server, "dependencies", []) if server else []
    if server_dependencies:
        with_packages = list(set(with_packages + server_dependencies))

    # Process environment variables if provided
    env_dict: Optional[Dict[str, str]] = None
    if env_file or env_vars:
        env_dict = {}
        # Load from .env file if specified
        if env_file:
            try:
                env_dict |= {
                    k: v
                    for k, v in dotenv.dotenv_values(env_file).items()
                    if v is not None
                }
            except Exception as e:
                logger.error(f"Failed to load .env file: {e}")
                sys.exit(1)

        # Add command line environment variables
        for env_var in env_vars:
            key, value = _parse_env_var(env_var)
            env_dict[key] = value

    if claude.update_claude_config(
        file_spec,
        name,
        with_editable=with_editable,
        with_packages=with_packages,
        env_vars=env_dict,
    ):
        logger.info(f"Successfully installed {name} in Claude app")
    else:
        logger.error(f"Failed to install {name} in Claude app")
        sys.exit(1)



================================================
File: src/fastmcp/prompts/__init__.py
================================================
from .base import Prompt
from .manager import PromptManager

__all__ = ["Prompt", "PromptManager"]



================================================
File: src/fastmcp/prompts/base.py
================================================
"""Base classes for FastMCP prompts."""

import json
from typing import Any, Callable, Dict, Literal, Optional, Sequence, Awaitable
import inspect

from pydantic import BaseModel, Field, TypeAdapter, validate_call
from mcp.types import TextContent, ImageContent, EmbeddedResource
import pydantic_core

CONTENT_TYPES = TextContent | ImageContent | EmbeddedResource


class Message(BaseModel):
    """Base class for all prompt messages."""

    role: Literal["user", "assistant"]
    content: CONTENT_TYPES

    def __init__(self, content: str | CONTENT_TYPES, **kwargs):
        if isinstance(content, str):
            content = TextContent(type="text", text=content)
        super().__init__(content=content, **kwargs)


class UserMessage(Message):
    """A message from the user."""

    role: Literal["user"] = "user"

    def __init__(self, content: str | CONTENT_TYPES, **kwargs):
        super().__init__(content=content, **kwargs)


class AssistantMessage(Message):
    """A message from the assistant."""

    role: Literal["assistant"] = "assistant"

    def __init__(self, content: str | CONTENT_TYPES, **kwargs):
        super().__init__(content=content, **kwargs)


message_validator = TypeAdapter(UserMessage | AssistantMessage)

SyncPromptResult = (
    str | Message | dict[str, Any] | Sequence[str | Message | dict[str, Any]]
)
PromptResult = SyncPromptResult | Awaitable[SyncPromptResult]


class PromptArgument(BaseModel):
    """An argument that can be passed to a prompt."""

    name: str = Field(description="Name of the argument")
    description: str | None = Field(
        None, description="Description of what the argument does"
    )
    required: bool = Field(
        default=False, description="Whether the argument is required"
    )


class Prompt(BaseModel):
    """A prompt template that can be rendered with parameters."""

    name: str = Field(description="Name of the prompt")
    description: str | None = Field(
        None, description="Description of what the prompt does"
    )
    arguments: list[PromptArgument] | None = Field(
        None, description="Arguments that can be passed to the prompt"
    )
    fn: Callable = Field(exclude=True)

    @classmethod
    def from_function(
        cls,
        fn: Callable[..., PromptResult],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "Prompt":
        """Create a Prompt from a function.

        The function can return:
        - A string (converted to a message)
        - A Message object
        - A dict (converted to a message)
        - A sequence of any of the above
        """
        func_name = name or fn.__name__

        if func_name == "<lambda>":
            raise ValueError("You must provide a name for lambda functions")

        # Get schema from TypeAdapter - will fail if function isn't properly typed
        parameters = TypeAdapter(fn).json_schema()

        # Convert parameters to PromptArguments
        arguments = []
        if "properties" in parameters:
            for param_name, param in parameters["properties"].items():
                required = param_name in parameters.get("required", [])
                arguments.append(
                    PromptArgument(
                        name=param_name,
                        description=param.get("description"),
                        required=required,
                    )
                )

        # ensure the arguments are properly cast
        fn = validate_call(fn)

        return cls(
            name=func_name,
            description=description or fn.__doc__ or "",
            arguments=arguments,
            fn=fn,
        )

    async def render(self, arguments: Optional[Dict[str, Any]] = None) -> list[Message]:
        """Render the prompt with arguments."""
        # Validate required arguments
        if self.arguments:
            required = {arg.name for arg in self.arguments if arg.required}
            provided = set(arguments or {})
            missing = required - provided
            if missing:
                raise ValueError(f"Missing required arguments: {missing}")

        try:
            # Call function and check if result is a coroutine
            result = self.fn(**(arguments or {}))
            if inspect.iscoroutine(result):
                result = await result

            # Validate messages
            if not isinstance(result, (list, tuple)):
                result = [result]

            # Convert result to messages
            messages = []
            for msg in result:
                try:
                    if isinstance(msg, Message):
                        messages.append(msg)
                    elif isinstance(msg, dict):
                        msg = message_validator.validate_python(msg)
                        messages.append(msg)
                    elif isinstance(msg, str):
                        messages.append(
                            UserMessage(content=TextContent(type="text", text=msg))
                        )
                    else:
                        msg = json.dumps(pydantic_core.to_jsonable_python(msg))
                        messages.append(Message(role="user", content=msg))
                except Exception:
                    raise ValueError(
                        f"Could not convert prompt result to message: {msg}"
                    )

            return messages
        except Exception as e:
            raise ValueError(f"Error rendering prompt {self.name}: {e}")



================================================
File: src/fastmcp/prompts/manager.py
================================================
"""Prompt management functionality."""

from typing import Any, Dict, Optional

from fastmcp.prompts.base import Message, Prompt
from fastmcp.utilities.logging import get_logger

logger = get_logger(__name__)


class PromptManager:
    """Manages FastMCP prompts."""

    def __init__(self, warn_on_duplicate_prompts: bool = True):
        self._prompts: Dict[str, Prompt] = {}
        self.warn_on_duplicate_prompts = warn_on_duplicate_prompts

    def get_prompt(self, name: str) -> Optional[Prompt]:
        """Get prompt by name."""
        return self._prompts.get(name)

    def list_prompts(self) -> list[Prompt]:
        """List all registered prompts."""
        return list(self._prompts.values())

    def add_prompt(
        self,
        prompt: Prompt,
    ) -> Prompt:
        """Add a prompt to the manager."""

        # Check for duplicates
        existing = self._prompts.get(prompt.name)
        if existing:
            if self.warn_on_duplicate_prompts:
                logger.warning(f"Prompt already exists: {prompt.name}")
            return existing

        self._prompts[prompt.name] = prompt
        return prompt

    async def render_prompt(
        self, name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> list[Message]:
        """Render a prompt by name with arguments."""
        prompt = self.get_prompt(name)
        if not prompt:
            raise ValueError(f"Unknown prompt: {name}")

        return await prompt.render(arguments)



================================================
File: src/fastmcp/prompts/prompt_manager.py
================================================
"""Prompt management functionality."""

from typing import Dict, Optional


from fastmcp.prompts.base import Prompt
from fastmcp.utilities.logging import get_logger

logger = get_logger(__name__)


class PromptManager:
    """Manages FastMCP prompts."""

    def __init__(self, warn_on_duplicate_prompts: bool = True):
        self._prompts: Dict[str, Prompt] = {}
        self.warn_on_duplicate_prompts = warn_on_duplicate_prompts

    def add_prompt(self, prompt: Prompt) -> Prompt:
        """Add a prompt to the manager."""
        logger.debug(f"Adding prompt: {prompt.name}")
        existing = self._prompts.get(prompt.name)
        if existing:
            if self.warn_on_duplicate_prompts:
                logger.warning(f"Prompt already exists: {prompt.name}")
            return existing
        self._prompts[prompt.name] = prompt
        return prompt

    def get_prompt(self, name: str) -> Optional[Prompt]:
        """Get prompt by name."""
        return self._prompts.get(name)

    def list_prompts(self) -> list[Prompt]:
        """List all registered prompts."""
        return list(self._prompts.values())



================================================
File: src/fastmcp/resources/__init__.py
================================================
from .base import Resource
from .types import (
    TextResource,
    BinaryResource,
    FunctionResource,
    FileResource,
    HttpResource,
    DirectoryResource,
)
from .templates import ResourceTemplate
from .resource_manager import ResourceManager

__all__ = [
    "Resource",
    "TextResource",
    "BinaryResource",
    "FunctionResource",
    "FileResource",
    "HttpResource",
    "DirectoryResource",
    "ResourceTemplate",
    "ResourceManager",
]



================================================
File: src/fastmcp/resources/base.py
================================================
"""Base classes and interfaces for FastMCP resources."""

import abc
from typing import Union, Annotated

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    UrlConstraints,
    ValidationInfo,
    field_validator,
)


class Resource(BaseModel, abc.ABC):
    """Base class for all resources."""

    model_config = ConfigDict(validate_default=True)

    uri: Annotated[AnyUrl, UrlConstraints(host_required=False)] = Field(
        default=..., description="URI of the resource"
    )
    name: str | None = Field(description="Name of the resource", default=None)
    description: str | None = Field(
        description="Description of the resource", default=None
    )
    mime_type: str = Field(
        default="text/plain",
        description="MIME type of the resource content",
        pattern=r"^[a-zA-Z0-9]+/[a-zA-Z0-9\-+.]+$",
    )

    @field_validator("name", mode="before")
    @classmethod
    def set_default_name(cls, name: str | None, info: ValidationInfo) -> str:
        """Set default name from URI if not provided."""
        if name:
            return name
        if uri := info.data.get("uri"):
            return str(uri)
        raise ValueError("Either name or uri must be provided")

    @abc.abstractmethod
    async def read(self) -> Union[str, bytes]:
        """Read the resource content."""
        pass



================================================
File: src/fastmcp/resources/resource_manager.py
================================================
"""Resource manager functionality."""

from typing import Callable, Dict, Optional, Union

from pydantic import AnyUrl

from fastmcp.resources.base import Resource
from fastmcp.resources.templates import ResourceTemplate
from fastmcp.utilities.logging import get_logger

logger = get_logger(__name__)


class ResourceManager:
    """Manages FastMCP resources."""

    def __init__(self, warn_on_duplicate_resources: bool = True):
        self._resources: Dict[str, Resource] = {}
        self._templates: Dict[str, ResourceTemplate] = {}
        self.warn_on_duplicate_resources = warn_on_duplicate_resources

    def add_resource(self, resource: Resource) -> Resource:
        """Add a resource to the manager.

        Args:
            resource: A Resource instance to add

        Returns:
            The added resource. If a resource with the same URI already exists,
            returns the existing resource.
        """
        logger.debug(
            "Adding resource",
            extra={
                "uri": resource.uri,
                "type": type(resource).__name__,
                "name": resource.name,
            },
        )
        existing = self._resources.get(str(resource.uri))
        if existing:
            if self.warn_on_duplicate_resources:
                logger.warning(f"Resource already exists: {resource.uri}")
            return existing
        self._resources[str(resource.uri)] = resource
        return resource

    def add_template(
        self,
        fn: Callable,
        uri_template: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> ResourceTemplate:
        """Add a template from a function."""
        template = ResourceTemplate.from_function(
            fn,
            uri_template=uri_template,
            name=name,
            description=description,
            mime_type=mime_type,
        )
        self._templates[template.uri_template] = template
        return template

    async def get_resource(self, uri: Union[AnyUrl, str]) -> Optional[Resource]:
        """Get resource by URI, checking concrete resources first, then templates."""
        uri_str = str(uri)
        logger.debug("Getting resource", extra={"uri": uri_str})

        # First check concrete resources
        if resource := self._resources.get(uri_str):
            return resource

        # Then check templates
        for template in self._templates.values():
            if params := template.matches(uri_str):
                try:
                    return await template.create_resource(uri_str, params)
                except Exception as e:
                    raise ValueError(f"Error creating resource from template: {e}")

        raise ValueError(f"Unknown resource: {uri}")

    def list_resources(self) -> list[Resource]:
        """List all registered resources."""
        logger.debug("Listing resources", extra={"count": len(self._resources)})
        return list(self._resources.values())

    def list_templates(self) -> list[ResourceTemplate]:
        """List all registered templates."""
        logger.debug("Listing templates", extra={"count": len(self._templates)})
        return list(self._templates.values())



================================================
File: src/fastmcp/resources/templates.py
================================================
"""Resource template functionality."""

import inspect
import re
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, Field, TypeAdapter, validate_call

from fastmcp.resources.types import FunctionResource, Resource


class ResourceTemplate(BaseModel):
    """A template for dynamically creating resources."""

    uri_template: str = Field(
        description="URI template with parameters (e.g. weather://{city}/current)"
    )
    name: str = Field(description="Name of the resource")
    description: str | None = Field(description="Description of what the resource does")
    mime_type: str = Field(
        default="text/plain", description="MIME type of the resource content"
    )
    fn: Callable = Field(exclude=True)
    parameters: dict = Field(description="JSON schema for function parameters")

    @classmethod
    def from_function(
        cls,
        fn: Callable,
        uri_template: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> "ResourceTemplate":
        """Create a template from a function."""
        func_name = name or fn.__name__
        if func_name == "<lambda>":
            raise ValueError("You must provide a name for lambda functions")

        # Get schema from TypeAdapter - will fail if function isn't properly typed
        parameters = TypeAdapter(fn).json_schema()

        # ensure the arguments are properly cast
        fn = validate_call(fn)

        return cls(
            uri_template=uri_template,
            name=func_name,
            description=description or fn.__doc__ or "",
            mime_type=mime_type or "text/plain",
            fn=fn,
            parameters=parameters,
        )

    def matches(self, uri: str) -> Optional[Dict[str, Any]]:
        """Check if URI matches template and extract parameters."""
        # Convert template to regex pattern
        pattern = self.uri_template.replace("{", "(?P<").replace("}", ">[^/]+)")
        match = re.match(f"^{pattern}$", uri)
        if match:
            return match.groupdict()
        return None

    async def create_resource(self, uri: str, params: Dict[str, Any]) -> Resource:
        """Create a resource from the template with the given parameters."""
        try:
            # Call function and check if result is a coroutine
            result = self.fn(**params)
            if inspect.iscoroutine(result):
                result = await result

            return FunctionResource(
                uri=uri,  # type: ignore
                name=self.name,
                description=self.description,
                mime_type=self.mime_type,
                fn=lambda: result,  # Capture result in closure
            )
        except Exception as e:
            raise ValueError(f"Error creating resource from template: {e}")



================================================
File: src/fastmcp/resources/types.py
================================================
"""Concrete resource implementations."""

import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Union

import httpx
import pydantic.json
import pydantic_core
from pydantic import Field, ValidationInfo

from fastmcp.resources.base import Resource


class TextResource(Resource):
    """A resource that reads from a string."""

    text: str = Field(description="Text content of the resource")

    async def read(self) -> str:
        """Read the text content."""
        return self.text


class BinaryResource(Resource):
    """A resource that reads from bytes."""

    data: bytes = Field(description="Binary content of the resource")

    async def read(self) -> bytes:
        """Read the binary content."""
        return self.data


class FunctionResource(Resource):
    """A resource that defers data loading by wrapping a function.

    The function is only called when the resource is read, allowing for lazy loading
    of potentially expensive data. This is particularly useful when listing resources,
    as the function won't be called until the resource is actually accessed.

    The function can return:
    - str for text content (default)
    - bytes for binary content
    - other types will be converted to JSON
    """

    fn: Callable[[], Any] = Field(exclude=True)

    async def read(self) -> Union[str, bytes]:
        """Read the resource by calling the wrapped function."""
        try:
            result = self.fn()
            if isinstance(result, Resource):
                return await result.read()
            if isinstance(result, bytes):
                return result
            if isinstance(result, str):
                return result
            try:
                return json.dumps(pydantic_core.to_jsonable_python(result))
            except (TypeError, pydantic_core.PydanticSerializationError):
                # If JSON serialization fails, try str()
                return str(result)
        except Exception as e:
            raise ValueError(f"Error reading resource {self.uri}: {e}")


class FileResource(Resource):
    """A resource that reads from a file.

    Set is_binary=True to read file as binary data instead of text.
    """

    path: Path = Field(description="Path to the file")
    is_binary: bool = Field(
        default=False,
        description="Whether to read the file as binary data",
    )
    mime_type: str = Field(
        default="text/plain",
        description="MIME type of the resource content",
    )

    @pydantic.field_validator("path")
    @classmethod
    def validate_absolute_path(cls, path: Path) -> Path:
        """Ensure path is absolute."""
        if not path.is_absolute():
            raise ValueError("Path must be absolute")
        return path

    @pydantic.field_validator("is_binary")
    @classmethod
    def set_binary_from_mime_type(cls, is_binary: bool, info: ValidationInfo) -> bool:
        """Set is_binary based on mime_type if not explicitly set."""
        if is_binary:
            return True
        mime_type = info.data.get("mime_type", "text/plain")
        return not mime_type.startswith("text/")

    async def read(self) -> Union[str, bytes]:
        """Read the file content."""
        try:
            if self.is_binary:
                return await asyncio.to_thread(self.path.read_bytes)
            return await asyncio.to_thread(self.path.read_text)
        except Exception as e:
            raise ValueError(f"Error reading file {self.path}: {e}")


class HttpResource(Resource):
    """A resource that reads from an HTTP endpoint."""

    url: str = Field(description="URL to fetch content from")
    mime_type: str | None = Field(
        default="application/json", description="MIME type of the resource content"
    )

    async def read(self) -> Union[str, bytes]:
        """Read the HTTP content."""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url)
            response.raise_for_status()
            return response.text


class DirectoryResource(Resource):
    """A resource that lists files in a directory."""

    path: Path = Field(description="Path to the directory")
    recursive: bool = Field(
        default=False, description="Whether to list files recursively"
    )
    pattern: str | None = Field(
        default=None, description="Optional glob pattern to filter files"
    )
    mime_type: str | None = Field(
        default="application/json", description="MIME type of the resource content"
    )

    @pydantic.field_validator("path")
    @classmethod
    def validate_absolute_path(cls, path: Path) -> Path:
        """Ensure path is absolute."""
        if not path.is_absolute():
            raise ValueError("Path must be absolute")
        return path

    def list_files(self) -> list[Path]:
        """List files in the directory."""
        if not self.path.exists():
            raise FileNotFoundError(f"Directory not found: {self.path}")
        if not self.path.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.path}")

        try:
            if self.pattern:
                return (
                    list(self.path.glob(self.pattern))
                    if not self.recursive
                    else list(self.path.rglob(self.pattern))
                )
            return (
                list(self.path.glob("*"))
                if not self.recursive
                else list(self.path.rglob("*"))
            )
        except Exception as e:
            raise ValueError(f"Error listing directory {self.path}: {e}")

    async def read(self) -> str:  # Always returns JSON string
        """Read the directory listing."""
        try:
            files = await asyncio.to_thread(self.list_files)
            file_list = [str(f.relative_to(self.path)) for f in files if f.is_file()]
            return json.dumps({"files": file_list}, indent=2)
        except Exception as e:
            raise ValueError(f"Error reading directory {self.path}: {e}")



================================================
File: src/fastmcp/tools/__init__.py
================================================
from .base import Tool
from .tool_manager import ToolManager

__all__ = ["Tool", "ToolManager"]



================================================
File: src/fastmcp/tools/base.py
================================================
import fastmcp
from fastmcp.exceptions import ToolError

from fastmcp.utilities.func_metadata import func_metadata, FuncMetadata
from pydantic import BaseModel, Field


import inspect
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from fastmcp.server import Context


class Tool(BaseModel):
    """Internal tool registration info."""

    fn: Callable = Field(exclude=True)
    name: str = Field(description="Name of the tool")
    description: str = Field(description="Description of what the tool does")
    parameters: dict = Field(description="JSON schema for tool parameters")
    fn_metadata: FuncMetadata = Field(
        description="Metadata about the function including a pydantic model for tool arguments"
    )
    is_async: bool = Field(description="Whether the tool is async")
    context_kwarg: Optional[str] = Field(
        None, description="Name of the kwarg that should receive context"
    )

    @classmethod
    def from_function(
        cls,
        fn: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        context_kwarg: Optional[str] = None,
    ) -> "Tool":
        """Create a Tool from a function."""
        func_name = name or fn.__name__

        if func_name == "<lambda>":
            raise ValueError("You must provide a name for lambda functions")

        func_doc = description or fn.__doc__ or ""
        is_async = inspect.iscoroutinefunction(fn)

        # Find context parameter if it exists
        if context_kwarg is None:
            sig = inspect.signature(fn)
            for param_name, param in sig.parameters.items():
                if param.annotation is fastmcp.Context:
                    context_kwarg = param_name
                    break

        func_arg_metadata = func_metadata(
            fn,
            skip_names=[context_kwarg] if context_kwarg is not None else [],
        )
        parameters = func_arg_metadata.arg_model.model_json_schema()

        return cls(
            fn=fn,
            name=func_name,
            description=func_doc,
            parameters=parameters,
            fn_metadata=func_arg_metadata,
            is_async=is_async,
            context_kwarg=context_kwarg,
        )

    async def run(self, arguments: dict, context: Optional["Context"] = None) -> Any:
        """Run the tool with arguments."""
        try:
            return await self.fn_metadata.call_fn_with_arg_validation(
                self.fn,
                self.is_async,
                arguments,
                {self.context_kwarg: context}
                if self.context_kwarg is not None
                else None,
            )
        except Exception as e:
            raise ToolError(f"Error executing tool {self.name}: {e}") from e



================================================
File: src/fastmcp/tools/tool_manager.py
================================================
from fastmcp.exceptions import ToolError

from fastmcp.tools.base import Tool


from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

from fastmcp.utilities.logging import get_logger

if TYPE_CHECKING:
    from fastmcp.server import Context

logger = get_logger(__name__)


class ToolManager:
    """Manages FastMCP tools."""

    def __init__(self, warn_on_duplicate_tools: bool = True):
        self._tools: Dict[str, Tool] = {}
        self.warn_on_duplicate_tools = warn_on_duplicate_tools

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        """List all registered tools."""
        return list(self._tools.values())

    def add_tool(
        self,
        fn: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Tool:
        """Add a tool to the server."""
        tool = Tool.from_function(fn, name=name, description=description)
        existing = self._tools.get(tool.name)
        if existing:
            if self.warn_on_duplicate_tools:
                logger.warning(f"Tool already exists: {tool.name}")
            return existing
        self._tools[tool.name] = tool
        return tool

    async def call_tool(
        self, name: str, arguments: dict, context: Optional["Context"] = None
    ) -> Any:
        """Call a tool by name with arguments."""
        tool = self.get_tool(name)
        if not tool:
            raise ToolError(f"Unknown tool: {name}")

        return await tool.run(arguments, context=context)



================================================
File: src/fastmcp/utilities/__init__.py
================================================
"""FastMCP utility modules."""



================================================
File: src/fastmcp/utilities/func_metadata.py
================================================
import inspect
from collections.abc import Callable, Sequence, Awaitable
from typing import (
    Annotated,
    Any,
    Dict,
    ForwardRef,
)
from pydantic import Field
from fastmcp.exceptions import InvalidSignature
from pydantic._internal._typing_extra import eval_type_lenient
import json
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic import ConfigDict, create_model
from pydantic import WithJsonSchema
from pydantic_core import PydanticUndefined
from fastmcp.utilities.logging import get_logger


logger = get_logger(__name__)


class ArgModelBase(BaseModel):
    """A model representing the arguments to a function."""

    def model_dump_one_level(self) -> dict[str, Any]:
        """Return a dict of the model's fields, one level deep.

        That is, sub-models etc are not dumped - they are kept as pydantic models.
        """
        kwargs: dict[str, Any] = {}
        for field_name in self.model_fields.keys():
            kwargs[field_name] = getattr(self, field_name)
        return kwargs

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class FuncMetadata(BaseModel):
    arg_model: Annotated[type[ArgModelBase], WithJsonSchema(None)]
    # We can add things in the future like
    #  - Maybe some args are excluded from attempting to parse from JSON
    #  - Maybe some args are special (like context) for dependency injection

    async def call_fn_with_arg_validation(
        self,
        fn: Callable[..., Any] | Awaitable[Any],
        fn_is_async: bool,
        arguments_to_validate: dict[str, Any],
        arguments_to_pass_directly: dict[str, Any] | None,
    ) -> Any:
        """Call the given function with arguments validated and injected.

        Arguments are first attempted to be parsed from JSON, then validated against
        the argument model, before being passed to the function.
        """
        arguments_pre_parsed = self.pre_parse_json(arguments_to_validate)
        arguments_parsed_model = self.arg_model.model_validate(arguments_pre_parsed)
        arguments_parsed_dict = arguments_parsed_model.model_dump_one_level()

        arguments_parsed_dict |= arguments_to_pass_directly or {}

        if fn_is_async:
            if isinstance(fn, Awaitable):
                return await fn
            return await fn(**arguments_parsed_dict)
        if isinstance(fn, Callable):
            return fn(**arguments_parsed_dict)
        raise TypeError("fn must be either Callable or Awaitable")

    def pre_parse_json(self, data: dict[str, Any]) -> dict[str, Any]:
        """Pre-parse data from JSON.

        Return a dict with same keys as input but with values parsed from JSON
        if appropriate.

        This is to handle cases like `["a", "b", "c"]` being passed in as JSON inside
        a string rather than an actual list. Claude desktop is prone to this - in fact
        it seems incapable of NOT doing this. For sub-models, it tends to pass
        dicts (JSON objects) as JSON strings, which can be pre-parsed here.
        """
        new_data = data.copy()  # Shallow copy
        for field_name, field_info in self.arg_model.model_fields.items():
            if field_name not in data.keys():
                continue
            if isinstance(data[field_name], str):
                try:
                    pre_parsed = json.loads(data[field_name])
                except json.JSONDecodeError:
                    continue  # Not JSON - skip
                if isinstance(pre_parsed, (str, int, float)):
                    # This is likely that the raw value is e.g. `"hello"` which we
                    # Should really be parsed as '"hello"' in Python - but if we parse
                    # it as JSON it'll turn into just 'hello'. So we skip it.
                    continue
                new_data[field_name] = pre_parsed
        assert new_data.keys() == data.keys()
        return new_data

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


def func_metadata(func: Callable, skip_names: Sequence[str] = ()) -> FuncMetadata:
    """Given a function, return metadata including a pydantic model representing its signature.

    The use case for this is
    ```
    meta = func_to_pyd(func)
    validated_args = meta.arg_model.model_validate(some_raw_data_dict)
    return func(**validated_args.model_dump_one_level())
    ```

    **critically** it also provides pre-parse helper to attempt to parse things from JSON.

    Args:
        func: The function to convert to a pydantic model
        skip_names: A list of parameter names to skip. These will not be included in
            the model.
    Returns:
        A pydantic model representing the function's signature.
    """
    sig = _get_typed_signature(func)
    params = sig.parameters
    dynamic_pydantic_model_params: dict[str, Any] = {}
    globalns = getattr(func, "__globals__", {})
    for param in params.values():
        if param.name.startswith("_"):
            raise InvalidSignature(
                f"Parameter {param.name} of {func.__name__} may not start with an underscore"
            )
        if param.name in skip_names:
            continue
        annotation = param.annotation

        # `x: None` / `x: None = None`
        if annotation is None:
            annotation = Annotated[
                None,
                Field(
                    default=param.default
                    if param.default is not inspect.Parameter.empty
                    else PydanticUndefined
                ),
            ]

        # Untyped field
        if annotation is inspect.Parameter.empty:
            annotation = Annotated[
                Any,
                Field(),
                # 🤷
                WithJsonSchema({"title": param.name, "type": "string"}),
            ]

        field_info = FieldInfo.from_annotated_attribute(
            _get_typed_annotation(annotation, globalns),
            param.default
            if param.default is not inspect.Parameter.empty
            else PydanticUndefined,
        )
        dynamic_pydantic_model_params[param.name] = (field_info.annotation, field_info)
        continue

    arguments_model = create_model(
        f"{func.__name__}Arguments",
        **dynamic_pydantic_model_params,
        __base__=ArgModelBase,
    )
    resp = FuncMetadata(arg_model=arguments_model)
    return resp


def _get_typed_annotation(annotation: Any, globalns: Dict[str, Any]) -> Any:
    if isinstance(annotation, str):
        annotation = ForwardRef(annotation)
        annotation = eval_type_lenient(annotation, globalns, globalns)

    return annotation


def _get_typed_signature(call: Callable[..., Any]) -> inspect.Signature:
    """Get function signature while evaluating forward references"""
    signature = inspect.signature(call)
    globalns = getattr(call, "__globals__", {})
    typed_params = [
        inspect.Parameter(
            name=param.name,
            kind=param.kind,
            default=param.default,
            annotation=_get_typed_annotation(param.annotation, globalns),
        )
        for param in signature.parameters.values()
    ]
    typed_signature = inspect.Signature(typed_params)
    return typed_signature



================================================
File: src/fastmcp/utilities/logging.py
================================================
"""Logging utilities for FastMCP."""

import logging
from typing import Literal

from rich.console import Console
from rich.logging import RichHandler


def get_logger(name: str) -> logging.Logger:
    """Get a logger nested under FastMCP namespace.

    Args:
        name: the name of the logger, which will be prefixed with 'FastMCP.'

    Returns:
        a configured logger instance
    """
    return logging.getLogger(f"FastMCP.{name}")


def configure_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
) -> None:
    """Configure logging for FastMCP.

    Args:
        level: the log level to use
    """
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=Console(stderr=True), rich_tracebacks=True)],
    )



================================================
File: src/fastmcp/utilities/types.py
================================================
"""Common types used across FastMCP."""

import base64
from pathlib import Path
from typing import Optional, Union

from mcp.types import ImageContent


class Image:
    """Helper class for returning images from tools."""

    def __init__(
        self,
        path: Optional[Union[str, Path]] = None,
        data: Optional[bytes] = None,
        format: Optional[str] = None,
    ):
        if path is None and data is None:
            raise ValueError("Either path or data must be provided")
        if path is not None and data is not None:
            raise ValueError("Only one of path or data can be provided")

        self.path = Path(path) if path else None
        self.data = data
        self._format = format
        self._mime_type = self._get_mime_type()

    def _get_mime_type(self) -> str:
        """Get MIME type from format or guess from file extension."""
        if self._format:
            return f"image/{self._format.lower()}"

        if self.path:
            suffix = self.path.suffix.lower()
            return {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }.get(suffix, "application/octet-stream")
        return "image/png"  # default for raw binary data

    def to_image_content(self) -> ImageContent:
        """Convert to MCP ImageContent."""
        if self.path:
            with open(self.path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
        elif self.data is not None:
            data = base64.b64encode(self.data).decode()
        else:
            raise ValueError("No image data available")

        return ImageContent(type="image", data=data, mimeType=self._mime_type)



================================================
File: tests/__init__.py
================================================



================================================
File: tests/test_cli.py
================================================
"""Tests for the FastMCP CLI."""

import json
import sys
from pathlib import Path
from unittest.mock import call, patch

import pytest
from typer.testing import CliRunner

from fastmcp.cli.cli import _parse_env_var, _parse_file_path, app


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock Claude config file."""
    config = {"mcpServers": {}}
    config_file = tmp_path / "claude_desktop_config.json"
    config_file.write_text(json.dumps(config))
    return config_file


@pytest.fixture
def server_file(tmp_path):
    """Create a server file."""
    server_file = tmp_path / "server.py"
    server_file.write_text(
        """from fastmcp import FastMCP
mcp = FastMCP("test")
"""
    )
    return server_file


@pytest.fixture
def mock_env_file(tmp_path):
    """Create a mock .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAZ=123")
    return env_file


def test_parse_env_var():
    """Test parsing environment variables."""
    assert _parse_env_var("FOO=bar") == ("FOO", "bar")
    assert _parse_env_var("FOO=") == ("FOO", "")
    assert _parse_env_var("FOO=bar baz") == ("FOO", "bar baz")
    assert _parse_env_var("FOO = bar ") == ("FOO", "bar")

    with pytest.raises(SystemExit):
        _parse_env_var("invalid")


@pytest.mark.parametrize(
    "args,expected_env",
    [
        # Basic env var
        (
            ["--env-var", "FOO=bar"],
            {"FOO": "bar"},
        ),
        # Multiple env vars
        (
            ["--env-var", "FOO=bar", "--env-var", "BAZ=123"],
            {"FOO": "bar", "BAZ": "123"},
        ),
        # Env var with spaces
        (
            ["--env-var", "FOO=bar baz"],
            {"FOO": "bar baz"},
        ),
    ],
)
def test_install_with_env_vars(mock_config, server_file, args, expected_env):
    """Test installing with environment variables."""
    runner = CliRunner()

    with patch("fastmcp.cli.claude.get_claude_config_path") as mock_config_path:
        mock_config_path.return_value = mock_config.parent

        result = runner.invoke(
            app,
            ["install", str(server_file)] + args,
        )

        assert result.exit_code == 0

        # Read the config file and check env vars
        config = json.loads(mock_config.read_text())
        assert "mcpServers" in config
        assert len(config["mcpServers"]) == 1
        server = next(iter(config["mcpServers"].values()))
        assert server["env"] == expected_env


def test_parse_file_path_windows_drive():
    """Test parsing a Windows file path with a drive letter."""
    file_spec = r"C:\path\to\file.txt"
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.is_file", return_value=True),
    ):
        file_path, server_object = _parse_file_path(file_spec)
        assert file_path == Path(r"C:\path\to\file.txt").resolve()
        assert server_object is None


def test_parse_file_path_with_object():
    """Test parsing a file path with an object specification."""
    file_spec = "/path/to/file.txt:object"
    with patch("sys.exit") as mock_exit:
        _parse_file_path(file_spec)

        # Check that sys.exit was called twice with code 1
        assert mock_exit.call_count == 2
        mock_exit.assert_has_calls([call(1), call(1)])


def test_parse_file_path_windows_with_object():
    """Test parsing a Windows file path with an object specification."""
    file_spec = r"C:\path\to\file.txt:object"
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.is_file", return_value=True),
    ):
        file_path, server_object = _parse_file_path(file_spec)
        assert file_path == Path(r"C:\path\to\file.txt").resolve()
        assert server_object == "object"


def test_install_with_env_file(mock_config, server_file, mock_env_file):
    """Test installing with environment variables from a file."""
    runner = CliRunner()

    with patch("fastmcp.cli.claude.get_claude_config_path") as mock_config_path:
        mock_config_path.return_value = mock_config.parent

        result = runner.invoke(
            app,
            ["install", str(server_file), "--env-file", str(mock_env_file)],
        )

        assert result.exit_code == 0

        # Read the config file and check env vars
        config = json.loads(mock_config.read_text())
        assert "mcpServers" in config
        assert len(config["mcpServers"]) == 1
        server = next(iter(config["mcpServers"].values()))
        assert server["env"] == {"FOO": "bar", "BAZ": "123"}


def test_install_preserves_existing_env_vars(mock_config, server_file):
    """Test that installing preserves existing environment variables."""
    # Set up initial config with env vars
    config = {
        "mcpServers": {
            "test": {
                "command": "uv",
                "args": [
                    "run",
                    "--with",
                    "fastmcp",
                    "fastmcp",
                    "run",
                    str(server_file),
                ],
                "env": {"FOO": "bar", "BAZ": "123"},
            }
        }
    }
    mock_config.write_text(json.dumps(config))

    runner = CliRunner()

    with patch("fastmcp.cli.claude.get_claude_config_path") as mock_config_path:
        mock_config_path.return_value = mock_config.parent

        # Install with a new env var
        result = runner.invoke(
            app,
            ["install", str(server_file), "--env-var", "NEW=value"],
        )

        assert result.exit_code == 0

        # Read the config file and check env vars are preserved
        config = json.loads(mock_config.read_text())
        server = next(iter(config["mcpServers"].values()))
        assert server["env"] == {"FOO": "bar", "BAZ": "123", "NEW": "value"}


def test_install_updates_existing_env_vars(mock_config, server_file):
    """Test that installing updates existing environment variables."""
    # Set up initial config with env vars
    config = {
        "mcpServers": {
            "test": {
                "command": "uv",
                "args": [
                    "run",
                    "--with",
                    "fastmcp",
                    "fastmcp",
                    "run",
                    str(server_file),
                ],
                "env": {"FOO": "bar", "BAZ": "123"},
            }
        }
    }
    mock_config.write_text(json.dumps(config))

    runner = CliRunner()

    with patch("fastmcp.cli.claude.get_claude_config_path") as mock_config_path:
        mock_config_path.return_value = mock_config.parent

        # Update an existing env var
        result = runner.invoke(
            app,
            ["install", str(server_file), "--env-var", "FOO=newvalue"],
        )

        assert result.exit_code == 0

        # Read the config file and check env var was updated
        config = json.loads(mock_config.read_text())
        server = next(iter(config["mcpServers"].values()))
        assert server["env"] == {"FOO": "newvalue", "BAZ": "123"}


def test_server_dependencies(mock_config, server_file):
    """Test that server dependencies are correctly handled."""
    # Create a server file with dependencies
    server_file = server_file.parent / "server_with_deps.py"
    server_file.write_text(
        """from fastmcp import FastMCP
mcp = FastMCP("test", dependencies=["pandas", "numpy"])
"""
    )

    runner = CliRunner()

    with patch("fastmcp.cli.claude.get_claude_config_path") as mock_config_path:
        mock_config_path.return_value = mock_config.parent

        result = runner.invoke(app, ["install", str(server_file)])

        assert result.exit_code == 0

        # Read the config file and check dependencies were added as --with args
        config = json.loads(mock_config.read_text())
        server = next(iter(config["mcpServers"].values()))
        assert "--with" in server["args"]
        assert "pandas" in server["args"]
        assert "numpy" in server["args"]


def test_server_dependencies_empty(mock_config, server_file):
    """Test that server with no dependencies works correctly."""
    runner = CliRunner()

    with patch("fastmcp.cli.claude.get_claude_config_path") as mock_config_path:
        mock_config_path.return_value = mock_config.parent

        result = runner.invoke(app, ["install", str(server_file)])

        assert result.exit_code == 0

        # Read the config file and check only fastmcp is in --with args
        config = json.loads(mock_config.read_text())
        server = next(iter(config["mcpServers"].values()))
        assert server["args"].count("--with") == 1
        assert "fastmcp" in server["args"]


def test_dev_with_dependencies(mock_config, server_file):
    """Test that dev command handles dependencies correctly."""
    server_file = server_file.parent / "server_with_deps.py"
    server_file.write_text(
        """from fastmcp import FastMCP
mcp = FastMCP("test", dependencies=["pandas", "numpy"])
"""
    )

    runner = CliRunner()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        result = runner.invoke(app, ["dev", str(server_file)])
        assert result.exit_code == 0

        if sys.platform == "win32":
            # On Windows, expect two calls
            assert mock_run.call_count == 2
            assert mock_run.call_args_list[0] == call(
                ["npx.cmd", "--version"], check=True, capture_output=True, shell=True
            )

            # get the actual command and expected command without dependencies
            actual_cmd = mock_run.call_args_list[1][0][0]
            expected_start = [
                "npx.cmd",
                "@modelcontextprotocol/inspector",
                "uv",
                "run",
                "--with",
                "fastmcp",
            ]
            expected_end = ["fastmcp", "run", str(server_file)]

            # verify start and end of command
            assert actual_cmd[: len(expected_start)] == expected_start
            assert actual_cmd[-len(expected_end) :] == expected_end

            # verify dependencies are present (order-independent)
            deps_section = actual_cmd[len(expected_start) : -len(expected_end)]
            assert all(
                x in deps_section for x in ["--with", "numpy", "--with", "pandas"]
            )

            # Verify subprocess call kwargs, allowing for environment variables
            call_kwargs = mock_run.call_args_list[1][1]
            assert call_kwargs["check"] is True
            assert call_kwargs["shell"] is True
            assert isinstance(call_kwargs["env"], dict)
        else:
            # same verification for unix, just with different command prefix
            actual_cmd = mock_run.call_args_list[0][0][0]
            expected_start = [
                "npx",
                "@modelcontextprotocol/inspector",
                "uv",
                "run",
                "--with",
                "fastmcp",
            ]
            expected_end = ["fastmcp", "run", str(server_file)]

            assert actual_cmd[: len(expected_start)] == expected_start
            assert actual_cmd[-len(expected_end) :] == expected_end

            deps_section = actual_cmd[len(expected_start) : -len(expected_end)]
            assert all(
                x in deps_section for x in ["--with", "numpy", "--with", "pandas"]
            )

            # Verify subprocess call kwargs, allowing for environment variables
            call_kwargs = mock_run.call_args_list[0][1]
            assert call_kwargs["check"] is True
            assert call_kwargs["shell"] is False
            assert isinstance(call_kwargs["env"], dict)


def test_run_with_dependencies(mock_config, server_file):
    """Test that run command does not handle dependencies."""
    # Create a server file with dependencies
    server_file = server_file.parent / "server_with_deps.py"
    server_file.write_text(
        """from fastmcp import FastMCP
mcp = FastMCP("test", dependencies=["pandas", "numpy"])

if __name__ == "__main__":
    mcp.run()
"""
    )

    runner = CliRunner()

    with patch("subprocess.run") as mock_run:
        result = runner.invoke(app, ["run", str(server_file)])
        assert result.exit_code == 0

        # Run command should not call subprocess.run
        mock_run.assert_not_called()



================================================
File: tests/test_func_metadata.py
================================================
from typing import Annotated

import annotated_types
import pytest
from pydantic import BaseModel, Field

from fastmcp.utilities.func_metadata import func_metadata


class SomeInputModelA(BaseModel):
    pass


class SomeInputModelB(BaseModel):
    class InnerModel(BaseModel):
        x: int

    how_many_shrimp: Annotated[int, Field(description="How many shrimp in the tank???")]
    ok: InnerModel
    y: None


def complex_arguments_fn(
    an_int: int,
    must_be_none: None,
    must_be_none_dumb_annotation: Annotated[None, "blah"],
    list_of_ints: list[int],
    # list[str] | str is an interesting case because if it comes in as JSON like
    # "[\"a\", \"b\"]" then it will be naively parsed as a string.
    list_str_or_str: list[str] | str,
    an_int_annotated_with_field: Annotated[
        int, Field(description="An int with a field")
    ],
    an_int_annotated_with_field_and_others: Annotated[
        int,
        str,  # Should be ignored, really
        Field(description="An int with a field"),
        annotated_types.Gt(1),
    ],
    an_int_annotated_with_junk: Annotated[
        int,
        "123",
        456,
    ],
    field_with_default_via_field_annotation_before_nondefault_arg: Annotated[
        int, Field(1)
    ],
    unannotated,
    my_model_a: SomeInputModelA,
    my_model_a_forward_ref: "SomeInputModelA",
    my_model_b: SomeInputModelB,
    an_int_annotated_with_field_default: Annotated[
        int,
        Field(1, description="An int with a field"),
    ],
    unannotated_with_default=5,
    my_model_a_with_default: SomeInputModelA = SomeInputModelA(),  # noqa: B008
    an_int_with_default: int = 1,
    must_be_none_with_default: None = None,
    an_int_with_equals_field: int = Field(1, ge=0),
    int_annotated_with_default: Annotated[int, Field(description="hey")] = 5,
) -> str:
    _ = (
        an_int,
        must_be_none,
        must_be_none_dumb_annotation,
        list_of_ints,
        list_str_or_str,
        an_int_annotated_with_field,
        an_int_annotated_with_field_and_others,
        an_int_annotated_with_junk,
        field_with_default_via_field_annotation_before_nondefault_arg,
        unannotated,
        an_int_annotated_with_field_default,
        unannotated_with_default,
        my_model_a,
        my_model_a_forward_ref,
        my_model_b,
        my_model_a_with_default,
        an_int_with_default,
        must_be_none_with_default,
        an_int_with_equals_field,
        int_annotated_with_default,
    )
    return "ok!"


async def test_complex_function_runtime_arg_validation_non_json():
    """Test that basic non-JSON arguments are validated correctly"""
    meta = func_metadata(complex_arguments_fn)

    # Test with minimum required arguments
    result = await meta.call_fn_with_arg_validation(
        complex_arguments_fn,
        fn_is_async=False,
        arguments_to_validate={
            "an_int": 1,
            "must_be_none": None,
            "must_be_none_dumb_annotation": None,
            "list_of_ints": [1, 2, 3],
            "list_str_or_str": "hello",
            "an_int_annotated_with_field": 42,
            "an_int_annotated_with_field_and_others": 5,
            "an_int_annotated_with_junk": 100,
            "unannotated": "test",
            "my_model_a": {},
            "my_model_a_forward_ref": {},
            "my_model_b": {"how_many_shrimp": 5, "ok": {"x": 1}, "y": None},
        },
        arguments_to_pass_directly=None,
    )
    assert result == "ok!"

    # Test with invalid types
    with pytest.raises(ValueError):
        await meta.call_fn_with_arg_validation(
            complex_arguments_fn,
            fn_is_async=False,
            arguments_to_validate={"an_int": "not an int"},
            arguments_to_pass_directly=None,
        )


async def test_complex_function_runtime_arg_validation_with_json():
    """Test that JSON string arguments are parsed and validated correctly"""
    meta = func_metadata(complex_arguments_fn)

    result = await meta.call_fn_with_arg_validation(
        complex_arguments_fn,
        fn_is_async=False,
        arguments_to_validate={
            "an_int": 1,
            "must_be_none": None,
            "must_be_none_dumb_annotation": None,
            "list_of_ints": "[1, 2, 3]",  # JSON string
            "list_str_or_str": '["a", "b", "c"]',  # JSON string
            "an_int_annotated_with_field": 42,
            "an_int_annotated_with_field_and_others": "5",  # JSON string
            "an_int_annotated_with_junk": 100,
            "unannotated": "test",
            "my_model_a": "{}",  # JSON string
            "my_model_a_forward_ref": "{}",  # JSON string
            "my_model_b": '{"how_many_shrimp": 5, "ok": {"x": 1}, "y": null}',  # JSON string
        },
        arguments_to_pass_directly=None,
    )
    assert result == "ok!"


def test_str_vs_list_str():
    """Test handling of string vs list[str] type annotations.

    This is tricky as '"hello"' can be parsed as a JSON string or a Python string.
    We want to make sure it's kept as a python string.
    """

    def func_with_str_types(str_or_list: str | list[str]):
        return str_or_list

    meta = func_metadata(func_with_str_types)

    # Test string input for union type
    result = meta.pre_parse_json({"str_or_list": "hello"})
    assert result["str_or_list"] == "hello"

    # Test string input that contains valid JSON for union type
    # We want to see here that the JSON-vali string is NOT parsed as JSON, but rather
    # kept as a raw string
    result = meta.pre_parse_json({"str_or_list": '"hello"'})
    assert result["str_or_list"] == '"hello"'

    # Test list input for union type
    result = meta.pre_parse_json({"str_or_list": '["hello", "world"]'})
    assert result["str_or_list"] == ["hello", "world"]


def test_str_vs_int():
    """
    Test that string values are kept as strings even when they contain numbers,
    while numbers are parsed correctly.
    """

    def func_with_str_and_int(a: str, b: int):
        return a

    meta = func_metadata(func_with_str_and_int)
    result = meta.pre_parse_json({"a": "123", "b": 123})
    assert result["a"] == "123"
    assert result["b"] == 123


def test_skip_names():
    """Test that skipped parameters are not included in the model"""

    def func_with_many_params(
        keep_this: int, skip_this: str, also_keep: float, also_skip: bool
    ):
        return keep_this, skip_this, also_keep, also_skip

    # Skip some parameters
    meta = func_metadata(func_with_many_params, skip_names=["skip_this", "also_skip"])

    # Check model fields
    assert "keep_this" in meta.arg_model.model_fields
    assert "also_keep" in meta.arg_model.model_fields
    assert "skip_this" not in meta.arg_model.model_fields
    assert "also_skip" not in meta.arg_model.model_fields

    # Validate that we can call with only non-skipped parameters
    model: BaseModel = meta.arg_model.model_validate({"keep_this": 1, "also_keep": 2.5})  # type: ignore
    assert model.keep_this == 1  # type: ignore
    assert model.also_keep == 2.5  # type: ignore


async def test_lambda_function():
    """Test lambda function schema and validation"""
    fn = lambda x, y=5: x  # noqa: E731
    meta = func_metadata(lambda x, y=5: x)

    # Test schema
    assert meta.arg_model.model_json_schema() == {
        "properties": {
            "x": {"title": "x", "type": "string"},
            "y": {"default": 5, "title": "y", "type": "string"},
        },
        "required": ["x"],
        "title": "<lambda>Arguments",
        "type": "object",
    }

    async def check_call(args):
        return await meta.call_fn_with_arg_validation(
            fn,
            fn_is_async=False,
            arguments_to_validate=args,
            arguments_to_pass_directly=None,
        )

    # Basic calls
    assert await check_call({"x": "hello"}) == "hello"
    assert await check_call({"x": "hello", "y": "world"}) == "hello"
    assert await check_call({"x": '"hello"'}) == '"hello"'

    # Missing required arg
    with pytest.raises(ValueError):
        await check_call({"y": "world"})


def test_complex_function_json_schema():
    meta = func_metadata(complex_arguments_fn)
    assert meta.arg_model.model_json_schema() == {
        "$defs": {
            "InnerModel": {
                "properties": {"x": {"title": "X", "type": "integer"}},
                "required": ["x"],
                "title": "InnerModel",
                "type": "object",
            },
            "SomeInputModelA": {
                "properties": {},
                "title": "SomeInputModelA",
                "type": "object",
            },
            "SomeInputModelB": {
                "properties": {
                    "how_many_shrimp": {
                        "description": "How many shrimp in the tank???",
                        "title": "How Many Shrimp",
                        "type": "integer",
                    },
                    "ok": {"$ref": "#/$defs/InnerModel"},
                    "y": {"title": "Y", "type": "null"},
                },
                "required": ["how_many_shrimp", "ok", "y"],
                "title": "SomeInputModelB",
                "type": "object",
            },
        },
        "properties": {
            "an_int": {"title": "An Int", "type": "integer"},
            "must_be_none": {"title": "Must Be None", "type": "null"},
            "must_be_none_dumb_annotation": {
                "title": "Must Be None Dumb Annotation",
                "type": "null",
            },
            "list_of_ints": {
                "items": {"type": "integer"},
                "title": "List Of Ints",
                "type": "array",
            },
            "list_str_or_str": {
                "anyOf": [
                    {"items": {"type": "string"}, "type": "array"},
                    {"type": "string"},
                ],
                "title": "List Str Or Str",
            },
            "an_int_annotated_with_field": {
                "description": "An int with a field",
                "title": "An Int Annotated With Field",
                "type": "integer",
            },
            "an_int_annotated_with_field_and_others": {
                "description": "An int with a field",
                "exclusiveMinimum": 1,
                "title": "An Int Annotated With Field And Others",
                "type": "integer",
            },
            "an_int_annotated_with_junk": {
                "title": "An Int Annotated With Junk",
                "type": "integer",
            },
            "field_with_default_via_field_annotation_before_nondefault_arg": {
                "default": 1,
                "title": "Field With Default Via Field Annotation Before Nondefault Arg",
                "type": "integer",
            },
            "unannotated": {"title": "unannotated", "type": "string"},
            "my_model_a": {"$ref": "#/$defs/SomeInputModelA"},
            "my_model_a_forward_ref": {"$ref": "#/$defs/SomeInputModelA"},
            "my_model_b": {"$ref": "#/$defs/SomeInputModelB"},
            "an_int_annotated_with_field_default": {
                "default": 1,
                "description": "An int with a field",
                "title": "An Int Annotated With Field Default",
                "type": "integer",
            },
            "unannotated_with_default": {
                "default": 5,
                "title": "unannotated_with_default",
                "type": "string",
            },
            "my_model_a_with_default": {
                "$ref": "#/$defs/SomeInputModelA",
                "default": {},
            },
            "an_int_with_default": {
                "default": 1,
                "title": "An Int With Default",
                "type": "integer",
            },
            "must_be_none_with_default": {
                "default": None,
                "title": "Must Be None With Default",
                "type": "null",
            },
            "an_int_with_equals_field": {
                "default": 1,
                "minimum": 0,
                "title": "An Int With Equals Field",
                "type": "integer",
            },
            "int_annotated_with_default": {
                "default": 5,
                "description": "hey",
                "title": "Int Annotated With Default",
                "type": "integer",
            },
        },
        "required": [
            "an_int",
            "must_be_none",
            "must_be_none_dumb_annotation",
            "list_of_ints",
            "list_str_or_str",
            "an_int_annotated_with_field",
            "an_int_annotated_with_field_and_others",
            "an_int_annotated_with_junk",
            "unannotated",
            "my_model_a",
            "my_model_a_forward_ref",
            "my_model_b",
        ],
        "title": "complex_arguments_fnArguments",
        "type": "object",
    }



================================================
File: tests/test_server.py
================================================
import base64
from pathlib import Path
from typing import TYPE_CHECKING, Union

import pytest
from mcp.shared.exceptions import McpError
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)
from mcp.types import (
    ImageContent,
    TextContent,
    TextResourceContents,
    BlobResourceContents,
)
from pydantic import AnyUrl

from fastmcp import Context, FastMCP
from fastmcp.prompts.base import EmbeddedResource, Message, UserMessage
from fastmcp.resources import FileResource, FunctionResource
from fastmcp.utilities.types import Image

if TYPE_CHECKING:
    from fastmcp import Context


class TestServer:
    async def test_create_server(self):
        mcp = FastMCP()
        assert mcp.name == "FastMCP"

    async def test_add_tool_decorator(self):
        mcp = FastMCP()

        @mcp.tool()
        def add(x: int, y: int) -> int:
            return x + y

        assert len(mcp._tool_manager.list_tools()) == 1

    async def test_add_tool_decorator_incorrect_usage(self):
        mcp = FastMCP()

        with pytest.raises(TypeError, match="The @tool decorator was used incorrectly"):

            @mcp.tool  # Missing parentheses #type: ignore
            def add(x: int, y: int) -> int:
                return x + y

    async def test_add_resource_decorator(self):
        mcp = FastMCP()

        @mcp.resource("r://{x}")
        def get_data(x: str) -> str:
            return f"Data: {x}"

        assert len(mcp._resource_manager._templates) == 1

    async def test_add_resource_decorator_incorrect_usage(self):
        mcp = FastMCP()

        with pytest.raises(
            TypeError, match="The @resource decorator was used incorrectly"
        ):

            @mcp.resource  # Missing parentheses #type: ignore
            def get_data(x: str) -> str:
                return f"Data: {x}"


def tool_fn(x: int, y: int) -> int:
    return x + y


def error_tool_fn() -> None:
    raise ValueError("Test error")


def image_tool_fn(path: str) -> Image:
    return Image(path)


def mixed_content_tool_fn() -> list[Union[TextContent, ImageContent]]:
    return [
        TextContent(type="text", text="Hello"),
        ImageContent(type="image", data="abc", mimeType="image/png"),
    ]


class TestServerTools:
    async def test_add_tool(self):
        mcp = FastMCP()
        mcp.add_tool(tool_fn)
        mcp.add_tool(tool_fn)
        assert len(mcp._tool_manager.list_tools()) == 1

    async def test_list_tools(self):
        mcp = FastMCP()
        mcp.add_tool(tool_fn)
        async with client_session(mcp._mcp_server) as client:
            tools = await client.list_tools()
            assert len(tools.tools) == 1

    async def test_call_tool(self):
        mcp = FastMCP()
        mcp.add_tool(tool_fn)
        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool("my_tool", {"arg1": "value"})
            assert not hasattr(result, "error")
            assert len(result.content) > 0

    async def test_tool_exception_handling(self):
        mcp = FastMCP()
        mcp.add_tool(error_tool_fn)
        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool("error_tool_fn", {})
            assert len(result.content) == 1
            content = result.content[0]
            assert isinstance(content, TextContent)
            assert "Test error" in content.text
            assert result.isError is True

    async def test_tool_error_handling(self):
        mcp = FastMCP()
        mcp.add_tool(error_tool_fn)
        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool("error_tool_fn", {})
            assert len(result.content) == 1
            content = result.content[0]
            assert isinstance(content, TextContent)
            assert "Test error" in content.text
            assert result.isError is True

    async def test_tool_error_details(self):
        """Test that exception details are properly formatted in the response"""
        mcp = FastMCP()
        mcp.add_tool(error_tool_fn)
        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool("error_tool_fn", {})
            content = result.content[0]
            assert isinstance(content, TextContent)
            assert isinstance(content.text, str)
            assert "Test error" in content.text
            assert result.isError is True

    async def test_tool_return_value_conversion(self):
        mcp = FastMCP()
        mcp.add_tool(tool_fn)
        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool("tool_fn", {"x": 1, "y": 2})
            assert len(result.content) == 1
            content = result.content[0]
            assert isinstance(content, TextContent)
            assert content.text == "3"

    async def test_tool_image_helper(self, tmp_path: Path):
        # Create a test image
        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"fake png data")

        mcp = FastMCP()
        mcp.add_tool(image_tool_fn)
        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool("image_tool_fn", {"path": str(image_path)})
            assert len(result.content) == 1
            content = result.content[0]
            assert isinstance(content, ImageContent)
            assert content.type == "image"
            assert content.mimeType == "image/png"
            # Verify base64 encoding
            decoded = base64.b64decode(content.data)
            assert decoded == b"fake png data"

    async def test_tool_mixed_content(self):
        mcp = FastMCP()
        mcp.add_tool(mixed_content_tool_fn)
        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool("mixed_content_tool_fn", {})
            assert len(result.content) == 2
            content1 = result.content[0]
            content2 = result.content[1]
            assert isinstance(content1, TextContent)
            assert content1.text == "Hello"
            assert isinstance(content2, ImageContent)
            assert content2.mimeType == "image/png"
            assert content2.data == "abc"

    async def test_tool_mixed_list_with_image(self, tmp_path: Path):
        """Test that lists containing Image objects and other types are handled correctly"""
        # Create a test image
        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"test image data")

        def mixed_list_fn() -> list:
            return [
                "text message",
                Image(image_path),
                {"key": "value"},
                TextContent(type="text", text="direct content"),
            ]

        mcp = FastMCP()
        mcp.add_tool(mixed_list_fn)
        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool("mixed_list_fn", {})
            assert len(result.content) == 4
            # Check text conversion
            content1 = result.content[0]
            assert isinstance(content1, TextContent)
            assert content1.text == "text message"
            # Check image conversion
            content2 = result.content[1]
            assert isinstance(content2, ImageContent)
            assert content2.mimeType == "image/png"
            assert base64.b64decode(content2.data) == b"test image data"
            # Check dict conversion
            content3 = result.content[2]
            assert isinstance(content3, TextContent)
            assert '"key": "value"' in content3.text
            # Check direct TextContent
            content4 = result.content[3]
            assert isinstance(content4, TextContent)
            assert content4.text == "direct content"


class TestServerResources:
    async def test_text_resource(self):
        mcp = FastMCP()

        def get_text():
            return "Hello, world!"

        resource = FunctionResource(
            uri=AnyUrl("resource://test"), name="test", fn=get_text
        )
        mcp.add_resource(resource)

        async with client_session(mcp._mcp_server) as client:
            result = await client.read_resource(AnyUrl("resource://test"))
            assert isinstance(result.contents[0], TextResourceContents)
            assert result.contents[0].text == "Hello, world!"

    async def test_binary_resource(self):
        mcp = FastMCP()

        def get_binary():
            return b"Binary data"

        resource = FunctionResource(
            uri=AnyUrl("resource://binary"),
            name="binary",
            fn=get_binary,
            mime_type="application/octet-stream",
        )
        mcp.add_resource(resource)

        async with client_session(mcp._mcp_server) as client:
            result = await client.read_resource(AnyUrl("resource://binary"))
            assert isinstance(result.contents[0], BlobResourceContents)
            assert result.contents[0].blob == base64.b64encode(b"Binary data").decode()

    async def test_file_resource_text(self, tmp_path: Path):
        mcp = FastMCP()

        # Create a text file
        text_file = tmp_path / "test.txt"
        text_file.write_text("Hello from file!")

        resource = FileResource(
            uri=AnyUrl("file://test.txt"), name="test.txt", path=text_file
        )
        mcp.add_resource(resource)

        async with client_session(mcp._mcp_server) as client:
            result = await client.read_resource(AnyUrl("file://test.txt"))
            assert isinstance(result.contents[0], TextResourceContents)
            assert result.contents[0].text == "Hello from file!"

    async def test_file_resource_binary(self, tmp_path: Path):
        mcp = FastMCP()

        # Create a binary file
        binary_file = tmp_path / "test.bin"
        binary_file.write_bytes(b"Binary file data")

        resource = FileResource(
            uri=AnyUrl("file://test.bin"),
            name="test.bin",
            path=binary_file,
            mime_type="application/octet-stream",
        )
        mcp.add_resource(resource)

        async with client_session(mcp._mcp_server) as client:
            result = await client.read_resource(AnyUrl("file://test.bin"))
            assert isinstance(result.contents[0], BlobResourceContents)
            assert (
                result.contents[0].blob
                == base64.b64encode(b"Binary file data").decode()
            )


class TestServerResourceTemplates:
    async def test_resource_with_params(self):
        """Test that a resource with function parameters raises an error if the URI
        parameters don't match"""
        mcp = FastMCP()

        with pytest.raises(ValueError, match="Mismatch between URI parameters"):

            @mcp.resource("resource://data")
            def get_data_fn(param: str) -> str:
                return f"Data: {param}"

    async def test_resource_with_uri_params(self):
        """Test that a resource with URI parameters is automatically a template"""
        mcp = FastMCP()

        with pytest.raises(ValueError, match="Mismatch between URI parameters"):

            @mcp.resource("resource://{param}")
            def get_data() -> str:
                return "Data"

    async def test_resource_with_untyped_params(self):
        """Test that a resource with untyped parameters raises an error"""
        mcp = FastMCP()

        @mcp.resource("resource://{param}")
        def get_data(param) -> str:
            return "Data"

    async def test_resource_matching_params(self):
        """Test that a resource with matching URI and function parameters works"""
        mcp = FastMCP()

        @mcp.resource("resource://{name}/data")
        def get_data(name: str) -> str:
            return f"Data for {name}"

        async with client_session(mcp._mcp_server) as client:
            result = await client.read_resource(AnyUrl("resource://test/data"))
            assert isinstance(result.contents[0], TextResourceContents)
            assert result.contents[0].text == "Data for test"

    async def test_resource_mismatched_params(self):
        """Test that mismatched parameters raise an error"""
        mcp = FastMCP()

        with pytest.raises(ValueError, match="Mismatch between URI parameters"):

            @mcp.resource("resource://{name}/data")
            def get_data(user: str) -> str:
                return f"Data for {user}"

    async def test_resource_multiple_params(self):
        """Test that multiple parameters work correctly"""
        mcp = FastMCP()

        @mcp.resource("resource://{org}/{repo}/data")
        def get_data(org: str, repo: str) -> str:
            return f"Data for {org}/{repo}"

        async with client_session(mcp._mcp_server) as client:
            result = await client.read_resource(
                AnyUrl("resource://cursor/fastmcp/data")
            )
            assert isinstance(result.contents[0], TextResourceContents)
            assert result.contents[0].text == "Data for cursor/fastmcp"

    async def test_resource_multiple_mismatched_params(self):
        """Test that mismatched parameters raise an error"""
        mcp = FastMCP()

        with pytest.raises(ValueError, match="Mismatch between URI parameters"):

            @mcp.resource("resource://{org}/{repo}/data")
            def get_data_mismatched(org: str, repo_2: str) -> str:
                return f"Data for {org}"

        """Test that a resource with no parameters works as a regular resource"""
        mcp = FastMCP()

        @mcp.resource("resource://static")
        def get_static_data() -> str:
            return "Static data"

        async with client_session(mcp._mcp_server) as client:
            result = await client.read_resource(AnyUrl("resource://static"))
            assert isinstance(result.contents[0], TextResourceContents)
            assert result.contents[0].text == "Static data"

    async def test_template_to_resource_conversion(self):
        """Test that templates are properly converted to resources when accessed"""
        mcp = FastMCP()

        @mcp.resource("resource://{name}/data")
        def get_data(name: str) -> str:
            return f"Data for {name}"

        # Should be registered as a template
        assert len(mcp._resource_manager._templates) == 1
        assert len(await mcp.list_resources()) == 0

        # When accessed, should create a concrete resource
        resource = await mcp._resource_manager.get_resource("resource://test/data")
        assert isinstance(resource, FunctionResource)
        result = await resource.read()
        assert result == "Data for test"


class TestContextInjection:
    """Test context injection in tools."""

    async def test_context_detection(self):
        """Test that context parameters are properly detected."""
        mcp = FastMCP()

        def tool_with_context(x: int, ctx: Context) -> str:
            return f"Request {ctx.request_id}: {x}"

        tool = mcp._tool_manager.add_tool(tool_with_context)
        assert tool.context_kwarg == "ctx"

    async def test_context_injection(self):
        """Test that context is properly injected into tool calls."""
        mcp = FastMCP()

        def tool_with_context(x: int, ctx: Context) -> str:
            assert ctx.request_id is not None
            return f"Request {ctx.request_id}: {x}"

        mcp.add_tool(tool_with_context)
        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool("tool_with_context", {"x": 42})
            assert len(result.content) == 1
            content = result.content[0]
            assert isinstance(content, TextContent)
            assert "Request" in content.text
            assert "42" in content.text

    async def test_async_context(self):
        """Test that context works in async functions."""
        mcp = FastMCP()

        async def async_tool(x: int, ctx: Context) -> str:
            assert ctx.request_id is not None
            return f"Async request {ctx.request_id}: {x}"

        mcp.add_tool(async_tool)
        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool("async_tool", {"x": 42})
            assert len(result.content) == 1
            content = result.content[0]
            assert isinstance(content, TextContent)
            assert "Async request" in content.text
            assert "42" in content.text

    async def test_context_logging(self):
        """Test that context logging methods work."""
        mcp = FastMCP()

        def logging_tool(msg: str, ctx: Context) -> str:
            ctx.debug("Debug message")
            ctx.info("Info message")
            ctx.warning("Warning message")
            ctx.error("Error message")
            return f"Logged messages for {msg}"

        mcp.add_tool(logging_tool)
        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool("logging_tool", {"msg": "test"})
            assert len(result.content) == 1
            content = result.content[0]
            assert isinstance(content, TextContent)
            assert "Logged messages for test" in content.text

    async def test_optional_context(self):
        """Test that context is optional."""
        mcp = FastMCP()

        def no_context(x: int) -> int:
            return x * 2

        mcp.add_tool(no_context)
        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool("no_context", {"x": 21})
            assert len(result.content) == 1
            content = result.content[0]
            assert isinstance(content, TextContent)
            assert content.text == "42"

    async def test_context_resource_access(self):
        """Test that context can access resources."""
        mcp = FastMCP()

        @mcp.resource("test://data")
        def test_resource() -> str:
            return "resource data"

        @mcp.tool()
        async def tool_with_resource(ctx: Context) -> str:
            data = await ctx.read_resource("test://data")
            return f"Read resource: {data}"

        async with client_session(mcp._mcp_server) as client:
            result = await client.call_tool("tool_with_resource", {})
            assert len(result.content) == 1
            content = result.content[0]
            assert isinstance(content, TextContent)
            assert "Read resource: resource data" in content.text


class TestServerPrompts:
    """Test prompt functionality in FastMCP server."""

    async def test_prompt_decorator(self):
        """Test that the prompt decorator registers prompts correctly."""
        mcp = FastMCP()

        @mcp.prompt()
        def fn() -> str:
            return "Hello, world!"

        prompts = mcp._prompt_manager.list_prompts()
        assert len(prompts) == 1
        assert prompts[0].name == "fn"
        # Don't compare functions directly since validate_call wraps them
        content = await prompts[0].render()
        assert isinstance(content[0].content, TextContent)
        assert content[0].content.text == "Hello, world!"

    async def test_prompt_decorator_with_name(self):
        """Test prompt decorator with custom name."""
        mcp = FastMCP()

        @mcp.prompt(name="custom_name")
        def fn() -> str:
            return "Hello, world!"

        prompts = mcp._prompt_manager.list_prompts()
        assert len(prompts) == 1
        assert prompts[0].name == "custom_name"
        content = await prompts[0].render()
        assert isinstance(content[0].content, TextContent)
        assert content[0].content.text == "Hello, world!"

    async def test_prompt_decorator_with_description(self):
        """Test prompt decorator with custom description."""
        mcp = FastMCP()

        @mcp.prompt(description="A custom description")
        def fn() -> str:
            return "Hello, world!"

        prompts = mcp._prompt_manager.list_prompts()
        assert len(prompts) == 1
        assert prompts[0].description == "A custom description"
        content = await prompts[0].re