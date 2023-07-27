from collections.abc import Sequence

from oes.interview.input.field_types.text import TextField
from oes.interview.input.question import Question
from oes.interview.interview.interview import Interview
from oes.interview.serialization import converter
from oes.interview.variables.locator import parse_locator
from oes.template import Template
from ruamel.yaml import YAML

interview1_doc = """
- id: int1
  questions:
    - id: q1
      fields:
        - set: name
          type: text
          label: Name

"""

yaml = YAML(typ="safe")


def test_parse_interview():
    doc = yaml.load(interview1_doc)
    interviews = converter.structure(doc, Sequence[Interview])
    assert len(interviews) == 1

    int1: Interview = interviews[0]
    assert int1.id == "int1"
    assert len(int1.question_bank) == 1
    assert int1.question_bank["q1"] == Question(
        id="q1", fields=(TextField(set=parse_locator("name"), label=Template("Name")),)
    )
