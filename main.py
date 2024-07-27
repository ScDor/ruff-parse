import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

from loguru import logger
from packaging.version import Version

from models.configured_rules import (
    _DEFAULT_CONFIGURATION,
    ConfiguredRules,
    _SupportedConfigurationFileNames,
    parse_configured_rules,
)
from rule import Rule, parse_rules


class Ruff(NamedTuple):
    version: Version
    rules: list[Rule]
    configuration: ConfiguredRules | None


def parse_all(
    project_path: Path,
    ruff_config_path: Path | None = None,
    default_config_if_missing: bool = True,
) -> Ruff:
    """Runs ruff locally and returns its version, configured rules and known rules."""
    try:
        ruff_version = Version(
            subprocess.run(
                ["ruff", "--version"],
                check=True,
                text=True,
                capture_output=True,
            ).stdout.split(" ")[1]  # ruff's output is `ruff x.y.z`
        )
        logger.debug(f"parsed {ruff_version=!s}")

    except FileNotFoundError:
        logger.error("Make sure ruff is installed (pip install ruff)")
        sys.exit(1)

    # Now when ruff is found, assume the following commands will run properly
    rules = parse_rules(
        subprocess.run(
            ("ruff", "rule", "--all", "--output-format=json"),
            check=True,
            text=True,
            capture_output=True,
        ).stdout
    )
    logger.debug(f"read {len(rules)} rules from JSON output")

    configured_rules = None

    if ruff_config_path:
        configured_rules = parse_configured_rules(ruff_config_path)
    else:
        for file_name in _SupportedConfigurationFileNames:
            if (path := project_path / file_name.value).exists():
                configured_rules = parse_configured_rules(path)
                break
        else:  # none of the files
            if default_config_if_missing:
                configured_rules = _DEFAULT_CONFIGURATION

    if configured_rules is None:
        logger.error("Could not find a ruff configuration file")
        sys.exit(1)

    return Ruff(ruff_version, rules, configured_rules)
