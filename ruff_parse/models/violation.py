from typing import Any

from pydantic import BaseModel, Field, RootModel


class _Location(BaseModel):
    column: int
    row: int


class _Edit(BaseModel):
    content: str
    end_location: _Location
    location: _Location


class _Fix(BaseModel):
    applicability: str
    edits: tuple[_Edit, ...]
    message: str | None


class Violation(BaseModel):
    cell: Any  # TODO handle notebook output
    code: str
    end_location: _Location
    file_name: str = Field(alias="filename")
    fix: _Fix | None
    location: _Location
    message: str
    noqa_row: int
    url: str


class _ViolationList(RootModel):
    root: list[Violation]


def parse_violations(json_output: str) -> list[Violation]:
    return _ViolationList.model_validate_json(json_output).root
