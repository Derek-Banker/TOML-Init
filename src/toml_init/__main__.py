"""Entry point for the ``toml-init`` console script."""

from __future__ import annotations

import sys
from typing import NoReturn
from toml_init.manager import main


if __name__ == "__main__":  # pragma: no cover - direct CLI execution
    def _entry() -> NoReturn:
        sys.exit(main())

    _entry()
