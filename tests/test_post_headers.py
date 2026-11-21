from email.message import Message
from unittest.mock import Mock

import pytest

from src.server import Handler


@pytest.mark.parametrize("content_type, origin, expected_code", [
    ("text/plain", None, 415),
    ("application/json", "http://other.example", 403),
])
def test_invalid_headers_stop_post_before_state_change(
    content_type, origin, expected_code
):
    handler = Mock()
    handler.path = "/api/mode"
    handler.headers = Message()
    handler.headers["Host"] = "127.0.0.1:5000"
    handler.headers["Content-Type"] = content_type
    if origin is not None:
        handler.headers["Origin"] = origin

    Handler.do_POST(handler)

    handler._json.assert_called_once()
    assert handler._json.call_args.args[0] == expected_code
    handler._read_json.assert_not_called()
    handler.server.app.mode.assert_not_called()
