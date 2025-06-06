# src\toml_init\validators.py
from abc import ABC, abstractmethod
from toml_init.exceptions import InvalidConfigValueError, InvalidDefaultSchemaError

class Validator(ABC):
    """
    Base class for custom validators.
    Subclasses must implement `validate(value)`:
      - Return the value (possibly transformed) if valid
      - Raise InvalidConfigValueError on invalid input
    """

    @abstractmethod
    def validate(self, value):
        """Validate (and optionally coerce) `value`."""
        ...

    def __call__(self, value):
        return self.validate(value)

# Registry for custom validators
CUSTOM_VALIDATORS: dict[str, Validator] = {}


def register_validator(name: str, validator: Validator):
    """
    Register a Validator instance under the given name.
    """
    if not isinstance(validator, Validator):
        raise InvalidDefaultSchemaError(f"Validator for '{name}' must be a Validator instance.")
    CUSTOM_VALIDATORS[name] = validator
