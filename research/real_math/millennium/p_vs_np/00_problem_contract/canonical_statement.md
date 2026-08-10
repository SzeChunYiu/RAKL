# Canonical problem contract

## Root statement

Let `P` be the class of languages decidable by a deterministic Turing machine in polynomial time. Let `NP` be the class of languages decidable by a nondeterministic Turing machine in polynomial time, equivalently languages with polynomial-length certificates verifiable in deterministic polynomial time.

The root question is whether

`P = NP`.

The active positive goal of this lane is the exact claim

`P != NP`.

No neighboring separation is silently treated as equivalent.

## Registered sufficient bridge B1

`SAT notin P/poly  =>  P != NP`.

Reason. If `P = NP`, then `SAT in P`. Every polynomial-time language has polynomial-size circuit families, so `SAT in P/poly`. The contrapositive gives B1.

**Important:** B1 is a sufficient route, not an asserted equivalence. Proving `P != NP` does not by itself establish the stronger nonuniform lower bound `SAT notin P/poly`.

## Registered sufficient bridge B2

Any explicit NP-complete language `L` with superpolynomial Boolean circuit complexity implies `P != NP`, provided the reduction and circuit model are fixed and the lower bound applies to the corresponding language family.

## Registered stronger bridge B3

A superpolynomial general-circuit lower bound for a canonical CLIQUE/SAT Boolean-function family, with an audited polynomial-time reduction to the root language model, is sufficient for B1/B2 as appropriate.

## Failure conditions

A candidate does **not** solve the root if it proves only:

- a lower bound for monotone circuits, AC0, ACC, formulas, branching programs, or another restricted model without a valid lifting theorem to general polynomial-time computation;
- existence of hard Boolean functions by counting without placing an explicit hard language in NP;
- a nonuniform or uniform separation in the wrong direction;
- a relativized world statement;
- computational evidence on finitely many input lengths;
- a theorem whose formal statement is weaker than the claimed root.
