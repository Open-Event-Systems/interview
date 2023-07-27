# flake8: noqa
import pytest

try:
    import blacksheep
except ImportError:
    pytest.skip(
        "Install the `server` extra to run these tests", allow_module_level=True
    )
