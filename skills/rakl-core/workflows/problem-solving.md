# Workflow — Problem Solving

Use for a new scientific, mathematical, engineering, or modelling problem.

## Procedure

1. Define the object and downstream QoI/decision.
2. Compile a problem signature: objects, relations, quantifiers, symmetries, domain, goal type and constraints.
3. Draw the current solution chain as atomic transformations and register every unresolved step as an explicit obstruction.
4. Open a knowledge fiber for every unresolved step.
5. For each step, enumerate alternative representations, mechanisms, assumptions, observations, scales, inference methods and falsifiers.
6. Search alternative vocabularies before assuming the known taxonomy or operator basis is complete.
7. Collapse exact/equivalent representations and remove incompatible combinations.
8. Retrieve typed research operators whose preconditions match the current state and whose declared targets intersect active obstructions.
9. Construct candidate operator paths rather than assuming a fixed solution path is already stored. Rank paths by explicit cost, verification debt, boundary risk and obstruction relief.
10. Treat operator composition as partial and generally non-commutative. A later move is admissible only when previous moves establish its required facts/conditions.
11. Identify what observations or proof obligations cannot distinguish among surviving paths.
12. Choose discriminators, falsifiers or verifiers for the remaining ambiguity.
13. Validate on controlled worlds before native evidence and preserve failed paths as negative history.
14. Use residuals to recurse. Repeated residuals that no registered operator can relieve open an operator-invention/Self-RAKL fiber.
15. Synthesize a global object portrait and, only if required, derive a new formalism that contains surviving prior descriptions as projections/special cases.

The executable planning layer is `src/rakl/problem_solving_algebra.py`. Its path outputs are planning objects only: they cannot set a terminal scientific or mathematical result. Terminal closure requires a separate verified certificate with explicit scope and artifact identity.

## Mathematical-research handoff

If any target is a conjecture, theorem, proof, formalization, or claim of new mathematics, compose this workflow with `mathematical-research.md` before granting mathematical authority. In particular, generated derivations, numerical examples, CAS output, or absence of a counterexample remain proposals/evidence until the mathematical assurance gates classify them. `src/rakl/math_research_runtime.py` compiles those assurance gaps into explicit blockers and candidate operator paths.

## Required question at every step

> What aspect of the object does this step preserve, and what does it throw away?

Also ask:

> Which explicit obstruction is this operator intended to relieve, what new obligation does it introduce, and under what conditions is the next operator actually composable?

For mathematical proof edges also ask:

> What exact proposition is claimed, what assumptions does it depend on, and what independent checker or refuter can attack it?

## Failure rule

If all models fail, do not immediately broaden model complexity. Reopen source, observation, target, identifiability, decomposition, representation, operator-basis and scale fibers first. For mathematical research, resource exhaustion or failed proof search is nonterminal and is never evidence that the conjecture is false.
