# Final recursive closure decision

## 1. The framework asked the right meta-question

Persistent negatives were reclassified before another executor was optimized. The audit distinguishes at least five causes:

\[
\mathcal C=\{H,A,M/E,C,Q\},
\]

where:

- \(H\): hypothesis/mechanic family is genuinely inadequate;
- \(A\): representation or acquisition is inadequate;
- \(M/E\): measurement or evaluator contract is inadequate;
- \(C\): required executor/capability/resource is unavailable;
- \(Q\): the active scientific question is malformed, over-demanding, or conflates information regimes.

A persistent negative is not allowed to collapse automatically into \(H\). RFA-v1 already supplies bidirectional recursion and ancestor ascent. The remaining delta is to make the information assumptions of \(Q\) explicit enough that the evaluator can be audited against them.

## 2. No protected-core reopen

The new object is pursuit state, not authority state. It can be represented using the already-closed reflective calculus:

- local pursuit state for the current observation contract;
- append-only audit receipts and negative history;
- existing evaluator-protected services when evaluator policy itself changes;
- existing capability effects when external knowledge/model execution is requested.

Therefore no new privileged effect, authority semantic, certificate class, or protected service is required.

Formally, let \(\Omega\) be an ObservationContract and let \(q\) be a question proposal. The audit transformation

\[
A_{\Omega}:(P,\Omega,q)\mapsto(P',\Omega',q',r)
\]

is an ordinary pursuit mechanic. For the authority projection \(\alpha\),

\[
\alpha(A_{\Omega}(S))=\alpha(S)
\]

unless a separately certified protected operation is invoked. Changing the question is not evidence that the new question is true, and changing an evaluator policy is not permitted through this ordinary path.

## 3. What actually changes

The framework gains one plugin-level contract and one reusable obstruction:

### Observation / Information Contract

A frozen contract records:

- allowed input sources;
- acquisition regime;
- allowed semantic normalizers;
- external-knowledge policy;
- provenance requirement;
- abstention policy;
- evaluator/gold policy and evaluator epoch.

### Input-observability obstruction

For a registered license predicate \(Lic_{\Omega}(g)\), an extractor constrained to emit only licensed targets obeys

\[
E_{\Omega}(B)\subseteq\{g:Lic_{\Omega}(g)=1\}.
\]

Hence, for gold set \(G\),

\[
Recall_G(E_{\Omega})\le \frac{|G_{\Omega}|}{|G|},
\qquad
G_{\Omega}=\{g\in G:Lic_{\Omega}(g)=1\}.
\]

This is a contract-relative bound, not a theorem that semantic inference or world knowledge cannot recover the remaining targets.

## 4. Closure meaning

The specification question is closed at v1: persistent failures now have an explicit route for auditing whether the object-level question/evaluator assumes inaccessible information. The empirical programme is not scientifically closed. Fresh comparative utility of RFA-v1 and execution of stronger semantic acquisition parents remain open assurance gates.
