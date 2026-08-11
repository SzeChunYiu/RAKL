# Paper 2 V3.2.1 harvest repair — same-context hostile review

Date: 2026-08-11

## Independence boundary

This is internal same-context hostile review, not independent review or peer
review. Native scheduler and receipt bytes dispose of claims; prose confidence
does not.

## Initial findings

### P2-V321-HR-B01 — in-place V3.2 mutation would break native lineage

**Disposition.** V3.2 runtime, contract, final-path receipt and original
`HARVEST_CANNOT_CHECK` are byte-immutable. V3.2.1 is a separate harvest-only
runtime, script, schema and self-bound contract. It has no submit or stage
command.

### P2-V321-HR-B02 — generic PEP 508 acceptance would weaken the lock

**Disposition.** Only the two exact bundled pip/setuptools file URLs and wheel
hashes observed natively are admitted. Synthetic URL, hash, generic HTTPS,
equality substitution, duplicate and missing worlds fail closed. The parsed map
must still equal all 31 installed name/version pairs exactly.

### P2-V321-HR-B03 — repair could erase the original cannot-check result

**Disposition.** A new harvest requires the exact prior receipt, its sole
failure, identical job ids/scheduler rows and matching bootstrap, submission,
probe and staging hashes. The new receipt retains the prior path/hash. The old
receipt is not rewritten.

### P2-V321-HR-B04 — local success could be confused with native re-harvest

**Disposition.** Known-answer and planted-hostile tests establish only local
validator behavior. The operator state is
`HARVEST_REPAIR_READY_NOT_REHARVESTED`. No positive native harvest is claimed
until the merged exact subject re-reads the same remote evidence.

### P2-V321-HR-B05 — contract subject and jobs could be disconnected from execution inputs

**Disposition.** The repair now requires source SHA
`c10ba7a261af02cc42690022226555a3197351ae`, source tree
`4f8053958d9ed4ea6e506ffa6dc8e60ee36715a5`, source-contract canonical
identity and exact jobs `3475123`/`3475124` in the operational inputs. Wrong or
swapped identities fail closed.

### P2-V321-HR-B06 — an additive output could overwrite protected evidence

**Disposition.** The runtime requires distinct repair/source checkouts, refuses
outputs inside either checkout or any source evidence root, refuses existing or
symlink outputs and temporaries, and creates the temporary receipt exclusively.

### P2-V321-HR-B07 — raw scheduler, bundle and cumulative counts were prose-only

**Disposition.** The runtime derives the two root scheduler rows from raw
`sacct --json` and byte-compares all seven tar members with the ingested
receipts/logs. A schema-validated synthesis receipt derives the cumulative
six/zero/zero counts from the three exact submission receipts.

### P2-V321-HR-B08 — fail-open schemas and structural CANNOT_CHECK worlds

**Disposition.** The repair-contract schema is closed and requires every
governed field and exact binding-role set. The harvest schema tightly constrains
a pass while allowing missing evidence to remain a schema-valid
`HARVEST_CANNOT_CHECK`. The reproduced V3.2 semantic hash excludes only the
fresh timestamp and is repeatable.

## Current verdict

`PASS__HARVEST_REPAIR_READY_NOT_REHARVESTED`

No V3.2.1 job, model execution, evaluated result or performance figure exists.
