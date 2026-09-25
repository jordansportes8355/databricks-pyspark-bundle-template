"""Minimal fake Databricks REST API, enough for `databricks bundle validate`."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

CURRENT_USER = {
    "id": "123",
    "userName": "jane.doe@example.com",
    "displayName": "Jane Doe",
    "emails": [{"value": "jane.doe@example.com", "primary": True}],
    "active": True,
}


class _Handler(BaseHTTPRequestHandler):
    def _send(self, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path == "/api/2.0/preview/scim/v2/Me":
            return self._send(CURRENT_USER)
        if url.path == "/api/2.0/workspace/get-status":
            path = parse_qs(url.query).get("path", ["/"])[0]
            return self._send({"object_type": "DIRECTORY", "path": path, "object_id": 1})
        return self._send({})

    def do_POST(self) -> None:
        return self._send({})

    def log_message(self, *args) -> None:
        pass


class DatabricksApiMock:
    """Serve the fake API on a free local port in a background thread."""

    def __enter__(self) -> str:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        return f"http://127.0.0.1:{self._server.server_port}"

    def __exit__(self, *exc) -> None:
        self._server.shutdown()
