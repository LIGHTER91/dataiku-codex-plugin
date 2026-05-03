# ADR-003 — Managed Folders Must Be Stream-First

## Status

Accepted.

## Context

Dataiku Managed Folders may be backed by local storage, S3, HDFS, GCS, FTP or other backends.

Local filesystem paths are not always available.

## Decision

The plugin must not assume local filesystem access for Managed Folders.

It should prefer file listing and stream-based read/write APIs.

## Consequences

Positive:

- works across backends.
- avoids common Dataiku bugs.
- safer for large files.

Negative:

- file access code is slightly more complex.
- some local-only optimizations cannot be assumed.
