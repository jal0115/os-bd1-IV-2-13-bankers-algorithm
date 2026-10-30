import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from core import Banker, ERROR, GRANTED, UNSAFE, WAIT  # noqa: E402
from server import App, BadRequest, EXAMPLE  # noqa: E402


def _book():
    return Banker(EXAMPLE["available"], EXAMPLE["max"], EXAMPLE["allocation"])


def test_banker_on_denies_unsafe_request():
    b = _book()
    assert b.request(1, [1, 0, 2])[0] == GRANTED
    assert b.request(0, [0, 2, 0])[0] == UNSAFE


def test_banker_off_grants_unsafe_request():
    b = _book()
    b.enforce = False
    assert b.request(1, [1, 0, 2])[0] == GRANTED
    assert b.request(0, [0, 2, 0])[0] == GRANTED
    assert b.is_safe()[0] is False


def test_banker_off_still_checks_need_and_available():
    b = _book()
    b.enforce = False
    assert b.request(0, [8, 0, 0])[0] == ERROR
    assert b.request(0, [4, 0, 0])[0] == WAIT


def test_mode_endpoint_persists_across_load_and_example():
    app = App()
    assert app.state()["enforce"] is True
    assert app.mode({"enforce": False})["state"]["enforce"] is False
    app.example()
    assert app.state()["enforce"] is False
    app.load({"available": [1], "max": [[1]]})
    assert app.banker.enforce is False and app.state()["enforce"] is False


def test_mode_rejects_non_bool():
    app = App()
    with pytest.raises(BadRequest):
        app.mode({"enforce": "yes"})
    with pytest.raises(BadRequest):
        app.mode({})
