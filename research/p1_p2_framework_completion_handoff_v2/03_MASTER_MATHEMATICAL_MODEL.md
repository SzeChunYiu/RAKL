# Master Mathematical Model: Pursuit + Justification

## 1. Research state

Let:

- \(O_t\): observations/source artifacts available at time \(t\);
- \(R_t\): candidate representations;
- \(H_t\): candidate hypotheses/explanations;
- \(A_t\): admissible information-acquisition/reasoning actions;
- \(C_t\): canonical scientific claims;
- \(E_t\): evidence/provenance ledger;
- \(N_t\): immutable negative-history ledger;
- \(Auth_t\): scientific-authority state.

Define

\[
S_t=(P_t,J_t)
\]

with Pursuit state

\[
P_t=(O_t,R_t,H_t,A_t)
\]

and Justification state

\[
J_t=(C_t,E_t,N_t,Auth_t).
\]

## 2. Non-sovereignty boundary

Pursuit operators

\[
u:P\to P
\]

may change search, representation, hypotheses and proposed probes.

They may not directly alter canonical authority:

\[
\pi_{Auth}(J_{t+1})=\pi_{Auth}(J_t)
\]

unless a separately certified promotion operator

\[
\Gamma:(P,J,\mathrm{certificate})\to J'
\]

is invoked.

Thus:

\[
\text{discovery} \neq \text{authority}.
\]

## 3. Candidate representation

A representation is a tuple

\[
r=(X_r,\Sigma_r,\rho_r,Q_r,M_r)
\]

where:

- \(X_r\): state/object space;
- \(\Sigma_r\): typed relation vocabulary;
- \(\rho_r:O\to\mathcal P(X_r)\): reduction/encoding operator;
- \(Q_r\): declared query/decision class;
- \(M_r\): allowed morphism family.

No representation is canonical merely because it is generated.

## 4. Representation evaluation

For registered problem basis/distribution \(D\) and budget \(B\),

\[
V(r;D,B)=
(\mathrm{task\ loss},
\mathrm{false\ derivation},
\mathrm{refusal},
\mathrm{cost},
\mathrm{auditability},
\mathrm{robustness}).
\]

Compare these by partial/Pareto order, not by one fused scalar.

## 5. Hypotheses and explanations

A hypothesis is

\[
h=(r,\theta,\mathrm{scope},\mathrm{pred},\mathrm{assumptions}).
\]

The Pursuit state may contain mutually incompatible hypotheses simultaneously.

## 6. Evidence and authority

Each evidence root \(e\) carries

\[
e=(\mathrm{source},\mathrm{content},\mathrm{scope},
\mathrm{method},\mathrm{provenance},
\mathrm{bias\ signature},\mathrm{time}).
\]

Authority remains a product/partial order across the repository's scientific coordinates. No scalarization is introduced by this packet.

## 7. Negative epochs

A negative epoch is

\[
n=(m,p,d,y,g)
\]

where \(m\) is the mechanic, \(p\) frozen protocol, \(d\) data, \(y\) typed outcome, and \(g\) a causal attribution DAG.

It is append-only in \(N_t\).

A successor never overwrites \(n\); it creates a new version and new evidence.
