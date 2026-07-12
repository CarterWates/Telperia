from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SchemaValidationError(ValueError):
    pass


def validate_result_package(package: dict[str, Any], schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text())
    _validate(package, schema, path="$", root_schema=schema)


def _validate(value: Any, schema: dict[str, Any], path: str, root_schema: dict[str, Any]) -> None:
    if "$ref" in schema:
        schema = _resolve_ref(schema["$ref"], root_schema)

    if "oneOf" in schema:
        _validate_one_of(value, schema["oneOf"], path, root_schema)
        return

    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(f"{path} must equal {schema['const']!r}")

    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(f"{path} must be one of {schema['enum']!r}")

    expected_type = schema.get("type")
    if expected_type is not None and not _matches_type(value, expected_type):
        raise SchemaValidationError(f"{path} has invalid type")

    if isinstance(value, dict):
        _validate_object(value, schema, path, root_schema)
    elif isinstance(value, list):
        _validate_array(value, schema, path, root_schema)
    elif isinstance(value, str):
        _validate_string(value, schema, path)
    elif isinstance(value, int | float):
        _validate_number(value, schema, path)


def _validate_object(value: dict[str, Any], schema: dict[str, Any], path: str, root_schema: dict[str, Any]) -> None:
    required = schema.get("required", [])
    for key in required:
        if key not in value:
            raise SchemaValidationError(f"{path}.{key} is required")

    properties = schema.get("properties", {})
    if schema.get("additionalProperties") is False:
        extras = set(value) - set(properties)
        if extras:
            extra = sorted(extras)[0]
            raise SchemaValidationError(f"{path}.{extra} is not allowed")

    for key, item in value.items():
        if key in properties:
            _validate(item, properties[key], f"{path}.{key}", root_schema)


def _validate_array(value: list[Any], schema: dict[str, Any], path: str, root_schema: dict[str, Any]) -> None:
    min_items = schema.get("minItems")
    if min_items is not None and len(value) < min_items:
        raise SchemaValidationError(f"{path} must contain at least {min_items} items")

    if schema.get("uniqueItems") and len(value) != len(set(value)):
        raise SchemaValidationError(f"{path} must contain unique items")

    item_schema = schema.get("items")
    if item_schema is not None:
        for index, item in enumerate(value):
            _validate(item, item_schema, f"{path}[{index}]", root_schema)


def _validate_string(value: str, schema: dict[str, Any], path: str) -> None:
    min_length = schema.get("minLength")
    if min_length is not None and len(value) < min_length:
        raise SchemaValidationError(f"{path} is too short")


def _validate_number(value: int | float, schema: dict[str, Any], path: str) -> None:
    minimum = schema.get("minimum")
    if minimum is not None and value < minimum:
        raise SchemaValidationError(f"{path} must be at least {minimum}")

    maximum = schema.get("maximum")
    if maximum is not None and value > maximum:
        raise SchemaValidationError(f"{path} must be at most {maximum}")

    exclusive_minimum = schema.get("exclusiveMinimum")
    if exclusive_minimum is not None and value <= exclusive_minimum:
        raise SchemaValidationError(f"{path} must be greater than {exclusive_minimum}")


def _matches_type(value: Any, expected_type: str | list[str]) -> bool:
    expected_types = [expected_type] if isinstance(expected_type, str) else expected_type
    return any(_matches_single_type(value, item) for item in expected_types)


def _matches_single_type(value: Any, expected_type: str) -> bool:
    if expected_type == "null":
        return value is None
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    return True


def _validate_one_of(value: Any, options: list[dict[str, Any]], path: str, root_schema: dict[str, Any]) -> None:
    matches = 0
    for option in options:
        try:
            _validate(value, option, path, root_schema)
        except SchemaValidationError:
            continue
        matches += 1

    if matches != 1:
        raise SchemaValidationError(f"{path} must match exactly one schema")


def _resolve_ref(ref: str, root_schema: dict[str, Any]) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise SchemaValidationError(f"unsupported schema reference: {ref}")

    target: Any = root_schema
    for part in ref[2:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(target, dict) or key not in target:
            raise SchemaValidationError(f"unknown schema reference: {ref}")
        target = target[key]

    if not isinstance(target, dict):
        raise SchemaValidationError(f"invalid schema reference: {ref}")
    return target
