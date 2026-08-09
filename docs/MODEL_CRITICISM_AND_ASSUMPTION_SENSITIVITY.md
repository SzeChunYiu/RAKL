# Model Criticism and Assumption Sensitivity

Status: child operators owned by the existing RAKL method surfaces. These mechanics do **not** create additional high-level method surfaces.

## 1. Why both operators are needed

A candidate scientific model can fail in at least two materially different ways.

1. **Generative/predictive inadequacy:** the model cannot reproduce a registered observable property of the data.
2. **Assumption sensitivity:** the headline conclusion depends materially on a plausible registered modelling assumption even when ordinary predictive/discrepancy checks look acceptable.

These are not interchangeable. A model can fit the observed residual battery but be fragile to missingness, clock, nuisance, dependence or transport assumptions. Conversely, a model can be robust to a stated assumption envelope and still fail to reproduce tails, memory or other registered observables.

RAKL therefore treats the two checks as sibling child operators under existing `benchmarking`, `gap_discovery`, `experiment_query_selection`, `synthesis`, and `authority_promotion` surfaces.

---

## 2. Frozen model criticism

For a predeclared scientific discrepancy statistic

\[
s_k=T_k(y_{obs}),
\]

and predictive/generative samples from the exact evaluated model and population

\[
s_k^{(b)}=T_k(y_{pred}^{(b)}),\qquad b=1,\ldots,B,
\]

RAKL computes a finite-sample empirical two-sided predictive tail probability

\[
p_k=2\min\left\{
\frac{1+\sum_b \mathbf 1[s_k^{(b)}\le s_k]}{B+1},
\frac{1+\sum_b \mathbf 1[s_k^{(b)}\ge s_k]}{B+1}
\right\},
\]

capped at one.

A probe is called materially failed only when both:

1. its predeclared discrepancy magnitude exceeds the registered material tolerance; and
2. its predictive tail is small enough under the frozen single/multiple-probe policy.

The implementation currently supports a single-probe policy or a frozen Bonferroni family for known-answer support. More elaborate sequential/multiplicity procedures remain separate methodological choices and must be preregistered before result access.

### 2.1 Resolution limit

The add-one empirical tail has finite resolution. For a two-sided level \(\alpha\), the predictive sample count must be large enough that the smallest attainable tail probability can resolve the declared threshold. If not, RAKL returns `CANNOT_CHECK` rather than reporting an impossible tail test as negative evidence.

### 2.2 Output semantics

```text
ADEQUATE_ON_FROZEN_PROBES_PROPOSAL_ONLY
STRUCTURED_RESIDUAL_DETECTED
PARTIALLY_IDENTIFIED
CANNOT_CHECK
TRIAL_INVALID
```

Passing the frozen probes means only:

> no registered material discrepancy was detected for this model, population, context, probe family and resolution.

It does **not** mean the model is true, globally complete, or mechanistically identified.

A failed probe is evidence against scoped model adequacy. It is not automatically evidence for one replacement mechanism. A predeclared residual mapping can route the failure to a scientific coordinate such as `tail`, `memory`, or `cross_asset_state`; a post-hoc explanation remains proposal-only.

---

## 3. Frozen assumption sensitivity

Let \(\theta_0\) be the baseline estimand under registered assumption state \(a_0\). Let

\[
\{(a_j,\theta_j)\}_{j=1}^J
\]

be a frozen envelope of scientifically justified perturbation scenarios under the **same population, context and QoI**.

For materiality threshold \(\delta\), define the conclusion class

\[
C(\theta;\delta)=
\begin{cases}
POSITIVE, & \theta>\delta,\\
NEGATIVE, & \theta<-\delta,\\
INDETERMINATE, & |\theta|\le\delta.
\end{cases}
\]

The baseline conclusion is robust within the registered envelope only when every evaluable registered scenario preserves the baseline conclusion class.

If at least one predeclared scenario changes the material conclusion class, the result is

```text
ASSUMPTION_SENSITIVE
```

This includes both a sign reversal and a shrinkage from a material positive/negative effect into the indeterminate materiality band.

### 3.1 Scope compatibility

A scenario that changes the population, target QoI, or another context coordinate is not silently treated as a sensitivity analysis of the same scientific claim. It is a new contextual chart and returns `CANNOT_COMPARE` under the generic operator.

### 3.2 Missing scenarios

If a registered scenario cannot be evaluated, the robustness claim is only partially identified. The unavailable scenario remains visible rather than being deleted to create a favorable sensitivity table.

### 3.3 Output semantics

```text
ROBUST_WITHIN_REGISTERED_ENVELOPE_PROPOSAL_ONLY
ASSUMPTION_SENSITIVE
PARTIALLY_IDENTIFIED
CANNOT_COMPARE
CANNOT_CHECK
TRIAL_INVALID
```

Robustness does not prove an assumption is correct. It states only that the conclusion is stable over the declared perturbation envelope.

---

## 4. Combined scientific loop

The two child operators create a more complete quantitative-model loop:

```text
candidate model
   |
   +-- frozen generative/predictive discrepancy battery
   |       |
   |       +-- failure -> structured residual -> next model requirement
   |
   +-- frozen assumption envelope
           |
           +-- sensitivity -> qualified conclusion / new discriminator
```

A model is not called descriptively closed merely because one branch passes. For the registered scope, the relevant residual battery must be adequate **and** the headline conclusions must have an honest robustness/partial-identification status under the registered assumption family.

For the future crypto spot application this is directly relevant to, among other things:

- clock/availability semantics;
- missing-data and source filtering assumptions;
- dependence/cluster definitions;
- nuisance/fixed-effect treatment;
- stationarity/regime boundaries;
- transport population definitions;
- microstructure feature construction;
- predictive target definitions.

These assumptions are not all fixed in advance by the generic RAKL framework. The project must register the domain-specific envelope before confirmation outcomes are used to establish robustness.

---

## 5. Authority boundary

Neither operator can grant mechanism authority, assumption truth, global scientific completeness, independent review credit, or method-promotion authority.

Model criticism answers whether a candidate reproduces registered observations. Assumption sensitivity answers whether a registered conclusion survives a specified perturbation family. Stronger scientific claims require the corresponding evidence layers defined elsewhere in RAKL.
