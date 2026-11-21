import json
from pathlib import Path

from src.server import App


SCENARIOS = Path(__file__).resolve().parents[1] / "src/ui/scenarios.json"


def load_scenario(name):
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    app = App()
    app.load(scenarios[name])
    return app


def test_unsafe_scenario_becomes_safe_after_release():
    app = load_scenario("unsafe")
    before = app.state()
    assert (before["n"], before["m"]) == (3, 2)
    assert before["safe"] is False

    result = app.release({"process": 0, "release": [2, 1]})
    assert result["request_result"]["status"] == "released"
    after = result["state"]
    assert after["available"] == [3, 2]
    assert after["safe"] is True
    assert after["sequence"] == ["P1", "P0", "P2"]


def test_big_scenario_starts_safe():
    app = load_scenario("big")
    state = app.state()
    assert (state["n"], state["m"]) == (10, 5)
    assert state["safe"] is True
    assert set(state["sequence"]) == {f"P{i}" for i in range(10)}
