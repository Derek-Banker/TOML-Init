"""Exception hierarchy for :mod:`toml_init`."""


class TomlInitError(Exception):
    """Base class for all toml-init exceptions."""
    pass

class MultipleConfigFilesError(TomlInitError):
    """Raised if more than one .toml is found in the primary config folder."""
    pass

class InvalidDefaultSchemaError(TomlInitError):
    """Raised if a default file's schema is malformed."""
    pass

class InvalidConfigValueError(TomlInitError):
    """Raised when a loaded config value fails validation."""
    pass

class BlockConflictError(TomlInitError):
    """Raised if two defaults define the same block with incompatible schemas."""
    pass
