import pytest
from oes.interview.config2.locator import (
    Access,
    InvalidLocatorError,
    Literal,
    Variable,
    literal,
    parse_locator,
    variable,
)
from pyparsing import ParseException


@pytest.mark.parametrize(
    "token, val, expected",
    (
        (literal, "0", Literal(0)),
        (literal, "1230", Literal(1230)),
        (literal, '""', Literal("")),
        (literal, '"test \\"string\\""', Literal('test "string"')),
        (variable, "test", Variable("test")),
        (variable, "test_var", Variable("test_var")),
        (variable, "test_var_", Variable("test_var_")),
    ),
)
def test_parse_tokens(token, val, expected):
    result = token.parse_string(val, parse_all=True)
    assert list(result) == [expected]


@pytest.mark.parametrize(
    "token, val",
    (
        (literal, "0123"),
        (literal, ""),
        (literal, '"test'),
        (literal, 'test"'),
        (literal, "''"),
        (variable, "_invalid"),
        (variable, "invalid-var"),
        (variable, "-invalid-var"),
        (variable, "invalid-var-"),
    ),
)
def test_parse_tokens_error(token, val):
    with pytest.raises(ParseException):
        token.parse_string(val, parse_all=True)


@pytest.mark.parametrize(
    "val, expected",
    (
        ("var", Variable("var")),
        ("a.b", Access(Variable("a"), Literal("b"))),
        ('a["b"]', Access(Variable("a"), Literal("b"))),
        ("a[0]", Access(Variable("a"), Literal(0))),
        ("a[123]", Access(Variable("a"), Literal(123))),
        ("a[b]", Access(Variable("a"), Variable("b"))),
        ('a[b]["c"]', Access(Access(Variable("a"), Variable("b")), Literal("c"))),
        ("a[b].c", Access(Access(Variable("a"), Variable("b")), Literal("c"))),
        ("a[b[c]]", Access(Variable("a"), Access(Variable("b"), Variable("c")))),
        ("a[ 0 ].b", Access(Access(Variable("a"), Literal(0)), Literal("b"))),
    ),
)
def test_parse_locator(val, expected):
    result = parse_locator(val)
    assert result == expected


@pytest.mark.parametrize(
    "val",
    (
        "bad var",
        "-bad-var",
        "bad-var-",
        "0",
        "123",
        "a.[b]",
        "a[b c]",
        "a[b.]",
    ),
)
def test_parse_locator_error(val):
    with pytest.raises(InvalidLocatorError):
        parse_locator(val)


@pytest.mark.parametrize(
    "val, expected",
    (
        ("f", True),
        ("a.b", [0, 1]),
        ('a["c"]', 2),
        ("d[a.b[0]].e", "c"),
        ("d[a.b[1]].e", "b"),
        ('a[d[1]["e"]][1]', 1),
    ),
)
def test_evaluate_locator(val, expected):
    doc = {
        "a": {"b": [0, 1], "c": 2},
        "d": [{"e": "c"}, {"e": "b"}],
        "f": True,
    }
    res = parse_locator(val)
    assert res.evaluate(doc) == expected


def test_set_locator():
    doc = {
        "a": {"b": [0, 1], "c": 2},
        "d": [{"e": "c"}, {"e": "b"}],
        "f": True,
    }

    loc = parse_locator('a[d[a.b[0]]["e"]]')
    loc.set(doc, "test")
    assert doc["a"]["c"] == "test"
