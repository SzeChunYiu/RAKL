# Prose-transfer instrument v1 — the gate discriminated, and it did not pass

Terminal: `INSTRUMENT_NOT_PROBATIVE__TEMPLATE_INVERSION`

Authority: same-context analysis. Not independent review. Promotes nothing.

Protocol frozen at commit `bf925375`, as its own commit, before any instrument,
extractor or runner code existed in this branch. `confirmatory_outcomes_accessed`
was `false` at freeze. Executed once, on laptop billy, `~/rakl-verify`,
`.venv/bin/python` 3.11.14, at `f79e864e`.

## 1. Why the epoch exists

Two Paper II instruments had already been shown to contain no extraction signal:

| instrument | probe G finding |
| --- | --- |
| six-family robustness | gold and all six coordinates unchanged under text scramble, 810/810 |
| controlled-witness extraction | text inert 2592/2592; `extract(render(t)).public == t.public` byte-identically |

Shared mechanism: **the answer travelled alongside the text in a pre-parsed
sibling field, so no arm ever read the text.** The repair specification was that
an instrument is probative for extraction only if destroying the text destroys
performance, registered *before* outcome access rather than discovered in audit.

## 2. The acceptance test passes — this instrument does read text

`ProseTask.public` is empty. Gold lives in a `LatentSpec` no arm receives, and
is defined as a function of what the text *says*: a coordinate realized as
hedged or elided is `CANNOT_CHECK`, because that is what a perfect reader of
that text would conclude.

| probe G, heldout confirmatory set (n = 576) | |
| --- | --- |
| rendered surface changed by scramble | 576 / 576 |
| full arm output changed by scramble | 416 / 576 |
| **clean full exact** | **0.9722** |
| **scrambled full exact** | **0.2500** |

Scrambling destroys performance. This is the first instrument in this line for
which that is true.

Note the collapse is *below* the shuffle-equal-n null, not into it. The
registered wording for NC1 expected collapse into the null 95% interval
`[0.3385, 0.4149]`; the observed 0.2500 sits under it. The reason is that on
noise the extractor finds no authoritative construction and fails closed to
`CANNOT_CHECK` on every item, scoring exactly the `CANNOT_CHECK` share of gold.
That is a stronger collapse than chance, but it is not what the protocol said,
and it is recorded as a deviation rather than smoothed over. NC1's operative
requirement — that G1 fails under scrambled text — did hold.

**This says the instrument reads text. It says nothing about natural-language
extraction capability.** The renderer is synthetic and self-authored; probe-G
collapse on one's own renderer is evidence about the apparatus, not about prose.

## 3. Registered gates

| gate | requirement | observed | |
| --- | --- | --- | --- |
| G1 lower bound | advantage ≥ 0.10, McNemar p < 0.01, bootstrap excludes 0 | 0.4722, p = 1.8e-80, [0.4323, 0.5156] | **pass** |
| G2 upper bound | full exact **< 1.00** strictly | 0.9722 | **pass** |
| G3 error attribution | errors in ≥ 3 registered ambiguity classes | **1 class** | **FAIL** |
| G4 joint property | valid_accept ≥ 0.80 and FA ≤ 0.10, no trivial arm attaining both | 0.8958 / 0.000 | **pass** |
| G5 paired variance | both arms' per-item loss variance > 0 | both > 0 | **pass** |
| G6 seed spread | ≥ 12 seeds, ≥ 3 distinct advantage values | 12 seeds, **9 distinct**, [0.4653, 0.4809] | **pass** |
| G7 falsifier demo | all three negative controls must FAIL the gate | all three failed | **pass** |

G6 and G7 close the two apparatus defects that made the predecessor unfalsifiable:
the statistic now varies across seeds (probe B: previously 12/12 identical), and
runs that ought to fail do fail (NC1 scrambled text, NC2 shuffled gold, NC3
trivial arms).

G5 closes probe A: neither arm of the paired statistic is the gold function, so
both have variance. In the predecessor the `full` arm was bound to `verify` with
loss variance 1.2e-37.

### One honest qualification on G1

`strongest_non_extraction_parent` resolved to `P_PRIOR_MAJORITY` (exact 0.500),
tied with `P_ALWAYS_REJECT` (0.500) — **not** the text-reading parent. So the
registered 0.4722 advantage is measured against a constant arm.

The advantage over the text-reading parent `P_KEYWORD_POLARITY` (exact 0.4601)
is 0.5122, so the comparison also holds against a baseline that reads the text
but parses no structure. Both numbers are stated because the gate as frozen
picked the trivial one.

