import json
import os
import sys
import threading
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import server  # noqa: E402


class Running:
    """Туршилтын серверийг түр порт дээр асаана."""

    def __enter__(self):
        self.srv = server.make_server("127.0.0.1", 0, quiet=True)
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.t.start()
        return self

    def __exit__(self, *exc):
        self.srv.shutdown()
        self.srv.server_close()

    def call(self, path, body=None, method=None, raw=None):
        data = raw if raw is not None else (
            json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(
            self.base + path, data=data,
            method=method or ("POST" if data is not None else "GET"),
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, r.headers, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers, e.read()

    def json(self, path, body=None, **kw):
        code, _, raw = self.call(path, body, **kw)
        return code, json.loads(raw.decode("utf-8"))


def test_initial_state_is_book_example():
    with Running() as s:
        code, st = s.json("/api/state")
        assert code == 200
        assert st["available"] == [3, 3, 2] and st["safe"] is True
        assert st["need"][1] == [1, 2, 2]


def test_book_sequence_over_http():
    with Running() as s:
        code, r = s.json("/api/request", {"process": 1, "request": [1, 0, 2]})
        assert code == 200 and r["request_result"]["status"] == "granted"
        assert r["state"]["available"] == [2, 3, 0]
        code, r = s.json("/api/request", {"process": 4, "request": [3, 3, 0]})
        assert r["request_result"]["status"] == "wait"
        code, r = s.json("/api/request", {"process": 0, "request": [0, 2, 0]})
        assert r["request_result"]["status"] == "unsafe"
        assert r["state"]["available"] == [2, 3, 0]          # rollback
        # төлөв серверт хадгалагдсан
        assert s.json("/api/state")[1]["available"] == [2, 3, 0]


def test_request_errors_are_http_200_with_error_status():
    with Running() as s:
        for body in [{"process": 1, "request": [2, 0, 0]},     # > Need
                     {"process": 1, "request": [-1, 0, 2]},
                     {"process": 9, "request": [0, 0, 0]},
                     {"process": 1, "request": [1, 0]},
                     {"process": 1, "request": ["a", 0, 0]},
                     {"process": "x", "request": [0, 0, 0]}]:
            code, r = s.json("/api/request", body)
            assert code == 200, body
            assert r["request_result"]["status"] == "error", body
            assert r["request_result"]["message"]
        assert s.json("/api/state")[1]["available"] == [3, 3, 2]


def test_release_and_reset():
    with Running() as s:
        s.json("/api/request", {"process": 1, "request": [1, 0, 2]})
        code, r = s.json("/api/release", {"process": 1, "release": [1, 0, 2]})
        assert r["request_result"]["status"] == "released"
        assert r["state"]["available"] == [3, 3, 2]
        code, r = s.json("/api/release", {"process": 1, "release": [9, 0, 0]})
        assert r["request_result"]["status"] == "error"
        s.json("/api/request", {"process": 1, "request": [1, 0, 2]})
        code, r = s.json("/api/reset", {})
        assert r["request_result"]["status"] == "reset"
        assert r["state"]["available"] == [3, 3, 2]


def test_load_custom_data_and_reset_returns_to_it():
    with Running() as s:
        body = {"available": [2], "max": [[3], [3]], "allocation": [[1], [1]]}
        code, r = s.json("/api/load", body)
        assert code == 200 and r["state"]["n"] == 2 and r["state"]["m"] == 1
        assert r["state"]["safe"] is True
        s.json("/api/request", {"process": 0, "request": [1]})
        _, r = s.json("/api/reset", {})
        assert r["state"]["available"] == [2]                 # шинэ ачаалсан төлөв


def test_load_without_allocation_defaults_to_zero():
    with Running() as s:
        code, r = s.json("/api/load", {"available": [4, 2], "max": [[2, 1]]})
        assert code == 200 and r["state"]["allocation"] == [[0, 0]]


def test_load_invalid_data_is_400_and_state_unchanged():
    with Running() as s:
        bad = [
            {"available": [-1, 0, 0], "max": [[1, 1, 1]]},
            {"available": [1, 1], "max": [[1, 1, 1]]},
            {"available": [1, 1, 1], "max": [[1, 1, 1]],
             "allocation": [[2, 0, 0]]},
            {"available": ["a", 1, 1], "max": [[1, 1, 1]]},
            {"available": [1, 1, 1]},
            {"max": [[1, 1, 1]]},
            [1, 2, 3],
            {"available": [], "max": []},
        ]
        for body in bad:
            code, r = s.json("/api/load", body)
            assert code == 400 and r["error"], body
        assert s.json("/api/state")[1]["available"] == [3, 3, 2]


def test_malformed_json_and_missing_fields():
    with Running() as s:
        code, _, raw = s.call("/api/request", raw=b"{not json")
        assert code == 400
        code, r = s.json("/api/request", {"process": 1})
        assert code == 400 and "request" in r["error"]
        code, r = s.json("/api/release", {"release": [0, 0, 0]})
        assert code == 400


def test_example_reloads_book():
    with Running() as s:
        s.json("/api/load", {"available": [1], "max": [[1]]})
        code, r = s.json("/api/example", {})
        assert r["request_result"]["status"] == "loaded"
        assert r["state"]["n"] == 5 and r["state"]["available"] == [3, 3, 2]


def test_state_json_contract():
    with Running() as s:
        st = s.json("/api/state")[1]
        assert set(st) >= {"n", "m", "available", "max", "allocation", "need",
                           "safe", "sequence", "steps"}


def test_static_files_served():
    with Running() as s:
        code, h, body = s.call("/")
        assert code == 200 and "text/html" in h["Content-Type"]
        assert "Banker" in body.decode("utf-8")
        code, h, _ = s.call("/graph.js")
        assert code == 200 and "javascript" in h["Content-Type"]


def test_no_path_traversal_and_unknown_paths():
    with Running() as s:
        for p in ["/../core.py", "/%2e%2e/core.py", "/..%2fcore.py",
                  "/nope.html", "/index.html/../../core.py", "/api/nope"]:
            code, _, _ = s.call(p)
            assert code == 404, p
        code, _, _ = s.call("/api/nope", {})
        assert code == 404


def test_unicode_error_messages_roundtrip():
    with Running() as s:
        _, r = s.json("/api/request", {"process": 1, "request": [2, 0, 0]})
        assert "Need" in r["request_result"]["message"]
        assert "хэтэрсэн" in r["request_result"]["message"]
