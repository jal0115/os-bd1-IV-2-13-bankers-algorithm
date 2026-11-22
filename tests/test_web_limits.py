import pytest

from src.server import App, BadRequest


def table(processes, resources):
    return {
        "available": [1] * resources,
        "max": [[1] * resources for _ in range(processes)],
    }


def test_accepts_maximum_table_size():
    state = App().load(table(20, 8))["state"]
    assert (state["n"], state["m"]) == (20, 8)


@pytest.mark.parametrize("processes, resources, message", [
    (21, 8, "20 процесс"),
    (20, 9, "8 нөөц"),
])
def test_rejects_oversized_table_without_changing_state(processes, resources, message):
    app = App()
    before = app.state()

    with pytest.raises(BadRequest, match=message):
        app.load(table(processes, resources))

    assert app.state() == before
