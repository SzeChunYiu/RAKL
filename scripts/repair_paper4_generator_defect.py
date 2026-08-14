from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "publication" / "papers" / "paper-04-structural-learning-mechanics" / "main.tex"


REPLACEMENTS = (
    (
        "The paper makes no positive empirical claim for adaptive allocation, but it does report the executed Phase-0/1 prerequisite instrument on the frozen Qwen2.5 0.5B--7B ladder: across every model and exposure count it returns a \\emph{supported negative}---no state-dependent structural residual---so the Phase-2 adaptive-versus-static scheduler is deliberately not built. Only the simplest family was learnable, and only unstably. This is the protocol working as designed: the negative absorbs the mechanism back toward the sibling method-evolution paper rather than manufacturing a spurious contribution, and it locates the obstruction at the instrument's capability floor rather than in the mechanism itself.",
        "The paper makes no positive empirical claim for adaptive allocation. It reports the executed Phase-0/1 v1 instrument only as \\emph{invalidated diagnostic history}: root-cause analysis found that each structural family contained only two unique rendered inputs, so the run could not identify rule learning or a state-dependent structural residual. Stronger training still collapsed to a constant predictor, while the apparent \\texttt{state\\_reachability} signal was confounded by an input-length difference. The v1 run therefore supports no mechanism or capability-floor conclusion; it is preserved as negative instrument history. A varied, length-matched v2 generator with disjoint train/probe instances and a learnability positive-control gate is required before Phase~1 can test the residual.",
    ),
    (
        "\\textbf{Status: design-and-protocol preprint; the Phase-0/1 prerequisite instrument has been executed and returns a supported negative; no positive empirical claim is made.}",
        "\\textbf{Status: design-and-protocol preprint; the executed Phase-0/1 v1 instrument is invalidated by a generator defect and grants no mechanism conclusion.}",
    ),
    (
        "This document preregisters a Phase~0--4 protocol and reports \\emph{one} executed step: the Phase-0/1 exposure instrument (\\#461) run on the frozen Qwen2.5 0.5B--7B ladder (\\S\\ref{sec:phase1-result}). That run returns a \\emph{supported negative}---no state-dependent structural residual on any model---so the Phase-2 adaptive-versus-static scheduler is deliberately \\emph{not} built and no accuracy, effect-size or cost claim for adaptive allocation is made. Every quantitative value in the protocol sections is a preregistered threshold or design parameter chosen \\emph{before} data access; the reported Phase-0/1 numbers are read directly from the frozen instrument and grant no scientific or promotion authority. A standalone \\emph{positive} empirical paper remains conditional on (i) the later training programme (\\#466/\\#467/\\#468), (ii) a trainable, sufficiently capable in-ladder model and authorized compute, and (iii) affirmative authorization at gate \\#462. The residual hypothesis is therefore \\emph{unresolved at the tested capability level}, with the obstruction located at the instrument's capability floor rather than shown to be in the mechanism.",
        "This document preregisters a Phase~0--4 protocol and preserves one executed v1 Phase-0/1 run (\\#461) as invalidated instrument history (\\S\\ref{sec:phase1-result}). Root-cause analysis shows that the frozen v1 generator exposed only two unique rendered inputs per family; constant-predictor behaviour survives stronger training, and the apparent \\texttt{state\\_reachability} signal is confounded by input length. Consequently the v1 numbers are diagnostic observations, not a supported negative and not evidence for a model capability floor. Phase~2 remains closed because Phase~1 has not yet produced a valid residual test. A v2 generator must vary instances, length-match labels, separate train/probe instances and pass a learnability positive-control gate before any mechanism conclusion is eligible.",
    ),
    (
        "\\section{Phase-0/1 instrument result on the frozen ladder}",
        "\\section{Phase-0/1 v1 diagnostic and generator-defect root cause}",
    ),
    (
        "\\caption{Executed Phase-0/1 terminals on the frozen Qwen2.5 ladder (seed 461). Read directly from the frozen instrument; no value is a promotion signal.}",
        "\\caption{Executed v1 Phase-0/1 diagnostic terminals on the frozen Qwen2.5 ladder (seed 461). Subsequent root-cause analysis invalidates these terminals as mechanism evidence because the generator exposes only two unique rendered inputs per family. The table is retained as negative instrument history, not a promotion or capability signal.}",
    ),
    (
        "\\caption{Phase-0/1 exposure instrument on the frozen Qwen ladder. \\textbf{(a)}~Same-structure accuracy versus exposure for \\texttt{state\\_reachability}, the only learnable family: the $3$B model acquires and holds it, the $7$B model acquires then forgets it, and the two smaller models stay at chance. \\textbf{(b)}~The other two families never leave chance for any model (shown for $7$B; identical pattern across the ladder). This is a system/instrument measurement, not a scientific-authority or promotion signal.}",
        "\\caption{Invalidated v1 Phase-0/1 instrument trace on the frozen Qwen ladder. \\textbf{(a)}~The apparent \\texttt{state\\_reachability} signal is not credited as structural learning because valid inputs are systematically longer than invalid inputs. \\textbf{(b)}~The other two families remain at chance, but the generator contains only two unique rendered inputs per family and stronger training collapses to a constant predictor. The figure is preserved as an instrument-defect diagnostic, not mechanism evidence.}",
    ),
    (
        "The registered gate for the central mechanism---the same-structure marginal value falling after principle mastery while unsaturated coordinates still gain (\\texttt{MECHANISM\\_SIGNAL\\_PRESENT})---is \\emph{not} reached by any model (Table~\\ref{tab:phase1-terminals}, Figure~\\ref{fig:phase1-result}). Only \\texttt{state\\_reachability}, the simplest family, is learnable at all, and only unstably; \\texttt{balance\\_conservation} and \\texttt{sequence\\_composition} remain at chance for every model and every exposure. By the frozen protocol this is a \\emph{supported negative}: the learner-conditioned structural residual is unsupported at the tested capability level, so the Phase-2 adaptive-versus-static scheduler is not built and the mechanism is absorbed back toward the sibling method-evolution paper, exactly as \\S\\ref{sec:threats} anticipates. Crucially, the obstruction is located at the instrument's capability floor, not shown to be in the mechanism: the frozen Qwen ladder cannot consistently clear the floor of even this deterministic known world, mirroring the wider series' \\texttt{CAPABLE\\_MODEL\\_AVAILABLE}=\\texttt{NO\\_REFUTED} blocker. Testing whether the residual exists for a model that \\emph{does} clear the floor requires a capable in-ladder model and authorization at gate \\#462; that experiment is not run here and no positive result is implied.",
        "The v1 run cannot identify the central mechanism. Root-cause analysis of the frozen generator shows that each family contains only two unique rendered inputs: every valid example within a family is identical and every invalid example is identical. Stronger LoRA training remains a constant predictor on the affected family rather than demonstrating rule generalization. The apparent \\texttt{state\\_reachability} improvement is additionally confounded by valid examples containing more edges than invalid examples. These observations classify the v1 packet as an \\emph{instrument/generator defect}. Its terminal labels remain frozen historical outputs, but they no longer support the claims \\texttt{NO\\_STATE\\_DEPENDENT\\_RESIDUAL}, \\texttt{MODEL\\_FLOOR} or \\texttt{REPETITION\\_REMAINS\\_VALUABLE} as evidence about the intended mechanism. Phase~2 is still not built, now for the stronger reason that a valid Phase~1 prerequisite has not yet been executed. The repair is a v2 generator with varied instances per family, length-matched valid/invalid cases, disjoint instance-level train/probe sets and a learnability positive-control gate. The residual hypothesis therefore remains unresolved.",
    ),
    (
        "The Phase-0/1 prerequisite instrument has been executed on academic HPC (\\S\\ref{sec:phase1-result}) and returned a supported negative on the frozen ladder.",
        "The Phase-0/1 v1 instrument has been executed on academic HPC (\\S\\ref{sec:phase1-result}) but is invalidated as a mechanism test by the generator defect; a repaired v2 prerequisite must pass before the powered programme can open.",
    ),
    (
        "This paper reports no experiment; it preregisters one.",
        "This paper reports one invalidated v1 instrument diagnostic as negative history and preregisters the repaired mechanism experiment; it reports no valid adaptive-allocation result.",
    ),
)


