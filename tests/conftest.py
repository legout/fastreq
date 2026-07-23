"""Hermetic test server for integration tests.

Provides a local aiohttp-free HTTP server using asyncio directly,
supporting JSON responses, chunked streaming, cookies, redirects,
custom status codes, and Retry-After headers.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import Callable


class MockResponse:
    """Configuration for a mock HTTP response."""

    def __init__(
        self,
        status: int = 200,
        body: bytes = b"",
        headers: dict[str, str] | None = None,
        chunks: list[bytes] | None = None,
        delay: float = 0.0,
    ) -> None:
        self.status = status
        self.body = body
        self.headers = headers or {}
        self.chunks = chunks
        self.delay = delay


class LocalTestServer:
    """A minimal asyncio HTTP server for hermetic testing.

    Supports configurable routes that return MockResponse objects.
    """

    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], MockResponse | Callable[..., MockResponse]] = {}
        self._server: asyncio.base_events.Server | None = None
        self._host = "127.0.0.1"
        self.port: int = 0
        self.requests_received: list[dict[str, object]] = []

    def add_route(
        self,
        method: str,
        path: str,
        response: MockResponse | Callable[..., MockResponse],
    ) -> None:
        self.routes[(method.upper(), path)] = response

    @property
    def base_url(self) -> str:
        return f"http://{self._host}:{self.port}"

    def url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_connection,
            host=self._host,
            port=0,
        )
        sock = self._server.sockets[0]
        self.port = sock.getsockname()[1]

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def __aenter__(self) -> LocalTestServer:
        await self.start()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.stop()

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            await self._handle_request(reader, writer)
        except Exception:
            pass
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

    async def _handle_request(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        # Read request line
        request_line = await reader.readline()
        if not request_line:
            return

        parts = request_line.decode().strip().split()
        if len(parts) < 3:
            return

        method, path_with_query, _ = parts

        # Separate path from query string
        path = path_with_query.split("?")[0]

        # Read headers
        headers: dict[str, str] = {}
        while True:
            line = await reader.readline()
            if line in (b"\r\n", b"\n", b""):
                break
            key, _, value = line.decode().partition(":")
            headers[key.strip().lower()] = value.strip()

        # Read body if present
        body = b""
        content_length = headers.get("content-length")
        if content_length:
            body = await reader.readexactly(int(content_length))

        # Record request
        self.requests_received.append(
            {
                "method": method,
                "path": path,
                "headers": headers,
                "body": body,
            }
        )

        # Find matching route
        route_key = (method.upper(), path)
        response = self.routes.get(route_key)
        if response is None:
            # Try GET fallback for any method
            response = self.routes.get(("GET", path), MockResponse(status=404, body=b"Not Found"))

        if callable(response):
            response = response()

        if response.delay > 0:
            await asyncio.sleep(response.delay)

        # Build response
        resp_headers: dict[str, str] = {
            "Server": "fastreq-test-server",
            **response.headers,
        }

        body_data = response.body
        if response.chunks is not None:
            # Use chunked transfer encoding
            chunk_lines = []
            for chunk in response.chunks:
                chunk_lines.append(f"{len(chunk):x}\r\n".encode())
                chunk_lines.append(chunk)
                chunk_lines.append(b"\r\n")
            chunk_lines.append(b"0\r\n\r\n")
            body_data = b"".join(chunk_lines)
            resp_headers["Transfer-Encoding"] = "chunked"
        else:
            resp_headers["Content-Length"] = str(len(body_data))

        # Build response bytes
        status_line = f"HTTP/1.1 {response.status} {self._status_text(response.status)}\r\n"
        header_lines = "".join(f"{k}: {v}\r\n" for k, v in resp_headers.items())
        response_bytes = (status_line + header_lines + "\r\n").encode() + body_data

        writer.write(response_bytes)
        await writer.drain()

    @staticmethod
    def _status_text(status: int) -> str:
        texts = {
            200: "OK",
            201: "Created",
            301: "Moved Permanently",
            302: "Found",
            400: "Bad Request",
            404: "Not Found",
            429: "Too Many Requests",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
        }
        return texts.get(status, "Unknown")


def json_body(data: object) -> bytes:
    """Create a JSON body with proper content-type."""
    return json.dumps(data).encode()


def json_response(
    data: object,
    status: int = 200,
    extra_headers: dict[str, str] | None = None,
) -> MockResponse:
    """Create a JSON MockResponse."""
    headers = {"Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    return MockResponse(
        status=status,
        body=json_body(data),
        headers=headers,
    )


def text_response(
    text: str,
    status: int = 200,
    extra_headers: dict[str, str] | None = None,
) -> MockResponse:
    """Create a text MockResponse."""
    headers = {"Content-Type": "text/plain"}
    if extra_headers:
        headers.update(extra_headers)
    return MockResponse(
        status=status,
        body=text.encode(),
        headers=headers,
    )


def chunked_response(
    chunks: list[bytes],
    status: int = 200,
    extra_headers: dict[str, str] | None = None,
) -> MockResponse:
    """Create a chunked MockResponse."""
    headers = {"Content-Type": "application/octet-stream"}
    if extra_headers:
        headers.update(extra_headers)
    return MockResponse(
        status=status,
        chunks=chunks,
        headers=headers,
    )
