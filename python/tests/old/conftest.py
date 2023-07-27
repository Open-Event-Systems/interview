import pytest
from oes.interview_old.parsing.template import default_jinja2_env
from oes.template import set_jinja2_env


@pytest.fixture(autouse=True)
def setup_jinja2_env():
    with set_jinja2_env(default_jinja2_env):
        yield
