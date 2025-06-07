"""Utilities for registering and running custom validators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict
from toml_init.exceptions import InvalidConfigValueError, InvalidDefaultSchemaError

class Validator(ABC):
    """
    Base class for custom validators.
    Subclasses must implement `validate(value)`:
      - Return the value (possibly transformed) if valid
      - Raise InvalidConfigValueError on invalid input
    """

    @abstractmethod
    def validate(self, value: Any) -> Any:
        """Validate (and optionally coerce) `value`."""
        ...

    def __call__(self, value: Any) -> Any:
        return self.validate(value)

# Registry for custom validators
CUSTOM_VALIDATORS: Dict[str, Validator] = {}


def register_validator(name: str, validator: Validator) -> None:
    """
    Register a Validator instance under the given name.
    """
    if not isinstance(validator, Validator):
        raise InvalidDefaultSchemaError(f"Validator for '{name}' must be a Validator instance.")
    CUSTOM_VALIDATORS[name] = validator
