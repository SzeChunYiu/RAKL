# RAKL Verified Discovery — Navier–Stokes

This directory is the persistent RAKL workspace for the 3D incompressible Navier–Stokes Millennium problem.

## Root control surface

GitHub issue: `#83` — **Verified Discovery: Navier–Stokes existence and smoothness**.

The official Clay problem accepts four distinct outcomes (A)–(D). This workspace keeps those statements separate. The current positive route targets the unforced whole-space global-regularity statement (A); the blow-up-classification lane studies necessary singularity scenarios that would have to be excluded to close that route.

## Active blow-up lane

| Atom | Question | State |
|---|---|---|
| `NS-B1` | If a finite-time **Type-I** singularity exists, what exact ancient rescaled object is forced, and which additional property would place it inside a valid Liouville/rigidity theorem? | `STRICT_PRE_CANDIDATE_PACKET` |
| `NS-B2` | What remains if the singularity is Type-II rather than Type-I? | `OPEN_SIBLING_RESIDUAL` |

`NS-B1` deliberately separates:

1. exact backward self-similar profiles — fixed points of the renormalized flow;
2. discretely self-similar profiles — periodic rescaled trajectories;
3. general Type-I ancient limits — potentially nonperiodic complete trajectories;
4. Type-II concentration — outside this atom.

The first strict packet contains **no new Navier–Stokes theorem candidate**. Its next action is a source-bound implication/counterexample matrix across known Type-I and Liouville hypotheses, followed only then by selection of the smallest genuinely open bridge.

## Authority

`OPEN_NO_SOLUTION_CERTIFICATE`

Finite computation is falsification/calibration only. Same-context expert roles are not independent review. A root solution requires exact statement binding, a closed proof DAG, audited dependencies/axioms/verifier trust, isolated recheck where supported, bounded novelty search, and three genuinely isolated mathematical reviews.
