import logging
import os
import sys


def set_logger_with_envs(logger: logging.Logger):
    """
    Set the logger with logging related environment variables

    TODO: This is temporary logger setting function. logger setting needs to be organized in the future.

    Args:
        logger: logger to set with environment variables
    """

    logger.propagate = False

    # log level setting
    if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true"):
        # MCP_DEBUG has higher priority than KUBECTL_MCP_LOG_LEVEL
        log_level = logging.DEBUG
    elif log_level_str := os.environ.get("KUBECTL_MCP_LOG_LEVEL"):
        # log_level_str is "DEBUG", "INFO", "WARNING", or "ERROR"
        log_level = getattr(logging, log_level_str.upper())
    else:
        log_level = logging.INFO

    logger.setLevel(level=log_level)

    # NOTE: some script (e.g. mcp_server.py) loads logger twice when it runs. To prevent duplicate logging.
    if not logger.handlers:
        # logger handler setting
        log_file = os.environ.get("MCP_LOG_FILE")
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler(sys.stderr)

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
