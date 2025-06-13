# TOML-Init

A lightweight Python library for auto-creating and validating TOML-based configuration files from one or more default templates.

For use where you use multiple relatively independent modules that need config values and you want a standardized way to handle, implement, and validate.

---

## Defaults

| Variable                             | Value                                   |
|--------------------------------------|-----------------------------------------|
| `DEFAULT_CONFIG_FOLDER_PATH`         | \<Current Working Directory\>/config    |
| `DEFAULT_CONFIG_DEFAULT_FOLDER_PATH` | \<Current Working Directory\>/defaults  |
| `DEFAULT_CONFIG_FILE`                | "config.toml"                           |


## Features
* **Automatic directory setup**

  * Ensures your primary `configs/` directory and its `defaults/` subdirectory exist (creates them if missing).

* **Defaults merging**

  * Scans all `*.toml` files under `configs/defaults/`. Each top-level TOML table is treated as a “block” of settings.
  * Merges multiple default files into a single master `config.toml`, with conflict detection.

* **Schema-driven validation**

  * Each setting may be declared in two ways:

    1. **Simple**: `KEY = <defaultValue>`
    2. **Full**: `KEY = { defaultValue = <...>, type = "<int|float|bool|str>", min = <...>, max = <...>, allowedValues = [...], validator = "<name>" }`
  * Supports numeric range checks (`min`/`max`), enumerations (`allowedValues`), and custom validation hooks.

* **Custom validators**

  * Implement by subclassing `Validator` and registering via `register_validator("name", instance)`.
  * Allows arbitrary user‑defined checks (e.g. path existence, regex match).

* **Preserves user overrides**

  * If users manually edit `config.toml`, extra keys remain intact.
  * Invalid values are reset to defaults with a logged warning.

* **CLI & programmatic API**

  * Installable console script: `toml-init` for quick command-line setup.
  * `ConfigManager` class for embedding in Python code.

* **Dry‑run & logging**

  * `--dry-run` to validate without writing changes.
  * Verbose mode with `--verbose` for debug logging.

---

## Installation

```bash
pip install toml-init
```

## Package Structure

```
toml_init
├── __init__.py
├── __main__.py
├── exceptions.py
├── validators.py
└── manager.py
```

## Quickstart (Python)

```python
from pathlib import Path
from toml_init import ConfigManager, register_validator, Validator

# Optional: register a custom validator
class PathExistsValidator(Validator):
    def validate(self, value):
        from pathlib import Path as P
        if not (isinstance(value, str) and P(value).exists()):
            raise InvalidConfigValueError(f"Path not found: {value}")
        return value

register_validator("path_exists", PathExistsValidator())

# Initialize and validate
cm = ConfigManager(
    base_path=Path("configs"),
    defaults_path=Path("configs/defaults"),
    master_filename="config.toml"
)
cm.initialize(dry_run=False)

# Access validated settings
settings = cm.get_block("QuickBooks.Invoices.Saver")
print(settings["WINDOW_LOAD_DELAY"])  # e.g. 0.5
```

## Quickstart (CLI)

```bash
# Create or validate configs in ./configs (defaults in ./configs/defaults)
toml-init

# Verbose & dry-run (no file writes)
toml-init --verbose --dry-run

# Custom paths
 toml-init --base /etc/myapp/configs \
           --defaults /etc/myapp/configs/defaults \
           --master settings.toml
```

## Example Project

A working sample lives under `example_project/`. Run `python run_demo.py` inside
that directory to generate `config.toml` using the defaults in
`configs/defaults/example_defaults.toml`.

## Default File Format

Place your default templates in `configs/defaults/`. Each file may define **multiple** blocks (tables):

```toml
# defaults/app_defaults.toml

[__meta__]
name = "Config - QuickBooks Invoice Saver"
module_version = "0.1.0"

[QuickBooks.Invoices.Saver]
SHOW_TOASTS = true
WINDOW_LOAD_DELAY  = { defaultValue = 0.5,  type = "float", min = 0.0 }
NAVIGATION_DELAY   = { defaultValue = 0.15, type = "float", min = 0.0 }

[MyApp.Logging]
LEVEL       = { defaultValue = "INFO", type = "str", allowedValues = ["DEBUG","INFO","WARN","ERROR"] }
ENABLE_LOGS = { defaultValue = true,   type = "bool" }
```

* **Block names** = the table names (e.g. `QuickBooks.Invoices.Saver`).
* **Settings** under each block may be:

  * A primitive default: `KEY = 123` (shorthand for a setting with only `defaultValue`).
  * A full schema object: specifying `type`, optional `min`/`max`, `allowedValues`, and `validator`.
* An optional `[__meta__]` table may be present and is ignored by the library.

## Supported Types

* `int`, `float`, `bool`, `str`, `list`, `dict`, `datetime`, `date`, `time`
* Numeric range checks with `min`/`max`
* Enumerations via `allowedValues`
* Custom hooks via `validator` (must match a registered `Validator`)

---

## Exception Hierarchy

* `TomlInitError` (base)

  * `MultipleConfigFilesError`
  * `InvalidDefaultSchemaError`
  * `InvalidConfigValueError`
  * `BlockConflictError`

Catch these to handle specific error cases gracefully.

---

## Potential Future Features
| Feature               | Description                                                          |
|-----------------------|----------------------------------------------------------------------|
| Multiple config files | Will support having separate config files for organization purposes? |
| Comment injection     | Allow comments to be specified in the defaults?                      |
