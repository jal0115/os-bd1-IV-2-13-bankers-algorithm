"""Banker's Algorithm web server (зөвхөн Python стандарт сан, dependency-гүй).

Ажиллуулах:   python src/server.py [--port 5000]
Дараа нь хөтөчөөр http://127.0.0.1:5000 нээнэ.

API (JSON). Бүх хариу UTF-8.
  GET  /api/state      -> төлөв (core.to_json())
  POST /api/load       -> {available, max, allocation?} шинэ төлөв ачаална
  POST /api/request    -> {process, request}
  POST /api/release    -> {process, release}
  POST /api/reset      -> анх ачаалсан төлөвт буцаана
  POST /api/example    -> номын 8.6.3 жишээг ачаална
  POST /api/mode       -> {enforce: true|false} Banker's Algorithm-ийн safety шалгалтыг асаах/унтраах

request/release/reset/example -> 200 {"request_result": {status, message}, "state": {...}}
(wait/unsafe/error статус ч HTTP 200; зөвхөн хэрэглэгчийн оролтын формат буруу
эсвэл /api/load-ын өгөгдөл буруу бол 400 {"error": "..."}).

Нэг хэрэглэгчийн сервер: төлөв санах ойд нэг л хадгалагдана.
"""
import argparse
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import Banker, BankerError  # noqa: E402

UI_DIR = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui"))
MAX_BODY = 1_000_000

EXAMPLE = {
    "available": [3, 3, 2],
    "max": [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]],
    "allocation": [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
}

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".json": "application/json; charset=utf-8",
}


def _example_banker():
    return Banker(EXAMPLE["available"], EXAMPLE["max"], EXAMPLE["allocation"])


class BadRequest(Exception):
    pass


class App:
    """Серверийн төлөв ба үйлдлүүд (HTTP-ээс салгасан, тестлэхэд хялбар)."""

    def __init__(self):
        self.lock = threading.Lock()
        self.banker = _example_banker()
        self.enforce = True

    def state(self):
        d = self.banker.to_json()
        d["enforce"] = self.enforce
        return d

    def _wrap(self, status, message):
        return {"request_result": {"status": status, "message": message},
                "state": self.state()}

    def load(self, data):
        if not isinstance(data, dict):
            raise BadRequest("JSON объект байх ёстой")
        for key in ("available", "max"):
            if key not in data:
                raise BadRequest(f"'{key}' талбар дутуу байна")
        try:
            self.banker = Banker(data["available"], data["max"],
                                 data.get("allocation"))
        except BankerError as e:
            raise BadRequest(str(e))
        self.banker.enforce = self.enforce
        return {"state": self.state()}

    def example(self):
        self.banker = _example_banker()
        self.banker.enforce = self.enforce
        return self._wrap("loaded", "Номын 8.6.3 жишээг ачааллаа")

    def reset(self):
        self.banker.reset()
        return self._wrap("reset", "Анх ачаалсан төлөвт буцлаа")

    def mode(self, data):
        if not isinstance(data, dict) or not isinstance(data.get("enforce"), bool):
            raise BadRequest("'enforce' талбар (true/false) хэрэгтэй")
        self.enforce = data["enforce"]
        self.banker.enforce = self.enforce
        msg = ("Banker's Algorithm идэвхтэй: аюултай хүсэлтийг татгалзана" if self.enforce
               else "Banker's Algorithm унтраалттай: аюултай хүсэлт ч олгогдоно (deadlock-ийн эрсдэл)")
        return self._wrap("mode", msg)

    def request(self, data):
        if not isinstance(data, dict) or "process" not in data or "request" not in data:
            raise BadRequest("'process' ба 'request' талбар хэрэгтэй")
        return self._wrap(*self.banker.request(data["process"], data["request"]))

    def release(self, data):
        if not isinstance(data, dict) or "process" not in data or "release" not in data:
            raise BadRequest("'process' ба 'release' талбар хэрэгтэй")
        return self._wrap(*self.banker.release(data["process"], data["release"]))


class Handler(BaseHTTPRequestHandler):
    server_version = "BankerServer/1.0"

    def log_message(self, fmt, *args):
        if not getattr(self.server, "quiet", False):
            super().log_message(fmt, *args)

    # ---- туслах ----
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise BadRequest("Content-Length буруу")
        if length > MAX_BODY:
            raise BadRequest("Хүсэлт хэт том байна")
        raw = self.rfile.read(length) if length else b""
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise BadRequest("JSON задлагдсангүй")

    # ---- GET ----
    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        app = self.server.app
        if path == "/api/state":
            with app.lock:
                return self._json(200, app.state())
        if path.startswith("/api/"):
            return self._json(404, {"error": "Ийм API байхгүй"})
        self._static(path)

    def _static(self, path):
        rel = "index.html" if path in ("", "/") else path.lstrip("/")
        full = os.path.realpath(os.path.join(UI_DIR, rel))
        inside = full == UI_DIR or full.startswith(UI_DIR + os.sep)
        ctype = CONTENT_TYPES.get(os.path.splitext(full)[1].lower())
        if not inside or not os.path.isfile(full) or ctype is None:
            return self._send(404, "Олдсонгүй".encode("utf-8"),
                              "text/plain; charset=utf-8")
        with open(full, "rb") as f:
            self._send(200, f.read(), ctype)

    # ---- POST ----
    def do_POST(self):
        path = unquote(urlsplit(self.path).path)
        app = self.server.app
        routes = {
            "/api/load": app.load,
            "/api/request": app.request,
            "/api/release": app.release,
            "/api/reset": lambda _data: app.reset(),
            "/api/example": lambda _data: app.example(),
            "/api/mode": app.mode,
        }
        fn = routes.get(path)
        if fn is None:
            return self._json(404, {"error": "Ийм API байхгүй"})
        try:
            data = self._read_json()
            with app.lock:
                result = fn(data)
        except BadRequest as e:
            return self._json(400, {"error": str(e)})
        self._json(200, result)


def make_server(host="127.0.0.1", port=5000, quiet=False):
    server = ThreadingHTTPServer((host, port), Handler)
    server.app = App()
    server.quiet = quiet
    return server


def main(argv=None):
    p = argparse.ArgumentParser(description="Banker's Algorithm web UI")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--host", default="127.0.0.1")
    args = p.parse_args(argv)
    try:
        server = make_server(args.host, args.port)
    except OSError as e:
        print(f"алдаа: {args.host}:{args.port} дээр сервер ассангүй "
              f"({e.strerror}). Өөр порт сонгоно уу: --port 5001")
        return 2
    print(f"Banker's Algorithm UI: http://{args.host}:{args.port}  (зогсоох: Ctrl+C)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nЗогслоо")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
