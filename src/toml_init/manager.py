"""Core configuration management logic."""

from __future__ import annotations

import os
import argparse
import logging
import pytomlpp as toml
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Final,
    Mapping,
    MutableMapping,
    Optional,
    Set,
)
from datetime import date, datetime, time

from toml_init.exceptions import (
    MultipleConfigFilesError,
    InvalidDefaultSchemaError,
    InvalidConfigValueError,
    BlockConflictError,
)
from toml_init.validators import CUSTOM_VALIDATORS, Validator, register_validator


def _ensure_datetime(value: Any) -> datetime:
    """Validate that ``value`` is a :class:`~datetime.datetime`."""
    if isinstance(value, datetime):
        return value
    raise TypeError("value is not a datetime")


def _ensure_date(value: Any) -> date:
    """Validate that ``value`` is a :class:`~datetime.date` (not datetime)."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    raise TypeError("value is not a date")


def _ensure_time(value: Any) -> time:
    """Validate that ``value`` is a :class:`~datetime.time`."""
    if isinstance(value, time):
        return value
    raise TypeError("value is not a time")


def _ensure_list(value: Any) -> list[Any]:
    """Validate that ``value`` is a list."""
    if isinstance(value, list):
        return value
    raise TypeError("value is not a list")


def _ensure_dict(value: Any) -> dict[str, Any]:
    """Validate that ``value`` is a dictionary."""
    if isinstance(value, dict):
        return value
    raise TypeError("value is not a dict")


# Type coercion registry
TYPE_REGISTRY: Dict[str, Callable[[Any], Any]] = {
    "int": int,
    "float": float,
    "bool": bool,
    "str": str,
    "datetime": _ensure_datetime,
    "date": _ensure_date,
    "time": _ensure_time,
    "list": _ensure_list,
    "array": _ensure_list,
    "dict": _ensure_dict,
    "table": _ensure_dict,
}

# Keys that indicate a value is a schema object rather than a primitive default
SCHEMA_KEYS: Set[str] = {"defaultValue", "type", "min", "max", "allowedValues", "validator"}


def _infer_type(value: Any) -> str:
    """Return the schema type string for a Python value."""
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int) and not isinstance(value, bool):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, datetime):
        return "datetime"
    if isinstance(value, date) and not isinstance(value, datetime):
        return "date"
    if isinstance(value, time):
        return "time"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    raise InvalidDefaultSchemaError(
        f"Unsupported default value type: {type(value).__name__}"
    )


def _normalize_table(tbl: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Expand shorthand default values into explicit schema dictionaries."""
    normalized = {}
    for key, val in tbl.items():
        if isinstance(val, dict) and SCHEMA_KEYS.intersection(val.keys()):
            normalized[key] = val
        else:
            normalized[key] = {
                "defaultValue": val,
                "type": _infer_type(val),
            }
    return normalized


cwd = Path(os.getcwd())

DEFAULT_CONFIG_FOLDER_PATH: Final[Path] = cwd.joinpath("configs")
DEFAULT_CONFIG_DEFAULT_FOLDER_PATH: Final[Path] = DEFAULT_CONFIG_FOLDER_PATH.joinpath(
    "defaults"
)
DEFAULT_CONFIG_FILE_NAME: Final[str] = "config.toml"


def validate_setting(
    key_name: str, raw_value: Any, schema: Mapping[str, Any]
) -> Any:
    """Validate a configuration value against the provided schema.

    :param key_name: Name of the setting being validated
    :param raw_value: The value loaded from the master config
    :param schema: Parsed schema dictionary from the defaults
    :returns: The validated and coerced value
    :raises InvalidDefaultSchemaError: If the schema is malformed
    :raises InvalidConfigValueError: If ``raw_value`` fails validation
    """

    default_val = schema.get("defaultValue")
    expected_str = schema.get("type")
    min_allowed = schema.get("min")
    max_allowed = schema.get("max")
    allowed_vals = schema.get("allowedValues")
    validator_id = schema.get("validator")

    # Missing -> default
    if raw_value is None:
        return default_val

    # Type coercion
    if expected_str not in TYPE_REGISTRY:
        raise InvalidDefaultSchemaError(
            f"Type '{expected_str}' for '{key_name}' not supported."
        )
    try:
        coerced = TYPE_REGISTRY[expected_str](raw_value)
    except (ValueError, TypeError):
        raise InvalidConfigValueError(
            f"Key '{key_name}' expected type {expected_str}, got {type(raw_value).__name__}."
        )

    # Range checks for numbers
    if expected_str in ("int", "float"):
        num = float(coerced) if expected_str == "float" else int(coerced)
        if (min_allowed is not None and num < min_allowed) or (
            max_allowed is not None and num > max_allowed
        ):
            raise InvalidConfigValueError(
                f"Key '{key_name}'={num} outside range [{min_allowed}, {max_allowed}]."
            )
        coerced = int(num) if expected_str == "int" else float(num)

    # Allowed values
    if allowed_vals is not None and coerced not in allowed_vals:
        raise InvalidConfigValueError(
            f"Key '{key_name}' value {coerced} not in {allowed_vals}."
        )

    # Custom validator hook
    if validator_id:
        validator = CUSTOM_VALIDATORS.get(validator_id)
        if validator is None:
            raise InvalidDefaultSchemaError(
                f"Validator '{validator_id}' not found for '{key_name}'."
            )
        coerced = validator.validate(coerced)

    return coerced


