import pytest
from attrs import define, field
from oes.interview_old.parsing.types import validate_identifier


@define
class Example:
    id: str = field(validator=[validate_identifier])


@pytest.mark.parametrize(
    "value",
    [
        "_id",
        "0id",
        "id-test-",
        "id.test",
    ],
)
def test_identifier_validation(value):
    with pytest.raises(ValueError):
        Example(id=value)
