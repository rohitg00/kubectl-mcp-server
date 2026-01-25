from .prompts import register_prompts
from .custom import (
    CustomPrompt,
    PromptArgument,
    PromptMessage,
    render_prompt,
    load_prompts_from_config,
    load_prompts_from_toml_file,
    validate_prompt_args,
    apply_defaults,
    get_prompt_schema,
)
from .builtin import (
    BUILTIN_PROMPTS,
    get_builtin_prompts,
    get_builtin_prompt_by_name,
    CLUSTER_HEALTH_CHECK,
    DEBUG_WORKLOAD,
    RESOURCE_USAGE,
    SECURITY_POSTURE,
    DEPLOYMENT_CHECKLIST,
    INCIDENT_RESPONSE,
)

__all__ = [
    # Main registration function
    "register_prompts",
    # Custom prompt types and functions
    "CustomPrompt",
    "PromptArgument",
    "PromptMessage",
    "render_prompt",
    "load_prompts_from_config",
    "load_prompts_from_toml_file",
    "validate_prompt_args",
    "apply_defaults",
    "get_prompt_schema",
    # Built-in prompts
    "BUILTIN_PROMPTS",
    "get_builtin_prompts",
    "get_builtin_prompt_by_name",
    "CLUSTER_HEALTH_CHECK",
    "DEBUG_WORKLOAD",
    "RESOURCE_USAGE",
    "SECURITY_POSTURE",
    "DEPLOYMENT_CHECKLIST",
    "INCIDENT_RESPONSE",
]
