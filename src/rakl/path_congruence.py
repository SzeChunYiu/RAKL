"""Algebraic laws for path quotienting: Mazurkiewicz trace congruence.

Closes a formal gap found in hostile mathematical review: ``path_equivalence``
supplies commuting-pair *witnesses* and a canonical partial-order trace, but not the
algebraic laws that make quotienting *safe*. For substitution inside larger proofs
to be sound, "same trace" must be

  (E)  an equivalence relation on ALL histories over the alphabet (the previous
       predicate was not even reflexive on histories that violated the declared
       dependencies -- a domain defect detected empirically), and
  (C)  a CONGRUENCE under path composition:  u ~ v  implies  p·u·q ~ p·v·q,
       so an equivalent subpath may be substituted inside any context without
       changing the meaning of the whole.

The weakest standard structure with both properties is the free partially
commutative monoid (Mazurkiewicz traces, concurrency theory): fix an alphabet A and
a symmetric, irreflexive *independence* relation I ⊆ A×A (here: verified commuting
pairs, witnessed by ``PathEquivalenceWitness``); trace equivalence is the reflexive-
transitive closure of swapping adjacent independent letters. That relation is a
congruence by construction. We deliberately do NOT import higher category theory:
the trace monoid is the minimal parent that closes the gap.

Foata normal form gives a canonical representative, so equality of normal forms
decides equivalence in O(n·|A|) rather than by permutation search.

Nothing here grants proof or scientific authority; a trace-equivalence class is a
bookkeeping object. Collapsing classes for *verified meaning* still requires the
per-pair verifier witnesses demanded by ``path_equivalence``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable, Sequence, Tuple

Pair = Tuple[str, str]


def _normalize_independence(pairs: Iterable[Pair]) -> FrozenSet[Pair]:
    """Symmetric, irreflexive closure of the declared independent (commuting) pairs."""
    out = set()
    for a, b in pairs:
        if a == b:
            raise ValueError(f"independence must be irreflexive: ({a},{b})")
        out.add((a, b))
        out.add((b, a))
    return frozenset(out)


@dataclass(frozen=True)
class TraceMonoid:
    """Free partially commutative monoid over ``alphabet`` with independence ``independent``."""

    alphabet: FrozenSet[str]
    independent: FrozenSet[Pair]

    @staticmethod
    def build(alphabet: Iterable[str], commuting_pairs: Iterable[Pair]) -> "TraceMonoid":
        alpha = frozenset(alphabet)
        indep = _normalize_independence(commuting_pairs)
        for a, b in indep:
            if a not in alpha or b not in alpha:
                raise ValueError(f"independence pair ({a},{b}) outside alphabet")
        return TraceMonoid(alpha, indep)

    def _check_word(self, word: Sequence[str]) -> Tuple[str, ...]:
        w = tuple(word)
        for x in w:
            if x not in self.alphabet:
                raise ValueError(f"letter {x!r} outside alphabet")
        return w

    def foata_normal_form(self, word: Sequence[str]) -> Tuple[Tuple[str, ...], ...]:
        """Canonical representative: maximal steps of pairwise-independent letters.

        Greedy left-to-right: each letter is placed in the earliest step after the
        last step containing a dependent letter; steps are sorted internally. Two
        words have the same Foata normal form iff they are trace-equivalent.
        """
        w = self._check_word(word)
        steps: list[list[str]] = []
        depth: dict[int, int] = {}  # index into steps for fast scan
        for x in w:
            # earliest step strictly after any step holding a letter dependent with x
            place = 0
            for i in range(len(steps) - 1, -1, -1):
                if any((x, y) not in self.independent and x != y or x == y for y in steps[i]):
                    place = i + 1
                    break
            if place == len(steps):
                steps.append([x])
            else:
                # letter must also be independent of everything in the target step
                while place < len(steps) and any(
                    x == y or (x, y) not in self.independent for y in steps[place]
                ):
                    place += 1
                if place == len(steps):
                    steps.append([x])
                else:
                    steps[place].append(x)
        return tuple(tuple(sorted(s)) for s in steps)

    def equivalent(self, left: Sequence[str], right: Sequence[str]) -> bool:
        """Trace equivalence: total on A* (defined for EVERY pair of words)."""
        return self.foata_normal_form(left) == self.foata_normal_form(right)

    def compose(self, *words: Sequence[str]) -> Tuple[str, ...]:
        out: list[str] = []
        for w in words:
            out.extend(self._check_word(w))
        return tuple(out)

    # ------------------------------------------------------------------ #
    # Law checks (executable; used by property tests and by callers that
    # want a machine-checked certificate before collapsing classes).
    # ------------------------------------------------------------------ #

    def check_equivalence_laws(self, words: Sequence[Sequence[str]]) -> dict:
        """Verify (E): reflexive, symmetric, transitive on the given sample."""
        refl = all(self.equivalent(w, w) for w in words)
        sym = all(self.equivalent(u, v) == self.equivalent(v, u) for u in words for v in words)
        trans = True
        for u in words:
            for v in words:
                if not self.equivalent(u, v):
                    continue
                for z in words:
                    if self.equivalent(v, z) and not self.equivalent(u, z):
                        trans = False
        return {"reflexive": refl, "symmetric": sym, "transitive": trans}

    def check_congruence(self, u: Sequence[str], v: Sequence[str], contexts: Sequence[Tuple[Sequence[str], Sequence[str]]]) -> bool:
        """Verify (C): u ~ v implies p·u·q ~ p·v·q for every supplied context (p, q)."""
        if not self.equivalent(u, v):
            return True  # vacuously
        return all(
            self.equivalent(self.compose(p, u, q), self.compose(p, v, q))
            for p, q in contexts
        )


def congruence_certificate(
    alphabet: Iterable[str],
    commuting_pairs: Iterable[Pair],
    sample_words: Sequence[Sequence[str]],
    sample_contexts: Sequence[Tuple[Sequence[str], Sequence[str]]],
) -> dict:
    """Machine-checked certificate that the declared quotient obeys (E) and (C).

    This is what ``path_equivalence`` consumers should demand before substituting
    equivalence classes inside larger structures. It grants no proof authority; it
    certifies only the algebra of the bookkeeping relation.
    """
    monoid = TraceMonoid.build(alphabet, commuting_pairs)
    laws = monoid.check_equivalence_laws(sample_words)
    cong = all(
        monoid.check_congruence(u, v, sample_contexts)
        for u in sample_words
        for v in sample_words
    )
    return {
        "structure": "free_partially_commutative_monoid",
        "equivalence_laws": laws,
        "congruence_under_composition": cong,
        "total_on_domain": True,  # foata_normal_form is defined for every word over A
        "grants_proof_authority": False,
    }
