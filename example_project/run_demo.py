from pathlib import Path
from toml_init import ConfigManager


def main() -> None:
    base_path = Path(__file__).parent / "configs"
    defaults_path = base_path / "defaults"
    cm = ConfigManager(
        base_path=base_path,
        defaults_path=defaults_path,
        master_filename="config.toml",
    )
    cm.initialize(dry_run=False)

    general = cm.get_block("DemoApp.General")
    features = cm.get_block("DemoApp.Features")

    print("General settings:", general)
    print("Feature flags:", features)


if __name__ == "__main__":
    main()
