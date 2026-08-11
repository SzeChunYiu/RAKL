# Terminology and rename dependency inventory (issue #137, v1)

Status: `ARCHITECTURE_TERMINOLOGY_RESEARCH / INVENTORY_ONLY / NO_NAME_SELECTED / NO_DESTRUCTIVE_RENAME / NO_AUTHORITY_CHANGE`

This document delivers steps 1–4 of the issue #137 AI-session pickup contract: build the
dependency inventory, separate mathematically incorrect terminology from historical/brand
terminology, freeze naming criteria, and generate candidate names. It deliberately stops
before step 5 (adversarial selection) and before any prose migration.

**Nothing here selects a name, authorizes a rename, or changes any authority.**

Measurements are reproducible:

```bash
python scripts/audit_terminology_inventory.py --json /tmp/terminology.json
```

Subject measured: `bd1a2768f0f474ff44ffa25243241f94bfaf6466`. Counts below are occurrences
in the **content** of tracked files; re-run the auditor rather than trusting this snapshot.

Counting basis, stated so the numbers are not over-read: file and directory *paths* are
not counted. A module named `src/rakl/failure_lattice.py` contributes only the occurrences
inside its text. Any Class-2/Class-3 migration therefore carries an additional path/symbol
rename cost that these content counts do not include and that §6 does not yet enumerate.

---

## 1. The central measurement

The issue's premise is that the word *lattice* misleads. The inventory shows the
mathematically load-bearing part of that problem is **far smaller** than the raw footprint:

| Class | Occurrences | Files | In immutable archives |
|---|---|---|---|
| Phrases asserting a *global* order-theoretic structure | **34** | 33 | 4 |
| — `knowledge lattice` | 22 | 21 | 3 |
| — `global lattice` | 9 | 9 | 1 |
| — `meta-lattice` | 2 | 2 | 0 |
| — `lattice path` | 1 | 1 | 0 |
| `failure lattice` (specialized contract; issue says keep) | 86 | 42 | 10 |
| `lattice` — every occurrence, all senses | 1223 | 210 | 120 |

So the phrases whose ordinary reading contradicts `ARCHITECTURE.md` account for
**≈2.8 % of the total `lattice` footprint**, and only **30 live occurrences** once
immutable archive artifacts (which must not be rewritten) are excluded.

**Consequence for sequencing:** a Class-1 reader-facing correction of ~30 occurrences
captures essentially all of the *mathematical* inaccuracy. The remaining ~1189 occurrences
are brand usage, the justified `FailureLattice` contract, local lattice/closure structures
where meet/join semantics are explicit, and frozen historical text. This supports the
issue's own step 6 ("prefer terminology-only migration first if it captures most of the
benefit") with counted evidence rather than impression.

---

## 2. The manuscript layer is already guarded

`paper/TERMINOLOGY_LEDGER.md` (and its two identical copies, see §5) already binds:

- `knowledge lattice` → "informal project name for the structured research/knowledge
  space", explicitly *not* "mathematical lattice unless meets/joins are actually proved";
- `authority poset` → explicitly *not* "authority lattice, unless lattice laws are proved".

The manuscript surface therefore already carries the caveat the issue asks for. The gap is
in **repository reader-facing surfaces** (`README.md`, `docs/`) and in the **acronym
expansion itself**, which no ledger row currently qualifies.

---

## 3. Previously unrecorded defect: the project name is not self-consistent

The acronym expansion exists in **two different forms** on current main:

| Form | Files | Examples |
|---|---|---|
| `Recursive Atomic Knowledge Lattices` (plural) | 13 | all three `TERMINOLOGY_LEDGER.md` copies, `paper/arxiv/main.tex`, `paper/arxiv_release_2026-08-10/main.tex`, `paper/archive/releases/2026-08-10-v1/main.tex`, paper-02 lineage sections |
| `Recursive Atomic Knowledge Lattice` (singular) | 7+ | `README.md`, `pyproject.toml`, `skills/rakl-core/SKILL.md`, `docs/PAPER_STRATEGY.md`, `docs/AUTHORITY_POSET.md` |

Both forms appear in released/arXiv-bound sources. This is decision-relevant: the
"continuity with published work" naming criterion (§6) must account for the fact that
there are already **two published expansions**, not one. Whichever direction #137 takes,
this inconsistency should be recorded rather than silently normalized, and the frozen
release artifacts must not be rewritten.

---

## 4. Vocabulary proposed by #137 that does not yet exist

| Proposed term | Current occurrences | Migration cost | Note |
|---|---|---|---|
| `epistemic GPS` | **0** | none | no incumbent usage; code name requires a benchmark first per the issue |
| `roadmap` | **0** | none | free to adopt as reader-facing vocabulary |
| `problem map` | **0** | none | free to adopt |
| `landscape` | 19 (11 immutable) | low | already used informally, mostly in archive |
| `territory` | 21 (1 immutable) | low | already used informally |

