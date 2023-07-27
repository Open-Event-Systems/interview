import pytest
from oes.interview_old.parsing.location import (
    AttributeAccess,
    Const,
    IndexAccess,
    Location,
    Name,
    UndefinedError,
    number,
    var_location,
    var_name,
)
from pyparsing import ParseException


@pytest.mark.parametrize(
    "value, expected",
    [
        ["123", 123],
        [" 123 ", 123],
        ["0", 0],
    ],
)
def test_parse_const(value, expected):
    res = number.parse_string(value, True)
    assert list(res) == [Const(expected)]


# @pytest.mark.parametrize(
#     "value",
#     ["00"]
# )
# def test_parse_invalid_const(value):
#     with pytest.raises(ValueError):
#         number.parse_string(value, True)


@pytest.mark.parametrize(
    "value, expected",
    [
        ["abc", ["abc"]],
        ["a_b_c", ["a_b_c"]],
        ["test0", ["test0"]],
        [" abc", ["abc"]],
        ["abc ", ["abc"]],
        [" abc ", ["abc"]],
    ],
)
def test_parse_var_name(value, expected):
    res = var_name.parse_string(value, True)
    assert list(res) == expected


@pytest.mark.parametrize(
    "value",
    [
        "a bc",
        "0test",
        "test-value",
    ],
)
def test_parse_name_error(value):
    with pytest.raises(ParseException):
        var_name.parse_string(value, True)


@pytest.mark.parametrize(
    "value, expected",
    [
        ["a", Name("a")],
        ["a.b", AttributeAccess(Name("a"), "b")],
        ["a.b.c", AttributeAccess(AttributeAccess(Name("a"), "b"), "c")],
        ["a[1]", IndexAccess(Name("a"), Const(1))],
        ["a[x]", IndexAccess(Name("a"), Name("x"))],
        ["a[x[y]]", IndexAccess(Name("a"), IndexAccess(Name("x"), Name("y")))],
        ["a[x.y]", IndexAccess(Name("a"), AttributeAccess(Name("x"), "y"))],
        ["a.b[x]", IndexAccess(AttributeAccess(Name("a"), "b"), Name("x"))],
        [
            "value1.value2[value3]",
            IndexAccess(AttributeAccess(Name("value1"), "value2"), Name("value3")),
        ],
    ],
)
def test_parse_location(value, expected):
    expr = var_location.parse_string(value, True)
    assert expr[0] == expected


@pytest.mark.parametrize(
    "value",
    [
        "te st",
        "te-st",
        "_test",
        "0test",
        "0123",
    ],
)
def test_parse_location_invalid(value):
    with pytest.raises(ParseException):
        var_location.parse_string(value, True)


def test_loc_equals():
    e1 = Location.parse("a.b[c]")
    e2 = Location.parse("a . b [ c ]")
    assert e1 == e2
    assert hash(e1) == hash(e2)


def test_loc_str():
    e = Location.parse("a . b [c ]")
    assert str(e) == "a.b[c]"


@pytest.mark.parametrize(
    "expr, expected", [["a.b.c", 1], ["a.d", 2], ["e", 3], ["a.b", {"c": 1}]]
)
def test_loc_get(expr, expected):
    obj = {
        "a": {
            "b": {
                "c": 1,
            },
            "d": 2,
        },
        "e": 3,
    }
    expr_obj = Location.parse(expr)
    assert expr_obj.evaluate(**obj) == expected


@pytest.mark.parametrize(
    "expr, expected",
    [
        ["a[0]", 1],
        ["a[a[0]]", 2],
        ["a[i]", 3],
    ],
)
def test_loc_get_complex(expr, expected):
    obj = {
        "a": [1, 2, 3],
        "i": 2,
    }
    expr_obj = Location.parse(expr)
    assert expr_obj.evaluate(**obj) == expected


@pytest.mark.parametrize(
    "v, err_path",
    [
        ["c", "c"],
        ["a.a", "a.a"],
        ["a.c.d", "a.c"],
        ["a[x]", "a[2]"],
        ["a[z]", "z"],
    ],
)
def test_loc_get_undefined(v, err_path):
    obj = {
        "a": {"b": 1},
        "x": 2,
    }

    expr = Location.parse(v)
    with pytest.raises(UndefinedError) as e:
        expr.evaluate(**obj)

    assert e.value.location == Location.parse(err_path)


@pytest.mark.parametrize(
    "obj, expr, value, final",
    [
        [{}, "a", 1, {"a": 1}],
        [{"a": 1}, "a", 2, {"a": 2}],
        [{"a": {}}, "a.b", 2, {"a": {"b": 2}}],
        [{"a": {"b": 1}}, "a.c", 2, {"a": {"b": 1, "c": 2}}],
        [{"a": {"b": 1}}, "a", 2, {"a": 2}],
        [{"a": {"b": 1}}, "a", {"c": 2}, {"a": {"c": 2}}],
    ],
)
def test_loc_set(obj, expr, value, final):
    expr_obj = Location.parse(expr)
    expr_obj.set(value, obj)
    assert obj == final
