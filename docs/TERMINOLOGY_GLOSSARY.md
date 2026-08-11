# RAKL terminology glossary (lattice vs typed-relational)

Status: `ARCHITECTURE_TERMINOLOGY_INVENTORY / GLOSSARY_ONLY / NO_NAME_SELECTED / NO_DESTRUCTIVE_RENAME / NO_AUTHORITY_CHANGE`

This glossary inventories reader-facing terms from `ARCHITECTURE.md` (and the
issue #137 vocabulary table) against the v3 typed relational / compatibility
substrate. It **selects no project rename**, authorizes no API migration, and
changes no scientific authority.

Companion measurement inventory: [`docs/TERMINOLOGY_RENAME_INVENTORY_V1.md`](TERMINOLOGY_RENAME_INVENTORY_V1.md)
(reproducible via `python scripts/audit_terminology_inventory.py`).

Manuscript ledger (separate surface): `paper/TERMINOLOGY_LEDGER.md`.

---

## 1. Architectural premise (from ARCHITECTURE.md §13)

```text
The substrate is not asserted to be one global order-theoretic lattice.
Specialized closure/lattice structures remain valid where their order/closure
laws are actually established; the global software substrate is a typed
relational/compatibility structure.
```

Consequence for this glossary:

- **Lattice** is kept only where meet/join/closure semantics are actually
  justified (local structures, specialized contracts such as the failure
  experience lattice).
- Casual prose that calls an arbitrary graph, path set, or global knowledge
  space a “lattice” is historically load-bearing brand language, not a proved
  order-theoretic claim.

---

## 2. Inventory table — ARCHITECTURE / issue terms → typed-relational reading

| Term in ARCHITECTURE.md / historical prose | Typed-relational / compatibility reading | Keep as lattice? | Notes |
|---|---|---|---|
| Global lattice (§5) | Compatibility-constrained graph / compatibility landscape \(\Gamma \subseteq K_1 \times \cdots \times K_n\) | **No** (global) | §5 still says “lattice” in the heading and “paths through the lattice”; §13 retracts the global order-theoretic claim. Prefer “compatibility landscape” / “compatibility graph” in new prose. |
| Compatible paths through the lattice | Compatible routes / operator paths through \(\Gamma\) | No | Route semantics, not lattice joins. |
| Knowledge fiber / knowledge fibre (§3, §13) | Problem-conditioned fibre: derived query/view over the substrate for atom \(a\) under \((P,c)\) | N/A (fibre, not lattice) | Keep “fibre/fiber”; it is a view, not an authority-bearing DB. |
| Recursive knowledge fiber | Recursive problem fibre opened by a residual | N/A | Same object family as knowledge fibre. |
| v3 recursive experience substrate (§13) | Persistent typed relational substrate with overlapping views (evidence, knowledge, operators, experience, obstruction, strategies, meta-method) | Only local views if laws hold | Canonical global name: **typed relational / compatibility substrate**. |
| Problem-conditioned fibres | Compiled `ProblemFibre` retrieval/view | N/A | Keep. |
| Failure lattice (code/docs contract) | Specialized failure-experience structure with typed relations | **Yes, scoped** | Issue #137: keep where the specialized contract justifies it (`FailureExperienceLattice`). |
| Local lattice / closure | Local order/meet/join/closure structure | **Yes, scoped** | Only where laws are established. |
| Authority poset | Partial order of multi-axis certificates under compatible scope | No (poset ≠ lattice) | Manuscript ledger already forbids “authority lattice” unless lattice laws are proved. |
| Saturation / vector saturation (§12–§13) | Exploration / map-growth flatness diagnostic across seven axes | No | Not completeness of \(\Omega_P\); bounded flatness of retained novelty under a search policy. |
| Experience-conditioned routing | Search-priority overlay on compatible operators/paths | No | Priority ≠ scientific authority. |
| Strategy motifs / operator paths | Discovered navigable transition sequences | No | Roadmap/route language, not lattice paths. |
| Meta-lattice (historical) | Self-RAKL meta-method substrate / variant archive | **No** (global) | Prefer “meta-method substrate” / “variant landscape”. |
| Knowledge lattice (brand / informal) | Informal name for structured research/knowledge space | **No** as mathematics | Manuscript ledger: informal only unless meets/joins proved. |
| Lattice path (historical) | Roadmap / operator path / compatible route | No | Disambiguate by exact semantics. |
| Problem-solving algebra | Typed partial transition/operator system | N/A | Keep. |

---

## 3. Map / territory vocabulary (issue #137 comment; inventory only)

These terms are **proposed reader-facing vocabulary**, not adopted renames:

| Proposed term | Intended meaning | Authority |
|---|---|---|
| Territory \(\Omega_P\) | Unknown mathematical/research possibility structure | Never fully observed; not minted by RAKL |
| Substrate | Persistent stored evidence/knowledge/experience/tools/failures | Storage/memory, not theorem truth |
| Problem fibre | Problem-conditioned retrieval/view over the substrate | View only |
| Problem map \(M_t\) | Current partial model of states/relations/transitions | Derived planning model |
| Illuminated map \(I_t\) | Materially resolved/connected part of \(M_t\) | Map growth, not proof |
| Darkness | Unmapped or unresolved region | Never automatically false/impossible |
| Roadmap | Navigable transition subgraph extracted from the current map | Search control |
| Navigator / epistemic GPS | Search-control layer | Code name requires a separate benchmark |
| Saturation | Bounded map-growth / illumination flatness vector | Dashboard, not exhaustion of territory |
| Verifier | Decides local authority of candidate edges/claims | Verification authority only as separately gated |
| Terminal contract | What counts as arrival (proof/counterexample/…) | Certificate semantics |

---

## 4. Project-name expansion (recorded inconsistency; no decision)

Both forms appear in the repository and in released artifacts:

| Expansion | Role |
|---|---|
| Recursive Atomic Knowledge Lattice (singular) | README / packaging / some docs |
| Recursive Atomic Knowledge Lattices (plural) | Manuscript ledgers / some arXiv sources |

This glossary **does not** pick a winner, change the acronym, or authorize a
repository/package rename. See `docs/TERMINOLOGY_RENAME_INVENTORY_V1.md` §§3,7,8
for measured criteria and unscored candidates.

---

## 5. What this inventory closes vs leaves open

**Closed by this document + the measured inventory (#147):**

- Exact glossary mapping of lattice-vs-typed-relational terms used in
  `ARCHITECTURE.md` and the #137 table.
- Explicit keep/retire guidance for *mathematical* use of “lattice”.
- Pointers to measurement tooling and manuscript ledger surfaces.

**Deliberately open (no rename decision here):**

- Strategy A/B/C project-name choice.
- Class-1 prose sweeps, Class-2 API aliases, Class-3 package/repo renames.
- Adoption of “epistemic GPS” / “roadmap” as code identifiers.
- Rewriting immutable historical artifacts (forbidden).

---

## Authority boundary

Glossary / inventory only. No brand selection, no schema/API/gate change, no
theorem or method authority.