class ConfigManager:
    """Manage merging and validation of configuration files."""
    def __init__(
        self,
        base_path: Path = DEFAULT_CONFIG_FOLDER_PATH,
        defaults_path: Path = DEFAULT_CONFIG_DEFAULT_FOLDER_PATH,
        master_filename: str = DEFAULT_CONFIG_FILE_NAME,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Create a new :class:`ConfigManager` instance.

        :param base_path: Directory containing the master config file
        :param defaults_path: Directory containing default templates
        :param master_filename: Name of the master config file
        :param logger: Optional :class:`logging.Logger` for diagnostics
        """
        self.base_path = base_path
        self.defaults_path = defaults_path or (base_path / "defaults")
        self.master_filename = master_filename
        self.logger = logger or logging.getLogger(__name__)

    def initialize(self, dry_run: bool = False) -> None:
        """Initialize the configuration directory structure and merge defaults."""
        # Create directories
        if not self.base_path.exists():
            self.logger.debug(f"Creating base dir {self.base_path}")
            self.base_path.mkdir(parents=True, exist_ok=True)
        if not self.defaults_path.exists():
            self.logger.debug(f"Creating defaults dir {self.defaults_path}")
            self.defaults_path.mkdir(parents=True, exist_ok=True)

        # Find master TOML
        toml_files = list(self.base_path.glob("*.toml"))
        if len(toml_files) > 1:
            raise MultipleConfigFilesError(
                f"Multiple TOML in {self.base_path}: {toml_files}"
            )
        elif toml_files:
            master_path = toml_files[0]
            self.logger.debug(f"Using existing master: {master_path}")
        else:
            master_path = self.base_path / self.master_filename
            self.logger.debug(f"No master found; will create {master_path}")
            if not dry_run:
                toml.dump({}, str(master_path))

        merged = self._merge_and_validate(master_path, dry_run)
        if merged and not dry_run:
            toml.dump(merged, str(master_path))
            self.logger.info(f"Wrote config to {master_path}")
        elif dry_run:
            self.logger.info(f"[Dry run] Would write config to {master_path}")

    def _merge_and_validate(
        self, master_path: Path, dry_run: bool
    ) -> Dict[str, Dict[str, Any]]:
        """Merge defaults with the master config and validate values."""
        try:
            base_doc = toml.load(str(master_path))
        except Exception:
            base_doc = {}

        seen = {}
        final = {}

        # Load defaults
        for df in sorted(self.defaults_path.glob("*.toml")):
            doc = toml.load(str(df))
            for blk, tbl in doc.items():
                if blk == "__meta__":
                    continue
                normalized = _normalize_table(tbl)
                if blk in seen and not self._schemas_compatible(seen[blk], normalized):
                    raise BlockConflictError(f"Conflict for block {blk}")
                seen[blk] = normalized

        # Validate or insert defaults
        for blk, schema_tbl in seen.items():
            self.logger.debug(f"Processing block {blk}")
            existing = base_doc.get(blk, {})
            validated = {}
            for k, schema in schema_tbl.items():
                raw = existing.get(k)
                try:
                    validated[k] = validate_setting(k, raw, schema)
                except InvalidConfigValueError as e:
                    self.logger.warning(
                        str(e) + f" -> resetting to default {schema['defaultValue']}"
                    )
                    validated[k] = schema["defaultValue"]
            # preserve extras
            for ek, ev in existing.items():
                if ek not in validated:
                    self.logger.debug(f"Keeping extra {ek} in {blk}")
                    validated[ek] = ev
            final[blk] = validated

        # Preserve user-only blocks
        for blk, tbl in base_doc.items():
            if blk not in final:
                self.logger.debug(f"Preserving user-only block {blk}")
                final[blk] = tbl

        return final

    def _schemas_compatible(
        self, s1: Mapping[str, Any], s2: Mapping[str, Any]
    ) -> bool:
        """Return ``True`` if two schema dictionaries are equivalent."""
        keys1 = set(s1.keys())
        keys2 = set(s2.keys())
        return keys1 == keys2 and all(s1[k] == s2[k] for k in keys1)

    def get_block(self, block_name: str) -> Dict[str, Any]:
        """Load a specific block from the merged configuration."""
        path = self.base_path / self.master_filename
        doc = toml.load(str(path))
        return doc.get(block_name, {})


def main() -> int:
    """Command-line entry point for ``toml-init``."""

    parser = argparse.ArgumentParser(description="Initialize or validate TOML configs.")
    parser.add_argument("-b", "--base", type=Path, default=Path.cwd() / "configs")
    parser.add_argument("-d", "--defaults", type=Path, default=None)
    parser.add_argument("-m", "--master", type=str, default="config.toml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logger = logging.getLogger("toml-init")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.setLevel(level)
    logger.addHandler(handler)

    defaults = args.defaults or (args.base / "defaults")
    cm = ConfigManager(args.base, defaults, args.master, logger)
    cm.initialize(dry_run=args.dry_run)
    return 0
