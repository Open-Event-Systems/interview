import pytest
from oes.interview_old.parsing.location import AttributeAccess, Name
from oes.interview_old.parsing.undefined import UndefinedError
from oes.template import Template


def test_undefined():
    template = Template("{{ value }}")
    with pytest.raises(UndefinedError) as e:
        template.render()

    assert e.value.location == Name("value")


def test_undefined_chained():
    template = Template("{{ value.a }}")
    with pytest.raises(UndefinedError) as e:
        template.render(value={})

    assert e.value.location == AttributeAccess(Name("value"), "a")


def test_undefined_chained_2():
    template = Template("{{ value.a.b }}")
    with pytest.raises(UndefinedError) as e:
        template.render(value={})

    assert e.value.location == AttributeAccess(Name("value"), "a")
