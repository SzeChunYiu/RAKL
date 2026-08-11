# YM-E1a observable-interface source addendum — 2026-08-11

**Scope:** primary-source support for the non-candidate observable-interface calibration. This addendum does not prove a continuum limit, reflection-positive continuum algebra, or mass gap.

## OI-S0 — official target / observable-level continuum obligation

Arthur Jaffe and Edward Witten, *Quantum Yang–Mills Theory*, Clay Mathematics Institute.

- https://www.claymath.org/wp-content/uploads/2022/06/yangmills.pdf
- The official discussion treats Wilson lattice gauge theory as a reflection-positive regulator but identifies continuum/infinite-volume limits of gauge-invariant observable expectations as a missing obligation.
- The Balaban discussion is used only to motivate the exact missing transfer: ultraviolet control of the lattice theory is not yet observable-level construction of the required continuum QFT.

## OI-S1 — fixed-cutoff lattice reflection positivity

K. Osterwalder and E. Seiler, *Gauge theories on a lattice*, Annals of Physics **110** (1978), 440–471.

**Retained use:** positive-half-space gauge-invariant lattice observables have a natural reflection-positive fixed-cutoff setting under the Wilson regulator.

**Boundary:** this supplies neither cutoff removal nor renormalization of a continuum observable family.

## OI-S2 — Wilson-loop renormalization is nontrivial

R. A. Brandt, F. Neri and M.-a. Sato, *Renormalization of loop functions for all loops*, Physical Review D **24** (1981), 879.

- DOI: https://doi.org/10.1103/PhysRevD.24.879

The paper proves perturbative renormalizability of Wilson-loop functions, including the extra local renormalization structure associated with cusps and self-intersections.

**Retained use:** a Wilson-loop interface cannot simply identify bounded lattice loops across refinements and call the limit renormalized; geometry-dependent perimeter/cusp/intersection renormalization is a load-bearing coordinate.

**Boundary:** this is perturbative renormalization, not a nonperturbative constructive cutoff-removal theorem for 4D pure Yang–Mills.

## OI-S3 — positive-flow-time gauge-invariant fields as UV-regular probes

M. Lüscher, *Properties and uses of the Wilson flow in lattice QCD*, JHEP 08 (2010) 071.

- arXiv: https://arxiv.org/abs/1006.4518

The paper identifies positive-flow-time gauge fields as smooth renormalized fields and local gauge-invariant expressions at positive flow time as well-defined probes at length scale of order `sqrt(t)`.

M. Lüscher and P. Weisz, *Perturbative analysis of the gradient flow in non-abelian gauge theories* (2011).

- arXiv: https://arxiv.org/abs/1101.0963

The all-orders perturbative analysis shows finiteness of correlation functions of the flowed field once the underlying four-dimensional theory is renormalized in the usual way.

**Retained use:** positive-flow-time composites are a strong calibration family for UV regularity and non-trivial continuum response.

**Critical boundaries:**

1. the finiteness theorem is perturbative and assumes the underlying 4D theory is already renormalized; it cannot supply the missing constructive existence theorem;
2. positive flow time introduces a physical smearing scale, so these observables are not the final local `t=0` Wightman/OS field algebra;
3. standard Euclidean-time reflection positivity for flowed observables is not assumed here. Four-dimensional diffusion can mix support across a reflection plane, so a separate support/reflection theorem would be required before using the flowed family as the OS-positive core algebra.

## OI-S4 — Balaban marked-observable gap remains open in this packet

T. Balaban's 4D lattice gauge RG series remains the same-problem multiscale backbone recorded in `YM_SOURCE_PACKET_20260811.md`.

**Calibration conclusion from source inspection:** the present packet contains no primary theorem showing that Balaban's RG map closes, with cutoff-uniform estimates, after adjoining a finite or controlled family of renormalized gauge-invariant source insertions. No such result is inferred from unmarked partition-function/effective-action control.

## Source-bound calibration boundary

These sources support only the following decisions:

- Wilson loops are the strongest exact lattice gauge-invariant / fixed-cutoff reflection-positive core candidate, but their continuum renormalization and locality role are nontrivial.
- Positive-flow-time local composites are useful UV-regular diagnostic probes but cannot be promoted to the final OS-positive local algebra without additional theorems.
- A source-generating functional is therefore treated as an **interface/wrapper** that can carry multiple observable strata and expose source mixing/derivative estimates to the RG, not as a claim that source-dependent 4D Yang–Mills has already been constructed.

No source here proves `YM-E1a` or the Yang–Mills root problem.
