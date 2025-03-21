"""Example pydantic models."""

import enum
import json
import pathlib
from typing import Annotated, Literal
import pydantic

Name = Annotated[
    str,
    pydantic.Field(
        title="Project name",
        description="A name for this docscraft project. (This text shows up in the JSON schema)",
        examples=["snapcraft", "charmcraft", "rockcraft"],
        max_length=79,
    )
]

class DocType(enum.Enum):
    """The type of documentation in this project."""

    END_USER = "end-user"
    """End user documentation.

    This is documentation for people who are using the product. For example, the end
    user of snapcraft's documentation is someone who's building or maintaining a snap.
    """
    DEVELOPER = "developer"
    """Developer documentation.

    This is documentation for someone who wants to contribute to the product's source
    code. It will often contain things like how to set up your development environment
    and linting rules.
    """
    DOCUMENTER = "documenter"
    """Documenter documentation.

    This is documentation aimed at someone who wants to work on the documentation for
    a product. It should contain things like how to set up a documentation environment,
    a style guide, etc. Examples include:

    - `The Ubuntu style guide <https://docs.ubuntu.com/styleguide/en/>`_
    - https://canonical-documentation-with-sphinx-and-readthedocscom.readthedocs-hosted.com/
    """


class DocBuild(pydantic.BaseModel):
    """A single documentation build option."""

    path: pathlib.Path
    """The relative path to the documentation directory from docscraft.yaml."""
    build_command: list[str]


class Part(pydantic.BaseModel):

    plugin: str
    source: str


class Docscraft(pydantic.BaseModel):
    """docscraft.yaml

    This file describes how Docscraft will build your documentation.
    We have to be careful with this docstring because it gets used in the schema but
    could also be used in the docs themselves.
    """

    name: Name
    """The name of this docsraft project.

    This text shows up on the documentation page.
    """

    testKey: int = pydantic.Field(
      description="json description",
      examples=[1, 2, 3]
    )
    """is this thing on?"""

    type: DocType

    build: DocBuild
    """The build information for this build."""

    parts: dict[str, Part] = pydantic.Field(
        description="Mapping of part names to their information.",
        examples=[
            {"my-part": {"plugin": "nil"}},
        ]
    )


with open("schema.json", "w+") as f:
    print(json.dumps(Docscraft.model_json_schema(), indent=2), file=f)