A zero count means zero migration cost **and** zero established meaning — these terms would
be introduced, not migrated. The issue's own comment distinguishes *territory* (unknown
possibility structure) from *problem map* (RAKL's constructed approximation); adopting
`Landscape` into the project name while also using it for the map would re-create exactly
the map/territory conflation the comment warns about.

---

## 5. Class-2 (API alias) surface

Symbols a compatibility-preserving alias migration would have to carry:

| Symbol | Occurrences | Files |
|---|---|---|
| `KnowledgeFiber` / `knowledge fibre` | 81 | 38 |
| `SaturationVector` / `saturation_vector` | 38 | 11 |
| `ProblemFibre` / `problem_fibre` | 36 | 16 |

Note also that `paper/TERMINOLOGY_LEDGER.md`, `paper/shared/editorial/TERMINOLOGY_LEDGER.md`
and `publishing/editorial/TERMINOLOGY_LEDGER.md` are **byte-identical** (SHA-256
`57d026e781be…`). Any glossary change is a three-path edit unless one is made canonical and
the others generated. That duplication is itself a migration hazard: a partial update would
silently create three disagreeing canonical ledgers.

---

## 6. Class-3 (repository/package rename) blast radius

| Surface | Measured |
|---|---|
| Python distribution/import name | `rakl` (`pyproject.toml`) |
| Python files importing `rakl` | **143** |
| Schema files | **96** |
| Distinct schema `$id` namespaces | **1** (canonical; see #148) |

Historical measurement (pre-#148, when this inventory was first frozen):

```text
https://github.com/SzeChunYiu/RAKL/schemas   52
https://example.invalid/rakl                 32
https://rakl.dev/schemas                      2
https://rakl.example/schemas                  1
```

Current state after #148: every `schemas/*.schema.json` `$id` uses the single
canonical base `https://github.com/SzeChunYiu/RAKL/schemas/`. The former
four-namespace split was an independent consistency defect (tracked as #148), not
a rename consequence. A repository rename would still rewrite that one GitHub-bound
base; the difference is that the blast radius is now uniform rather than partial.

Not yet inventoried here, and required before any Class-3 decision: `RAKL_math` framework
pin/config/submodule paths, external URLs, published citation strings, and historical
receipt payloads. Those live outside this repository or inside immutable artifacts and need
their own bounded coverage receipt.

---

## 7. Frozen naming criteria

Frozen before any candidate is scored, per the issue's step 3. No weights are assigned;
weighting is a governance decision.

```text
C1  architectural accuracy        — matches the typed relational/compatibility substrate
C2  mathematical accuracy         — asserts no global structure that is not proved
C3  reader understandability      — a new reader is not misled within one minute
C4  memorability
C5  continuity with published work — including BOTH existing published expansions (§3)
C6  migration cost                — measured against §5 and §6, not estimated
C7  package/repository stability  — `import rakl`, 96 schema `$id`s, CI, RAKL_math pins
C8  searchability / ambiguity     — distinguishable from existing projects
C9  domain coverage               — science + mathematics + engineering
C10 capability coverage           — knowledge + experience + planning + verification + self-evolution
C11 map/territory hygiene         — the name must not conflate RAKL's model with the space it models
```

C11 is added from the issue's own follow-up comment and is not in its original list.

---

## 8. Candidate set (generated, not scored, not selected)

| Strategy | Candidate | First-pass notes (not a verdict) |
|---|---|---|
| A — keep acronym, change expansion | Recursive Atomic Knowledge Landscape | conservative; but see §4 C11 risk of colliding with map/territory usage |
| A | Recursive Adaptive Knowledge Landscape | drops "Atomic", which is load-bearing for decomposition |
| A | Recursive Atomic Knowledge Learning | foregrounds experience/self-evolution; weakest on C1 structure |
| B — brand only, no forced expansion | `RAKL` as a project name | lowest C6/C7 cost; resolves §3 by retiring both expansions; loses mnemonic |
| C — full rename | (not generated) | requires §6 completion incl. RAKL_math and citation surfaces first |

Strategy C candidates are deliberately **not** generated: per §6 the Class-3 inventory is
incomplete (RAKL_math pins, external URLs, citations), so generating names would invite a
choice made against unmeasured cost.

---

## 9. What a successor session must do next

1. ~~Resolve the four-namespace schema `$id` defect (§6)~~ — closed by #148; Class-3
   rename reasoning may now treat schema `$id` as one uniform GitHub-bound base.
2. Decide how to record, not erase, the singular/plural expansion split (§3).
3. Complete the Class-3 inventory across `RAKL_math`, external URLs and citation strings.
4. Only then run step 5 (adversarial review of candidates against §7) and step 10 (publish a
   migration/glossary table) before touching reader-facing prose broadly.
5. Never rewrite immutable historical artifacts to match new terminology; the 120 archive
   occurrences of `lattice` correctly describe their frozen versions.

---

## Authority boundary

Measurement and option-framing only. This inventory selects no name, authorizes no
migration, changes no schema/API/gate, and creates no scientific or method authority.
Issue #137 remains open.
