"""Public API for the :mod:`toml_init` package."""

from __future__ import annotations

from typing import List

from toml_init.manager import ConfigManager, main
from toml_init.exceptions import (
    TomlInitError,
    MultipleConfigFilesError,
    InvalidDefaultSchemaError,
    InvalidConfigValueError,
    BlockConflictError,
)
from toml_init.validators import register_validator, Validator, CUSTOM_VALIDATORS
from toml_init.encryption_manager import EncryptionManager

__all__: List[str] = [
    "ConfigManager",
    "main",
    "EncryptionManager",
    "TomlInitError",
    "MultipleConfigFilesError",
    "InvalidDefaultSchemaError",
    "InvalidConfigValueError",
    "BlockConflictError",
    "register_validator",
    "Validator",
    "CUSTOM_VALIDATORS",
]
