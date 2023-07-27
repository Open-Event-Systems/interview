"""Loading questions."""
from collections.abc import Sequence
from pathlib import Path

from cattrs import Converter
from oes.interview.config.file import load_config_file, resolve_config_path
from oes.interview.input.question import Question


def structure_questions(
    converter: Converter, v: object, t: object
) -> Sequence[Question]:
    """Load questions or paths to files with questions."""
    questions: list[Question] = []

    if isinstance(v, Sequence) and not isinstance(v, str):
        for entry in v:
            questions.extend(_parse_question_or_path(converter, entry))

        return tuple(questions)
    else:
        raise TypeError(f"Invalid question set: {v}")


def _parse_question_or_path(converter: Converter, obj: object) -> Sequence[Question]:
    if isinstance(obj, (str, Path)):
        with resolve_config_path(obj) as config_path:
            doc = load_config_file(config_path)
            return converter.structure(doc, Sequence[Question])
    else:
        return (converter.structure(obj, Question),)
