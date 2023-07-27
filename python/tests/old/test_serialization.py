from collections.abc import Sequence

import pytest
from oes.interview_old.serialization import converter


@pytest.mark.parametrize(
    "val, typ",
    [
        (None, str),
        (None, int),
        (1, str),
        ("1", int),
        (1, bool),
    ],
)
def test_structure_does_not_cast(val, typ):
    with pytest.raises(TypeError):
        converter.structure(val, typ)


@pytest.mark.parametrize(
    "val, typ, res",
    [
        (1.4, int, 1),
        (1, float, 1.0),
        (True, int, 1),
    ],
)
def test_allowed_casts(val, typ, res):
    assert converter.structure(val, typ) == res


def test_structure_immutable_sequence():
    val = [1, 2, 3]
    res = converter.structure(val, Sequence[int])
    assert res == (1, 2, 3)
