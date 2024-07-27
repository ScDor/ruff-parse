from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, RootModel


class FixAvailability(Enum):
    ALWAYS = "Fix is always available."
    SOMETIMES = "Fix is sometimes available."
    NOT = "Fix is not available."

    @property
    def one_word(self) -> str:
        match self:
            case FixAvailability.ALWAYS:
                return "Always"
            case FixAvailability.SOMETIMES:
                return "Sometimes"
            case FixAvailability.NOT:
                return "No"
            case _:
                raise ValueError


class Rule(BaseModel):
    class Config:
        frozen = True
        use_enum_values: Literal[True]

    name: str
    code: str
    linter: str
    summary: str
    message_formats: tuple[str, ...]
    fix: FixAvailability = Field(alias="fix")
    explanation: str
    preview: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "Code": self.code,
            "Name": self.name,
            "Fixable": self.fix.one_word,
            "Preview": self.preview,
            "Linter": self.linter,
        }

    @property
    def is_fixable(self) -> bool:
        return self.fix in {FixAvailability.ALWAYS, FixAvailability.SOMETIMES}


class RuleList(RootModel):
    root: list[Rule]


def parse_rules(output: str) -> set[Rule]:
    return set(RuleList.model_validate_json(output).root)
