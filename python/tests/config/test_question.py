from collections.abc import Sequence
from pathlib import Path
from typing import Union

from cattrs.preconf.json import make_converter
from oes.interview.config.question import structure_questions
from oes.interview.input.field import structure_field
from oes.interview.input.question import Question
from oes.interview.input.types import Field, Locator
from oes.interview.variables.locator import parse_locator
from oes.template import Template, structure_template

converter = make_converter()

converter.register_structure_hook(Template, structure_template)

converter.register_structure_hook(Locator, lambda v, t: parse_locator(v))

converter.register_structure_hook_func(
    lambda cls: cls == Sequence[Union[Question, Path]],
    lambda v, t: structure_questions(converter, v, t),
)

converter.register_structure_hook_func(
    lambda cls: cls is Field, lambda v, t: structure_field(converter, v, t)
)

items = [
    "tests/test_data/questions.yml",
    {
        "id": "Test",
    },
]


def test_structure_questions():
    questions = converter.structure(items, Sequence[Union[Question, Path]])
    assert len(questions) == 2
    assert questions[0].id == "q1"
    assert questions[-1].id == "Test"
