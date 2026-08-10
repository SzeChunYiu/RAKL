# Content-addressed canonical archive

Status: Round 044 / V2.1 reference implementation.

Implementation: `src/rakl/content_addressed_archive.py`

## 1. Why the archive is separate from the lattice

The Knowledge Atlas answers semantic questions: what claims, regimes, representations, relations, contradictions and evidence lineages are registered? The canonical archive answers a different question: what exact source bytes must remain recoverable so those scientific objects can be audited or rehydrated?

A bounded active lattice does not imply a bounded historical archive. RAKL must therefore control archive cost without allowing storage pressure to silently erase scientific history.

## 2. Raw-content identity

For a raw payload `e`, the reference archive uses

```text
h = SHA256(e)
```

as the physical content identity.

The hash is computed over the **raw uncompressed payload**. Compression or cold-tier placement cannot change source identity.

A logical canonical record has its own immutable `record_id` and points to a payload hash. This lets RAKL preserve multiple provenance events or source aliases without storing byte-identical content repeatedly.

Rebinding one existing canonical `record_id` to different bytes is forbidden.

## 3. Physical deduplication

If two logical records contain identical bytes, they share one stored blob:

```text
logical records: 2
physical blobs:   1
```

This is byte deduplication only. It does not assert that two separately worded claims are scientifically equivalent, nor does it collapse evidence-lineage independence. Semantic identity remains an atlas/identity-resolution operation.

## 4. Lossless compression

On first insertion of a unique blob, the reference backend compares the raw payload with a deterministic zlib representation. Compression is used only when it is strictly smaller.

The physical blob records:

```text
raw payload hash
raw byte length
stored byte length
codec = RAW | ZLIB
stored payload
storage tier = HOT | COLD
```

Rehydration decompresses when necessary and verifies both raw length and SHA-256 before returning bytes. A compression error therefore cannot silently mint a different source.

This is **physical lossless compression**, different from RAKL's lossy semantic memory views. Lossy summaries remain rebuildable navigation/context artifacts and can never replace canonical raw evidence for strong verification.

## 5. Hot and cold tiers

Cold demotion is a storage-temperature change, not deletion.

A `HotArchivePolicy` can bound:

```text
max_hot_stored_bytes
max_hot_unique_blobs
```

The planner protects explicitly mandatory record ids, then deterministically proposes non-protected hot blobs for cold demotion. The reference policy uses largest-first byte reduction with hash tie-breaking.

After demotion:

- logical canonical records are unchanged;
- total stored bytes are unchanged;
- hot bytes/blobs can decrease;
- cold bytes/blobs increase;
- rehydration remains exact.

If protected evidence alone cannot fit the registered hot capacity, the planner returns `CANNOT_SATISFY_WITH_PROTECTED_SET`. It does not delete the protected evidence or pretend the capacity constraint was satisfied.

## 6. Storage metrics

The reference backend reports:

```text
logical_records
unique_blobs
logical_raw_bytes
unique_raw_bytes
stored_physical_bytes
hot_stored_bytes
cold_stored_bytes
hot_unique_blobs
cold_unique_blobs
deduplicated_raw_bytes
compression_saved_bytes
combined_saved_bytes
storage_to_logical_ratio
```

These metrics answer physical engineering questions and must not be interpreted as scientific novelty or knowledge value.

## 7. Three independent capacity planes

RAKL now distinguishes:

1. **canonical physical archive capacity** — deduplication, exact lossless compression and hot/cold placement;
2. **active lattice capacity** — reject fully redundant active updates or compact/demote a materialized atlas view while preserving canonical roots;
3. **prompt capacity** — compile the smallest mandatory target-conditioned context under the model token budget or fail closed.

A fourth control plane, search/tool budget, remains intentionally non-terminal: exhausting resources is not semantic saturation.

## 8. Reference vs production backend

`ContentAddressedArchive` is an in-memory deterministic reference implementation. It establishes observable semantics and tests, not production durability.

A production adapter should preserve the same contracts while adding at least:

- durable object storage;
- independent metadata/record ledger;
- atomic writes and crash recovery;
- checksum verification during reads and migrations;
- encryption/access controls appropriate to the deployment;
- hot/warm/cold backend adapters;
- lifecycle and retention policy without unauthorized evidence deletion;
- storage accounting and cost telemetry;
- backup/replication and restore tests.

Until such an adapter is implemented and benchmarked, RAKL may claim a tested storage **contract and reference backend**, not production-scale storage closure.

## 9. Known-answer archive demo

`src/rakl/mini_archive_demo.py` reuses the eight raw pendulum sources from the V2 mini research world. It stores the eight canonical source payloads, performs a byte-identical refetch of the first source, and then cold-demotes all but three protected evidence blobs.

The corresponding CI output is intended to show three engineering properties with actual numbers:

1. exact refetch increases the logical record count but adds zero physical blob bytes;
2. any beneficial lossless compression is measured rather than assumed;
3. hot-state reduction does not delete canonical records and all source payloads rehydrate exactly.

The demo is an engineering contract check and does not establish scientific superiority.
