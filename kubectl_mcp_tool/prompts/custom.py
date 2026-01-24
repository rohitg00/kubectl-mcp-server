"""
Custom prompt loading and rendering system for kubectl-mcp-server.

Supports user-defined workflow prompts via TOML configuration file with
Mustache-style template syntax ({{variable}}) and conditional sections.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("mcp-server")


@dataclass
class PromptArgument:
    """Definition of a prompt argument."""
    name: str
    description: str = ""
    required: bool = False
    default: str = ""


@dataclass
class PromptMessage:
    """A single message in a prompt conversation."""
    role: str  # "user" or "assistant"
    content: str


@dataclass
class CustomPrompt:
    """A custom prompt definition."""
    name: str
    description: str
    title: str = ""
    arguments: List[PromptArgument] = field(default_factory=list)
    messages: List[PromptMessage] = field(default_factory=list)


def render_prompt(prompt: CustomPrompt, args: Dict[str, str]) -> List[PromptMessage]:
    """
    Render prompt messages with argument substitution using {{arg_name}} syntax.

    Supports:
    - Simple substitution: {{variable}} -> value
    - Conditional sections: {{#variable}}content{{/variable}} (shown if variable is truthy)
    - Inverse sections: {{^variable}}content{{/variable}} (shown if variable is falsy)

    Args:
        prompt: The CustomPrompt to render
        args: Dictionary of argument names to values

    Returns:
        List of PromptMessage with rendered content
    """
    rendered = []
    for msg in prompt.messages:
        content = msg.content

        # Process conditional sections ({{#var}}...{{/var}})
        # These are shown only if the variable exists and is truthy
        def process_conditional(match):
            var_name = match.group(1)
            section_content = match.group(2)
            var_value = args.get(var_name, "")
            # Only render section if variable exists and is not empty/false
            if var_value and var_value.lower() not in ("false", "0", "no"):
                # Recursively process the section content for variable substitution
                processed = section_content
                for key, value in args.items():
                    processed = processed.replace(f"{{{{{key}}}}}", str(value))
                return processed
            return ""

        content = re.sub(
            r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}',
            process_conditional,
            content,
            flags=re.DOTALL
        )

        # Process inverse sections ({{^var}}...{{/var}})
        # These are shown only if the variable is missing or falsy
        def process_inverse(match):
            var_name = match.group(1)
            section_content = match.group(2)
            var_value = args.get(var_name, "")
            # Only render section if variable is missing or falsy
            if not var_value or var_value.lower() in ("false", "0", "no"):
                processed = section_content
                for key, value in args.items():
                    processed = processed.replace(f"{{{{{key}}}}}", str(value))
                return processed
            return ""

        content = re.sub(
            r'\{\{\^(\w+)\}\}(.*?)\{\{/\1\}\}',
            process_inverse,
            content,
            flags=re.DOTALL
        )

        # Simple variable substitution
        for key, value in args.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))

        # Remove unsubstituted optional placeholders (simple variables only)
        content = re.sub(r'\{\{[^#^/][^}]*\}\}', '', content)

        # Clean up any remaining empty lines from removed sections
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

        rendered.append(PromptMessage(role=msg.role, content=content.strip()))

    return rendered


def load_prompts_from_config(config: dict) -> List[CustomPrompt]:
    """
    Load prompts from config dict (from TOML).

    Expected config structure:
    {
        "prompts": [
            {
                "name": "debug-pod",
                "title": "Debug Pod Issues",
                "description": "Diagnose pod problems",
                "arguments": [
                    {"name": "pod_name", "required": True, "description": "Pod to debug"},
                    {"name": "namespace", "required": False, "default": "default"}
                ],
                "messages": [
                    {"role": "user", "content": "Debug pod {{pod_name}} in namespace {{namespace}}"}
                ]
            }
        ]
    }

    Args:
        config: Dictionary loaded from TOML configuration

    Returns:
        List of CustomPrompt objects
    """
    prompts = []

    prompt_configs = config.get("prompts", [])
    if not prompt_configs:
        return prompts

    for prompt_config in prompt_configs:
        try:
            # Parse arguments
            arguments = []
            for arg_config in prompt_config.get("arguments", []):
                arg = PromptArgument(
                    name=arg_config.get("name", ""),
                    description=arg_config.get("description", ""),
                    required=arg_config.get("required", False),
                    default=arg_config.get("default", "")
                )
                if arg.name:  # Only add valid arguments
                    arguments.append(arg)

            # Parse messages
            messages = []
            for msg_config in prompt_config.get("messages", []):
                msg = PromptMessage(
                    role=msg_config.get("role", "user"),
                    content=msg_config.get("content", "")
                )
                if msg.content:  # Only add non-empty messages
                    messages.append(msg)

            # Create prompt
            prompt = CustomPrompt(
                name=prompt_config.get("name", ""),
                title=prompt_config.get("title", prompt_config.get("name", "")),
                description=prompt_config.get("description", ""),
                arguments=arguments,
                messages=messages
            )

            if prompt.name:  # Only add valid prompts
                prompts.append(prompt)
                logger.debug(f"Loaded custom prompt: {prompt.name}")

        except Exception as e:
            logger.warning(f"Failed to parse prompt config: {e}")
            continue

    return prompts


def load_prompts_from_toml_file(file_path: str) -> List[CustomPrompt]:
    """
    Load prompts from a TOML file.

    Args:
        file_path: Path to the TOML configuration file

    Returns:
        List of CustomPrompt objects
    """
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            logger.warning("TOML parsing not available. Install tomli for Python < 3.11")
            return []

    try:
        with open(file_path, "rb") as f:
            config = tomllib.load(f)
        return load_prompts_from_config(config)
    except FileNotFoundError:
        logger.debug(f"Custom prompts file not found: {file_path}")
        return []
    except Exception as e:
        logger.warning(f"Failed to load prompts from {file_path}: {e}")
        return []


def validate_prompt_args(prompt: CustomPrompt, args: Dict[str, str]) -> List[str]:
    """
    Validate that all required arguments are provided.

    Args:
        prompt: The CustomPrompt to validate against
        args: Dictionary of argument names to values

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    for arg in prompt.arguments:
        if arg.required and arg.name not in args:
            errors.append(f"Missing required argument: {arg.name}")
        elif arg.required and not args.get(arg.name):
            errors.append(f"Required argument cannot be empty: {arg.name}")

    return errors


def apply_defaults(prompt: CustomPrompt, args: Dict[str, str]) -> Dict[str, str]:
    """
    Apply default values for missing optional arguments.

    Args:
        prompt: The CustomPrompt with argument definitions
        args: Dictionary of argument names to values

    Returns:
        New dictionary with defaults applied
    """
    result = dict(args)

    for arg in prompt.arguments:
        if arg.name not in result and arg.default:
            result[arg.name] = arg.default

    return result


def get_prompt_schema(prompt: CustomPrompt) -> Dict[str, Any]:
    """
    Generate JSON Schema for prompt arguments.

    Args:
        prompt: The CustomPrompt to generate schema for

    Returns:
        JSON Schema dictionary
    """
    properties = {}
    required = []

    for arg in prompt.arguments:
        properties[arg.name] = {
            "type": "string",
            "description": arg.description or f"Argument: {arg.name}"
        }
        if arg.default:
            properties[arg.name]["default"] = arg.default
        if arg.required:
            required.append(arg.name)

    return {
        "type": "object",
        "properties": properties,
        "required": required
    }
