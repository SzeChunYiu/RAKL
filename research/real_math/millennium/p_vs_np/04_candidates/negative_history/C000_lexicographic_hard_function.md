# C000 — lexicographically first hard truth table

**Status:** REFUTED_AS_ROOT_ROUTE

## Proposal

For each input length, counting shows that most Boolean functions require large circuits. Define `f_n` to be the lexicographically first truth table whose circuit complexity exceeds a chosen polynomial bound. Because the definition is short, try to call the family explicit and use it to separate P from NP.

## Failure

The move confuses **short metadescription** with **efficient evaluation / NP membership**.

Counting establishes existence of hard truth tables. Selecting the lexicographically first one requires deciding that all earlier candidates fail the circuit-size threshold, or an equivalent high-complexity selection procedure. Nothing in the counting argument supplies a polynomial-time evaluator or polynomially verifiable certificates for the bits of the selected family.

Therefore the constructed family is not licensed as an NP language. The proof cannot invoke bridge B2.

## RAKL diagnosis

- valid retained fact: hard truth tables exist by counting;
- invalid promotion: existence -> explicit NP-complete hard language;
- residual: obtain hardness for a family whose evaluation/certificate complexity is independently controlled;
- route consequence: use meta-complexity to study this explicitness gap rather than hiding it.

This failed route remains permanent negative history.