STALE_PHRASES = (
    "returns a supported negative",
    "By the frozen protocol this is a \\emph{supported negative}",
    "obstruction located at the instrument's capability floor",
)


def repair(text: str) -> str:
    # The repair exists to strip over-claim language from the retracted
    # Paper IV v1 narrative. If no over-claim phrase remains, the paper is
    # already honest and the repair is a no-op -- it must not error just
    # because surrounding prose has since been re-worded past the original
    # target strings (the retraction framing evolved after these targets
    # were written). Key on the honesty condition (stale-phrase absence),
    # not on exact prose match.
    if all(stale not in text for stale in STALE_PHRASES):
        return text
    updated = text
    for old, new in REPLACEMENTS:
        if old not in updated:
            raise RuntimeError(f"required stale Paper IV passage not found: {old[:90]!r}")
        updated = updated.replace(old, new, 1)
    for stale in STALE_PHRASES:
        if stale in updated:
            raise RuntimeError(f"stale Paper IV mechanism conclusion survived repair: {stale!r}")
    return updated


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    repaired = repair(text)
    TARGET.write_text(repaired, encoding="utf-8")
    print("PAPER4_GENERATOR_DEFECT_REPAIR=PASS")
    print("MECHANISM_CONCLUSION=v1_invalidated_no_conclusion")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
