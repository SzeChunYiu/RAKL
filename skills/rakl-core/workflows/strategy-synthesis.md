# Workflow — Strategy / Decision Synthesis

Use when surviving knowledge must be converted into actions, policies, economic strategies, or other decisions.

## Principle

A good model does not automatically imply a good decision.

The decision layer is its own RAKL object.

## Decision lattice

Expand compatible combinations of:

```text
mechanism trigger
state/context filter
object/contract selector
action path
execution method
exit/stopping rule
hedge
sizing
capacity constraint
risk/solvency constraint
```

Prune impossible combinations before testing.

## Mandatory ancestry

Every decision candidate should trace:

```text
source evidence
→ object facets
→ mechanism/model set
→ downstream QoI
→ action mapping
→ execution/implementation
→ value/utility
→ capacity/risk
```

A black-box predictive candidate may remain exploratory, but mechanistic authority requires the full ancestry.

## Economics / utility

Evaluate the true decision denominator.

For trading this means requests/opportunities, not successful fills only.

For other domains this means the analogous pre-outcome decision unit.

Report uncertainty and opportunity cost, not just conditional success.

## Null branches

If the primary predictive strategy is null, recursively fan surviving mechanisms into other consumers.

For example, a volatility mechanism with no directional alpha may still support:

```text
risk forecasting
position sizing
market making / quote width
toxicity filters
relative value
timing or abstention
```

Do not discard a mechanism merely because one consumer fails.

## Promotion

A decision becomes usable only when its required upstream authority and decision-specific evidence are sufficient for that scope.
