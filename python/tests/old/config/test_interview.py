from pathlib import Path

import pytest
from cattrs import BaseValidationError
from oes.interview_old.config.interview import Interview
from oes.interview_old.serialization import converter


def test_parse_questions():
    obj = {
        "id": "test",
        "title": "Test Interview",
        "questions": [Path("tests/test_data/questions.yml")],
        "steps": [{"ask": "name"}],
    }

    interview = converter.structure(obj, Interview)
    assert interview.question_bank.get_question("name") is not None
    assert interview.question_bank.get_question("optional-text") is not None
    assert interview.question_bank.get_question("test_not_found") is None


def test_parse_no_file():
    obj = {
        "id": "test",
        "title": "Test Interview",
        "questions": [Path("tests/test_data/not_found.yml")],
        "steps": [],
    }

    with pytest.raises(BaseValidationError):
        converter.structure(obj, Interview)


def test_parse_questions_missing():
    obj = {
        "id": "test",
        "title": "Test Interview",
        "questions": [Path("tests/test_data/questions.yml")],
        "steps": [{"ask": "test_not_found"}],
    }

    with pytest.raises(BaseValidationError):
        converter.structure(obj, Interview)
