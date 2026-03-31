from pydantic import BaseModel


def structured_response(data: dict, model: type[BaseModel]) -> dict:
    """Validate data against a Pydantic model and return a clean dict.

    FastMCP emits both structuredContent and TextContent when output_schema is set.
    This function validates the data before FastMCP sees it.
    """
    validated = model.model_validate(data)
    return validated.model_dump()
