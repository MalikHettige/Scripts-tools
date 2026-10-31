"""A tiny local target for testing bac-hunter against: deliberately has one
IDOR (object_id_swap should catch it) and one horizontal-access bug
(session_swap should catch it), plus one correctly-protected endpoint.
Run: python3 tests/mock_server.py   (serves on 127.0.0.1:8765)
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit, parse_qs

ORDERS = {
    "1001": {"owner": "alice", "total": 42.50},
    "1002": {"owner": "bob", "total": 17.00},
}

# Separate resource with an intentionally missing ownership check, so the
# demo has one real bug for the tool to catch alongside the correctly
# protected /api/orders/ endpoint (no false positive there).
INVOICES = {
    "5001": {"owner": "alice", "amount": 980.00},
    "5002": {"owner": "bob", "amount": 120.00},
}

SESSIONS = {
    "alice-cookie": "alice",
    "bob-cookie": "bob",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # quiet

    def _user(self):
        cookie = self.headers.get("Cookie", "")
        for token, user in SESSIONS.items():
            if token in cookie:
                return user
        return None

    def _send(self, status, body: dict):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parts = urlsplit(self.path)
        user = self._user()

        if parts.path.startswith("/api/orders/"):
            order_id = parts.path.rsplit("/", 1)[-1]
            order = ORDERS.get(order_id)
            if not order:
                return self._send(404, {"error": "not found"})
            # Correctly protected: only the owner may view their own order.
            if user != order["owner"]:
                return self._send(403, {"error": "forbidden"})
            return self._send(200, {"id": order_id, **order})

        if parts.path.startswith("/api/invoices/"):
            inv_id = parts.path.rsplit("/", 1)[-1]
            inv = INVOICES.get(inv_id)
            if not inv:
                return self._send(404, {"error": "not found"})
            # BUG (intentional, for the demo): no ownership check at all -
            # object_id_swap should catch bob reading alice's invoice 5001,
            # and session_swap should catch any session reaching either.
            if not user:
                return self._send(401, {"error": "unauthenticated"})
            return self._send(200, {"id": inv_id, **inv})

        if parts.path == "/api/profile":
            # BUG (intentional): /api/profile?user_id=bob works for anyone,
            # regardless of whose cookie is sent - session_swap should catch
            # this as "mutated session got 200 where it should've been denied"
            # IF we also vary user_id; here we demo the simpler case: no
            # auth check on a privileged admin endpoint at all.
            if not user:
                return self._send(401, {"error": "unauthenticated"})
            return self._send(200, {"user": user, "email": f"{user}@example.com"})

        if parts.path == "/api/admin/stats":
            # Correctly protected: only alice (treated as admin here) may pass.
            if user != "alice":
                return self._send(403, {"error": "forbidden"})
            return self._send(200, {"total_users": 2})

        return self._send(404, {"error": "no route"})


if __name__ == "__main__":
    srv = HTTPServer(("127.0.0.1", 8765), Handler)
    print("mock target listening on http://127.0.0.1:8765")
    srv.serve_forever()
