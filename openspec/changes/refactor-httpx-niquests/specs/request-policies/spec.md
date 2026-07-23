## ADDED Requirements

### Requirement: Explicit proxy pools
The system SHALL rotate only proxies explicitly supplied by the caller, environment, or an explicit Webshare import. It SHALL not discover or fetch free proxies.

#### Scenario: Cooldown after a transport failure
- **GIVEN** a proxy pool containing two proxies
- **WHEN** a request through one proxy fails with a retryable transport error
- **THEN** that proxy SHALL enter cooldown and the next eligible attempt SHALL use another available proxy.

#### Scenario: No free proxy configuration
- **WHEN** a caller supplies a removed free-proxy option
- **THEN** configuration SHALL fail with a migration-oriented error.

### Requirement: Unified admission control
The system SHALL use one concurrency gate and one token bucket per client.

#### Scenario: Rate token before concurrency slot
- **WHEN** requests are paced by a rate limit and a concurrency limit
- **THEN** a waiting request SHALL acquire a rate token before occupying a concurrency slot.

### Requirement: Safe retries
The system SHALL retry only configured transient transport failures and retryable statuses 429, 500, 502, 503, and 504.

#### Scenario: Retry-After
- **WHEN** a retryable response provides a valid `Retry-After` value
- **THEN** the next attempt SHALL wait at least that duration.

#### Scenario: Configuration error
- **WHEN** request configuration is invalid
- **THEN** the client SHALL raise immediately without retrying.
