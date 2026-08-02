# fastreq Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.2.0] - 2026-08-01

### Added

- Optional progress reporting for batch operations via the new
  `progress-rich` (`rich`) and `progress-tqdm` (`tqdm`) extras. Both are
  opt-in (`pip install fastreq[progress-rich]`), keeping the core
  dependency surface unchanged.

### Fixed

- `version-bump.yml` workflow now correctly detects version changes by
  comparing against `HEAD~1` instead of `origin/main` (the previous logic
  always saw the new version on `origin/main` after the push completed,
  silently skipping tag creation and blocking PyPI releases).

## [3.1.1] - 2026-07-25

### Fixed

- `fastreq.__version__` now matches the package version (was stale at 3.0.0).

## [3.1.0] - 2026-07-25

### Added

- New optional `curl_cffi` backend (`pip install fastreq[curl]`) with browser
  TLS/JA3 impersonation via the `impersonate` parameter (explicit target like
  `"chrome131"`, `"random"`, or `None`). Defeats bot detection that blocks
  plain HTTP clients.
- `impersonate` parameter on `FastRequests`, `fastreq()`, and
  `fastreq_async()`; `FASTREQ_IMPERSONATE` environment variable.
- User-agent rotation is disabled automatically when `impersonate` is set
  (curl_cffi supplies the browser-matching User-Agent).
- curl_cffi included in the shared hermetic transport contract tests.

## [2.0.1] - 2025-01-02

### Added

- Initial changelog structure
- Automated CI/CD workflows for testing, versioning, and publishing
