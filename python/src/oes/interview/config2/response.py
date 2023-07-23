"""Response validation and parsing."""
import itertools
import re
from collections.abc import Callable, Iterable, Mapping
from typing import Optional, Type, TypeVar

from attrs import AttrsInstance, asdict, make_class
from cattrs import Converter
from oes.interview.config2.locator import Locator
from oes.interview.config2.types import Parseable, ResponseParser, UserResponse

AttrsT = TypeVar("AttrsT", bound=AttrsInstance)


def create_response_parser(
    name: str,
    fields: Iterable[Parseable],
    converter: Converter,
) -> ResponseParser:
    """Create a callable to parse user responses.

    Args:
        name: A class name.
        fields: The input fields.
        converter: The :class:`Converter` to use to parse values.

    Returns:
        The :class:`ResponseParser`.
    """

    name_factory = _make_field_name_factory()

    by_name: dict[str, Parseable] = {name_factory(f): f for f in fields}

    name_to_loc: dict[str, Optional[Locator]] = {n: f.set for n, f in by_name.items()}

    attrs_cls = _create_attrs_class(_make_class_name(name), by_name)

    def parser(response: UserResponse) -> Mapping[Locator, object]:
        parsed_obj = _parse_response(response, attrs_cls, converter)
        by_loc = _map_response_values_to_locations(parsed_obj, name_to_loc)
        return by_loc

    return parser


def _make_class_name(name: str) -> str:
    subbed = re.sub(r"[^a-z0-9]+", "", name, flags=re.I)
    parts = re.split(r"[\s_-]+", subbed)
    cap_parts = (p.capitalize() for p in parts)
    return "_" + "".join(cap_parts)


def _make_field_name_factory() -> Callable[[Parseable], str]:
    """Get a callable that generates names for fields."""
    counter = itertools.count()

    def field_name_factory(field: Parseable) -> str:
        i = next(counter)
        return f"field_{i}"

    return field_name_factory


def _parse_response(
    response: UserResponse, cls: Type[AttrsT], converter: Converter
) -> AttrsT:
    """Parse a user response.

    Raises:
        ClassValidationError: If the response are invalid.
    """
    return converter.structure(response, cls)


def _map_response_values_to_locations(
    response_obj: AttrsInstance,
    locations: Mapping[str, Optional[Locator]],
) -> Mapping[Locator, object]:
    """Map the attributes of a parsed user response to variable locations."""
    as_dict = asdict(response_obj)
    mapped = {}

    for key, value in as_dict.items():
        loc = locations.get(key)
        if loc is not None:
            mapped[loc] = value

    return mapped


def _create_attrs_class(
    name: str,
    fields: Mapping[str, Parseable],
) -> Type[AttrsInstance]:
    """Create a class that :mod:`attrs` can use to parse responses."""
    cls = make_class(
        name,
        {nm: f.field_info for nm, f in fields.items()},
        frozen=True,
        slots=True,
    )
    return cls
