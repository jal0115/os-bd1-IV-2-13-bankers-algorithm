
from pathlib import Path

from src.cli import build_banker, execute


ROOT = Path(__file__).resolve().parent.parent
MAX = ROOT / "examples" / "book_max.txt"
ALLOC = ROOT / "examples" / "book_allocation.txt"


def make_banker():
    banker, _ = build_banker(
        [10, 5, 7], str(MAX), str(ALLOC)
    )
    return banker


def snapshot(b):
    return (
        tuple(b.available),
        tuple(tuple(row) for row in b.allocation),
        tuple(tuple(row) for row in b.need),
    )


def test_request_exceeds_need_keeps_state():
    b = make_banker()
    before = snapshot(b)

    result = execute(b, "RQ 1 2 0 0")

    assert result.startswith("error:")
    assert snapshot(b) == before


def test_insufficient_resources_keeps_state():
    b = make_banker()
    before = snapshot(b)

    result = execute(b, "RQ 4 4 0 0")

    assert result.startswith("wait:")
    assert snapshot(b) == before


def test_invalid_process_keeps_state():
    b = make_banker()
    before = snapshot(b)

    result = execute(b, "RQ 9 0 0 1")

    assert result.startswith("error:")
    assert snapshot(b) == before


def test_invalid_release_keeps_state():
    b = make_banker()
    before = snapshot(b)

    result = execute(b, "RL 0 1 0 0")

    assert result.startswith("error:")
    assert snapshot(b) == before


def test_unsafe_request_rolls_back():
    b = make_banker()

    first = execute(b, "RQ 1 1 0 2")
    assert first.startswith("granted:")

    before = snapshot(b)
    result = execute(b, "RQ 0 0 2 0")

    assert result.startswith("unsafe:")
    assert snapshot(b) == before


def test_request_release_restores_state():
    b = make_banker()
    before = snapshot(b)

    assert execute(b, "RQ 1 1 0 2").startswith("granted:")
    assert execute(b, "RL 1 1 0 2").startswith("released:")

    assert snapshot(b) == before

def test_status_rejects_extra_arguments():
    b = make_banker()
    before = snapshot(b)

    result = execute(b, "* 1 2")

    assert result.startswith("алдаа:")
    assert snapshot(b) == before
