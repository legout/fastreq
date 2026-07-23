from typing import Any

import pytest

from fastreq.backends.base import Backend, NormalizedResponse, RequestConfig


class TestRequestConfig:
    def test_request_config_defaults(self) -> None:
        config = RequestConfig(url="https://example.com")
        assert config.url == "https://example.com"
        assert config.method == "GET"
        assert config.params is None
        assert config.data is None
        assert config.json is None
        assert config.headers is None
        assert config.cookies is None
        assert config.timeout is None
        assert config.proxy is None
        assert config.http2 is True
        assert config.stream is False

    def test_request_config_with_all_fields(self) -> None:
        config = RequestConfig(
            url="https://example.com",
            method="POST",
            params={"key": "value"},
            data={"body": "data"},
            json={"json": "data"},
            headers={"Content-Type": "application/json"},
            cookies={"session": "abc123"},
            timeout=30.0,
            proxy="http://proxy:8080",
            http2=False,
            stream=True,
        )
        assert config.method == "POST"
        assert config.params == {"key": "value"}
        assert config.data == {"body": "data"}
        assert config.json == {"json": "data"}
        assert config.headers == {"Content-Type": "application/json"}
        assert config.cookies == {"session": "abc123"}
        assert config.timeout == 30.0
        assert config.proxy == "http://proxy:8080"
        assert config.http2 is False
        assert config.stream is True


class TestNormalizedResponse:
    def test_normalized_response_creation(self) -> None:
        response = NormalizedResponse(
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=b'{"key": "value"}',
            text='{"key": "value"}',
            json_data={"key": "value"},
            url="https://example.com",
        )
        assert response.status_code == 200
        assert response.url == "https://example.com"
        assert response.json_data == {"key": "value"}

    def test_normalized_response_auto_json_parsing(self) -> None:
        response = NormalizedResponse(
            status_code=200,
            headers={},
            content=b'{"test": 123}',
            text='{"test": 123}',
            json_data=None,
            url="https://example.com",
            is_json=True,
        )
        assert response.json_data == {"test": 123}

    def test_normalized_response_from_backend_json(self) -> None:
        response = NormalizedResponse.from_backend(
            status_code=200,
            headers={"Content-Type": "application/json"},
            content=b'{"key": "value"}',
            url="https://example.com",
            is_json=True,
        )
        assert response.status_code == 200
        assert response.headers == {"content-type": "application/json"}
        assert response.content == b'{"key": "value"}'
        assert response.text == '{"key": "value"}'
        assert response.json_data == {"key": "value"}
        assert response.url == "https://example.com"
        assert response.is_json is True

    def test_normalized_response_from_backend_text(self) -> None:
        response = NormalizedResponse.from_backend(
            status_code=404,
            headers={"Content-Type": "text/plain"},
            content=b"Not Found",
            url="https://example.com/notfound",
            is_json=False,
        )
        assert response.status_code == 404
        assert response.text == "Not Found"
        assert response.json_data is None
        assert response.is_json is False

    def test_normalized_response_from_backend_invalid_utf8(self) -> None:
        response = NormalizedResponse.from_backend(
            status_code=200,
            headers={},
            content=b"\xff\xfe\x00\x01",
            url="https://example.com",
            is_json=False,
        )
        assert response.text == "\ufffd\ufffd\x00\x01"


class TestBackendAbstractClass:
    def test_backend_is_abstract(self) -> None:
        with pytest.raises(TypeError):
            Backend()

    def test_backend_subclass_must_implement_abstract_methods(self) -> None:
        class IncompleteBackend(Backend):
            pass

        with pytest.raises(TypeError):
            IncompleteBackend()

    def test_backend_subclass_with_all_methods(self) -> None:
        class TestBackend(Backend):
            @property
            def name(self) -> str:
                return "test"

            async def request(self, config: RequestConfig) -> NormalizedResponse:
                return NormalizedResponse.from_backend(
                    status_code=200,
                    headers={},
                    content=b"",
                    url=config.url,
                    is_json=False,
                )

            async def close(self) -> None:
                pass

            async def __aenter__(self) -> "TestBackend":
                return self

            async def __aexit__(self, *args: Any) -> None:
                pass

            def supports_http2(self) -> bool:
                return True

        backend = TestBackend()
        assert backend.name == "test"
        assert backend.supports_http2() is True
