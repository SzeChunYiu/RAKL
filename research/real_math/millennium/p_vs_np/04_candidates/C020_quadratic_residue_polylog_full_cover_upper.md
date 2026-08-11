# C020 — quadratic-residue graphs have a polylogarithmic full-cover upper bound

**Status:** `PROOF_DRAFT / FULL_COVER_UPPER_BOUND / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`

C020 attacks the upper-bound-first branch of C019-R1. It does not prove a lower bound and does not solve P versus NP. Its purpose is adversarial. Before treating the Paley/quadratic-residue family as a possible high-cover object, bound how cheaply the relation can already be constructed from row and column stars.

## Statement

Let `p` be any odd prime, let `n = ceil(log2 p)`, and define the square bipartite graph

`QR_p = {(x,y) in Z_p x Z_p : y-x is a nonzero quadratic residue mod p}`.

Then, for a universal constant `K`,

`D_intersection(QR_p | G_{p,p}) <= K n^3`,

and therefore

`rho(QR_p, G_{p,p}) <= K n^3 = O((log p)^3)`.

The same upper bound applies in particular to the C019 subfamily `p == 3 (mod 8)`.

No attempt is made here to optimize `K` or the exponent 3.

## Source-bound bridge

Cavalar and Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 / ACM TOCT 17(2), Article 13 (2025), DOI `10.1145/3718746`, define graph intersection complexity using row and column stars and prove the fusion inequality

`rho(A,B) <= D_intersection(A | B)`.

Their graph model also notes that replacing individual stars by arbitrary unions of rows or arbitrary unions of columns does not change intersection complexity. Unions are free for this measure because only intersections are counted.

C020 uses only that source-level model and elementary modular arithmetic.

## Lemma C020-L1 — bit predicates are free in graph intersection complexity

Label rows and columns by integers in `{0,...,p-1}` using `n` binary bits. For each bit position `i` and value `b in {0,1}`, define

`X_i^b = union of all rows whose row label has bit i equal to b`,

`Y_i^b = union of all columns whose column label has bit i equal to b`.

Each such set is a union of graph generators and therefore has intersection cost zero.

Consequently any Boolean construction on the valid row/column labels can be interpreted as a set construction on `[p] x [p]` once both polarities of every input bit are available.

## Lemma C020-L2 — dual-rail Boolean circuits transfer gate count to intersection count

Take an ordinary fan-in-two Boolean circuit over AND, OR, and NOT, with both polarities of each input literal available. Maintain for every wire `z` two set-valued rails representing `z` and `not z`.

- If `z = a AND b`, compute the positive rail with one intersection and the negative rail as `not a OR not b`, using a union.
- If `z = a OR b`, compute the positive rail with a union and the negative rail as `not a AND not b`, using one intersection.
- If `z = NOT a`, swap the two rails.

Thus a circuit with `s` binary AND/OR gates yields a graph set construction with at most `s` intersections. Internal negations create no hidden complement operation in the graph model.

## Lemma C020-L3 — modular addition has linear Boolean size

For `n`-bit residues modulo fixed `p`, addition modulo `p` has a fan-in-two Boolean circuit of size `O(n)`.

Use a ripple-carry adder to compute an `(n+1)`-bit sum. Compare the sum with the fixed constant `p`, conditionally subtract `p`, and select the reduced result. Ripple carry, comparison with a fixed constant, constant subtraction, and bitwise selection each use `O(n)` Boolean gates.

The same bound holds for subtraction modulo `p` and for doubling modulo `p`.

## Lemma C020-L4 — modular multiplication has quadratic Boolean size

For two residues `a,b < p`, compute `a*b mod p` by scanning the `n` bits of `b` and maintaining a residue `r`.

At each step:

1. replace `r` by `2r mod p`;
2. conditionally replace it by `r+a mod p` according to the next multiplier bit.

Each step uses `O(n)` gates by C020-L3 plus an `O(n)` multiplexer. There are `n` steps. Hence modular multiplication has size `O(n^2)`.

This construction avoids any appeal to a nonuniform division theorem or a fast multiplication algorithm.

## Lemma C020-L5 — fixed-exponent modular powering has cubic Boolean size

For a fixed exponent `e < p`, binary square-and-multiply uses at most `2n` modular multiplications. By C020-L4 it therefore has Boolean size `O(n^3)`.

The exponent needed below is the fixed constant

`e = (p-1)/2`

for each member of the graph family.

## Proof of C020

Given row label `x` and column label `y`, first compute

`d = y-x mod p`.

Then compute

`z = d^((p-1)/2) mod p`.

Euler's criterion says that for nonzero `d`,

`z = 1` exactly when `d` is a quadratic residue modulo `p`, while `d=0` gives `z=0` because the exponent is positive. Therefore the predicate

`z == 1`

is exactly the adjacency predicate of `QR_p`.

The subtraction costs `O(n)` gates, modular powering costs `O(n^3)`, and comparison with 1 costs `O(n)`. Thus an ordinary Boolean circuit of size `O(n^3)` computes the relation on the valid row and column labels.

By C020-L1 and C020-L2 this circuit induces a graph construction from row/column stars using `O(n^3)` intersections. Therefore

`D_intersection(QR_p | G_{p,p}) = O(n^3)`.

The fusion inequality then gives

`rho(QR_p,G_{p,p}) = O(n^3)`.

## What this changes

C019 established that the `p == 3 mod 8` family survives several cheap logarithmic-ceiling screens. C020 shows that the same family nevertheless has a direct **polylogarithmic full-cover ceiling**. Hence rank `p`, dense degree, dense arboricity, and absence of repeated rows do not imply anything close to linear cover complexity for this algebraic family.

C020 does **not** refute the possibility that

`rho(QR_p) = omega(log p)`.

The remaining window is between the existing logarithmic lower-bound scale of interest and this cubic-log upper envelope. The next discriminator should therefore be sharper, not broader.

## Next residual C020-R1

Attempt one of the following in order.

1. Compile a genuinely `O(log p)` or `O(log^2 p)` intersection/cyclic construction using quadratic-character or Euclidean/Jacobi structure. An `O(log p)` construction would refute C019 as a super-log target.
2. If no such construction survives, formulate a character-sensitive lower-bound invariant that can distinguish `Omega(log^(1+epsilon) p)` from the cubic-log upper envelope and is stable under arbitrary pair reuse.
3. Search for a different explicit high-rank family whose membership circuit is not already known by an elementary polylogarithmic arithmetic construction.

## Five-role same-context disposition

- **Complexity theory — ACCEPT AS UPPER-BOUND PROOF DRAFT.** The construction is explicit and attacks the correct full-cover object, but it is an upper bound only.
- **Meta-complexity — ACCEPT WITH ROOT SCOPE ZERO.** This does not alter MCSP magnification and has no direct P-versus-NP implication.
- **Adversarial proof review — REVISE BEFORE THEOREM AUTHORITY.** The gate-to-intersection simulation and valid-label/non-power-of-two boundary must remain explicit. A hidden free complement operation would invalidate the argument; dual rail is included precisely to avoid it.
- **Formal methods — REVISE.** No theorem-prover artifact, formalization witness, proof receipt, dependency audit, or isolated kernel recheck exists.
- **Novelty/research value — NO_NOVELTY_CLAIM.** The ingredients are classical. The value is route pruning and a quantitative upper envelope, not a claim of new mathematics.

This is same-context review and is **not independent review**.

## Root authority

`P != NP` remains `OPEN_NO_SOLUTION_CERTIFICATE`.