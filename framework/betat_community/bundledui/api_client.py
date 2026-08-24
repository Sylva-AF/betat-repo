"""Internal client for calling this install's own public JSON API from the
bundled UI (COMMUNITY_FRAMEWORK.md Layer 2: "the bundled UI consumes the
public JSON API only — no internal shortcuts"). Uses Django's test Client
rather than a real socket: it drives the exact same URLconf, views,
serializers, and permission classes any external caller hits — the same
boundary, just without opening a connection back to its own process
(which risks deadlock behind a single-threaded server) or adding an HTTP
client dependency. This is not an ORM shortcut; no view using this touches
a model directly for anything the API itself could serve.

server_name matters: Client() defaults its Host header to "testserver",
which only passes ALLOWED_HOSTS validation inside pytest's test-environment
setup (which appends it there) — not in a real running server. Every
bundledui view must construct ApiClient(server_name=request.get_host())
so the internal call reuses the same host the browser's own request
already passed validation for, regardless of DEBUG/ALLOWED_HOSTS.
"""
import json

from django.test import Client


class ApiClient:
    def __init__(self, token=None, server_name=None):
        self._client = Client(**({'SERVER_NAME': server_name} if server_name else {}))
        self._token = token

    def _extra(self):
        return {'HTTP_AUTHORIZATION': f'Token {self._token}'} if self._token else {}

    def get(self, path, params=None):
        response = self._client.get(path, data=params or {}, **self._extra())
        return response.status_code, response.json()

    def post(self, path, payload):
        response = self._client.post(
            path,
            data=json.dumps(payload),
            content_type='application/json',
            **self._extra(),
        )
        return response.status_code, response.json()