| arm | exact | valid_accept | invalid_FA | cc_recall |
| --- | --- | --- | --- | --- |
| `FULL_PROSE_EXTRACTOR` | **0.9722** | 0.8958 | 0.000 | 1.000 |
| `P_ALWAYS_REJECT` | 0.500 | 0.000 | 0.000 | 0.000 |
| `P_PRIOR_MAJORITY` | 0.500 | 0.000 | 0.000 | 0.000 |
| `P_LEXICAL` (thr 0.51, fitted on dev) | 0.4983 | 0.000 | 0.004 | 0.000 |
| `P_KEYWORD_POLARITY` | 0.4601 | 0.083 | 0.097 | 0.208 |
| `P_ALWAYS_ACCEPT` | 0.250 | 1.000 | 1.000 | 0.000 |
| `P_ALWAYS_CANNOT_CHECK` | 0.250 | 0.000 | 0.000 | 1.000 |

`always_reject` again attains FA = 0.000 while retaining nothing. Only the joint
property separates the arms, which is why G4 is written jointly.

## 4. Why G3 fails, and why that is the result

All 55 coordinate errors fall in **one** registered ambiguity class:

| class | errors / realizations |
| --- | --- |
| `E_QUALITATIVE` | **55 / 379** |
| `E_LITERAL` | 0 / 864 |
| `E_NEGATION` | 0 / 981 |
| `E_DISTRACTOR` | 0 / 872 |
| `E_UNIT` | 0 / 216 |
| `E_HEDGE` | 0 / 66 |
| `E_ELISION` | 0 / 78 |

By coordinate: `relation:E_QUALITATIVE` 53, `effect:E_QUALITATIVE` 2.

Read plainly: **outside the held-out degree lexicon, the extractor inverts the
renderer perfectly** — zero errors across 3,077 realizations of the other six
classes. The only genuine difficulty in the instrument is the one place where
the confirmatory vocabulary was deliberately made disjoint from development.
Everywhere the wording is templated, the surface is invertible by construction.

That is the template-inversion signature the registered ceiling was written to
catch, and it is the same class of finding as probe F's `mechanism exact3 =
0.000`: a number produced by construction rather than measured.

The gate discriminated. It just did not pass. **The 0.9722 is therefore not a
result about extraction**, and G1's large, highly significant advantage does not
rescue it — that is precisely why the gate was registered two-sided.

## 5. What this run does and does not establish

**Establishes.** An instrument in which destroying the text destroys
performance, whose gate has non-degenerate seed spread, whose paired statistic
has variance in both arms, and which rejects its own negative controls. Every
apparatus defect found in the predecessor (probes A, B, F, G) is closed and
measured, not argued. The probe-F repair works: sampling the violated
coordinate rather than assigning it per stratum gave all six coordinates as sole
discriminator (qoi 54, relation 52, effect 52, boundary 44, direction 43,
precondition 43), so no arm is zeroed by construction.

**Does not establish.** Anything about recovering applicability coordinates from
real scientific prose. The renderer is synthetic and authored by the same agent
as the extractor's cue lists — the registered acknowledged limitation. A 0.9722
whose errors live in exactly one class is a measure of how much of the surface
the author templated.

**Untouched.** The binding constraint remains a natural-domain packet at n ≈ 48
with **external** labels. Prose-extraction natural-domain items sit at n = 16
with internally authored coordinates. `#608`'s boundary
`INSTRUMENT_ONLY__NO_EMPIRICAL_EXTRACTION_CLAIM` is preserved and is not
weakened by this run.

## 6. Revival specification for a successor epoch

A negative or not-probative terminal is intermediate, not terminal, and demands
an improvement path. What a successor must change, in order of leverage:

1. **The renderer must not be authored by whoever writes the extractor.** The
   single-author coupling is what produced 0 errors in six of seven classes. The
   cheapest real fix is an externally sourced surface, not a wider self-authored
   bank — widening the bank would move G3 without changing what it measures.
2. **Every ambiguity class needs a held-out realization**, not just
   `E_QUALITATIVE`. Held-out unit systems, held-out distractor discourse forms
   and held-out negation constructions would make G3 informative rather than a
   single-lexicon probe.
3. **Do not raise the ceiling.** G2 passed at 0.9722; the failure is G3. A
   successor that reports a lower exact score with errors spread across classes
   is strictly better evidence than one that reports a higher score.

Explicitly rejected as a repair: adding "exhausts" and "far side" to the cue
lists. That would move `full_exact` toward 1.00 and G3 toward zero classes,
i.e. further into template inversion while looking like an improvement.

## 7. Reproduction

```
PYTHONPATH=src:. .venv/bin/python \
  experiments/paper2/run_prose_transfer_confirmatory_v1.py --out <dir>
```

Receipt: `results/CONFIRMATORY_RESULT.json`.
