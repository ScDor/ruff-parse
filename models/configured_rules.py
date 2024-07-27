from enum import Enum
from pathlib import Path
from typing import NamedTuple

import tomllib
from loguru import logger

from rule import Rule

_MIN_RULE_CODE_LEN = 4
_DEFAULT_SELECT_RULES = ("E", "F")


def _convert_rule_codes_to_objects(raw_codes: set[str], rules: set[Rule]) -> set[Rule]:
    """
    Convert code values (e.g. `E401`), categories (e.g. `E`) and `ALL`, into Rule objects
    """
    if "ALL" in raw_codes:
        logger.debug("`ALL` found, returning all Rule objects")
        return rules

    code_to_rule = {rule.code: rule for rule in rules}

    result: set[Rule] = set()

    for code in raw_codes:
        if code.isalpha() or len(code) < _MIN_RULE_CODE_LEN:
            code_rules = tuple(
                rule for rule in rules if rule.code.removeprefix(code).isnumeric()
            )
            logger.debug(
                f"assuming {code} is a category, adding {len(code_rules)} rules: {sorted(r.code for r in code_rules)!s}"
            )
            result.update(code_rules)
            # TODO are there cases of category names with len>=MIN_RULE_CODE_LEN, mixing alpha&digits?
        else:
            result.add(code_to_rule[code])

    logger.debug(f"parsed {len(result)} rules from {len(raw_codes)} rule codes")
    return result


class ConfiguredRules(NamedTuple):
    selected_rules: set[Rule]
    ignored_rules: set[Rule]

    @property
    def all_rules(self) -> set[Rule]:
        return self.selected_rules | self.ignored_rules


_DEFAULT_CONFIGURATION = ConfiguredRules(
    select=set(_DEFAULT_SELECT_RULES), ignore=set()
)


class _SupportedConfigurationFileNames(Enum):
    PYPROJECT = "pyproject.toml"
    RUFF = "ruff.toml"
    DOT_RUFF = ".ruff.toml"


def parse_configured_rules(
    path: Path,
    default_if_missing_section: bool = True,
) -> ConfiguredRules:
    try:
        toml = tomllib.loads(path.read_text())
    except ValueError as e:
        raise ValueError(f"could not parse toml at {path}") from e

    match path.name:
        case _SupportedConfigurationFileNames.PYPROJECT.value:
            if (ruff_section := toml.get("tool", {}).get("ruff")) is None:
                message = f"could not find `tool` or `tool.ruff` in {path.name}"

                if default_if_missing_section:
                    logger.warning(f"{message}, using default")
                    return _DEFAULT_CONFIGURATION
                raise ValueError(message)

        case (
            _SupportedConfigurationFileNames.RUFF.value
            | _SupportedConfigurationFileNames.DOT_RUFF.value
        ):
            ruff_section = toml
        case _:
            raise ValueError(
                f"config file must be named `pyproject.toml`, `ruff.toml` or `.ruff.toml`. (Got {path.name})"
            )

    ruff_lint_section = ruff_section.get(
        "lint", ruff_section
    )  # Backwards-compatible. Newer versions use `ruff.lint`

    raw_select = set(ruff_lint_section.get("select", ()))
    logger.debug(f"parsed {len(raw_select)} `select` values")

    raw_ignore = set(ruff_lint_section.get("ignore", ()))
    logger.debug(f"parsed {len(raw_ignore)} `ignore` values")

    return ConfiguredRules(
        select=_convert_rule_codes_to_objects(raw_select),
        ignore=_convert_rule_codes_to_objects(raw_ignore),
    )
