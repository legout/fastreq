## ADDED Requirements

### Requirement: Retained Transport Set
The system SHALL support exactly the `niquests` and `httpx` backends. `niquests` SHALL be the default selected by `backend="auto"`.

#### Scenario: Default backend
- **WHEN** a caller creates `FastRequests()`
- **THEN** the client SHALL select the niquests backend.

#### Scenario: Explicit HTTPX backend
- **WHEN** a caller creates `FastRequests(backend="httpx")` with the HTTPX extra installed
- **THEN** the client SHALL execute requests through HTTPX.

#### Scenario: Removed backend name
- **WHEN** a caller selects `backend="aiohttp"` or `backend="requests"`
- **THEN** construction SHALL raise `ConfigurationError` explaining the supported replacements.

### Requirement: Real streaming
The system SHALL deliver stream chunks incrementally to a supplied callback without first loading the full response body.

#### Scenario: Chunk callback
- **WHEN** a request uses `stream=True` and a `stream_callback`
- **THEN** the callback SHALL receive each chunk before the complete response has been accumulated.

### Requirement: Retained backend contract
The system SHALL provide a narrow async backend contract implemented only by retained transports.

#### Scenario: Normal request
- **WHEN** a retained backend receives a normalized request configuration
- **THEN** it SHALL return a normalized response with status, headers, URL, bytes, text, and optionally parsed JSON.

#### Scenario: Lifecycle
- **WHEN** a caller exits a FastRequests async context
- **THEN** all backend sessions and proxy-scoped clients SHALL close.
