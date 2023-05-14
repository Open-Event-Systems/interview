"""Templating module."""
from __future__ import annotations

from oes.interview.parsing.undefined import Environment, Undefined

default_jinja2_env = Environment(undefined=Undefined)
"""The default Jinja2 environment."""
