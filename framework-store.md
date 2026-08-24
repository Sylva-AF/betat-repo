---
title: Framework Store
parent: For Builders
nav_order: 8
---

# Store Functions

`betat_community.store.store` is the append-only provenance store's entire write and read API — `append`/`get`/`list_records`/`verify_integrity` only, deliberately no `update`/`delete`. Useful if you're extending the framework in Python rather than going through the JSON API; the API endpoints in [API Endpoints](framework-api.html) are themselves built on exactly these functions.

```python
from betat_community.store import store
```

## `store.append(record_data)`

Validates a PROVENANCE_SPEC record dict, computes its `record_id` server-side (any caller-supplied `record_id` is ignored — a client-supplied hash would be an attack surface), and inserts it. Raises `django.core.exceptions.ValidationError` on anything that doesn't conform (missing fields, `hi_tag` not `true`, `content.type` not matching `community.content_type`).

```python
record = store.append({
    "betat_version": "0.1",
    "timestamp": "2026-09-01T12:00:00Z",
    "hi_tag": True,
    "provenancier": {"identity": "did:key:z6Mkf...", "identity_type": "cryptographic_key",
                      "authentication_method": "cryptographic_signature", "display_name": "Ada Lovelace"},
    "content": {"type": "text", "location": "https://archive.example/note",
                "content_hash": "sha256:...", "language": "en"},
    "community": {"id": "example.org", "name": "Example", "domain": "notes",
                  "content_type": "text", "store_uri": "https://example.org/betat/records"},
    "verification": {"method": "editorial_review", "verified_by": "verifier-1",
                      "verification_timestamp": "2026-09-01T12:00:01Z"},
    "declaration": {"text": "I declare...", "language": "en", "custom_addition": "human-originated, community-verified"},
})
print(record.record_id)
# '7c4a1d29e8f3b6a5d0c2f47e91b8a3d6c5e2f0a9b7d4c1e8f6a3b0d7c4e1f8a2'
```

In practice `workflow/record_builder.py`'s `build_record()` composes this dict for you from a `Submission` — see [API Endpoints](framework-api.html)'s `/betat/review/{id}`.

## `store.get(record_id)`

```python
record = store.get('7c4a1d29e8f3b6a5d0c2f47e91b8a3d6c5e2f0a9b7d4c1e8f6a3b0d7c4e1f8a2')
```

Raises `ProvenanceRecord.DoesNotExist` if there's no match.

## `store.list_records(since=None, page=1, page_size=50)`

Newest first, optionally filtered to records after `since` (an ISO 8601 timestamp string — same format as `record.timestamp`).

```python
latest = store.list_records(page=1, page_size=20)
new_since_last_check = store.list_records(since='2026-08-01T00:00:00Z')
```

## `store.verify_integrity(record_id)`

Recomputes the record's hash from its current stored content and compares it to the stored `record_id`. `False` means tampering (or, in a conforming store, something that should never happen).

```python
store.verify_integrity(record.record_id)  # True
```
