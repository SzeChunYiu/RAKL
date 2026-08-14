# Paper II nearest-work claim matrix — 2026 audit

Date: 2026-08-14. Authority: same-context analysis, not independent review.

Every record below was read off a canonical primary source (ACL Anthology,
arXiv `/abs/`, Crossref, DBLP, publisher PDF). No citation is reproduced from a
search-engine summary or from the issue body that proposed it.

Verdict key: **THREAT** = occupies the same functional niche;
**DISTINCT** = adjacent, different problem; **COSTUME** = surface resemblance only.

## A. Causal transportability — the genuine parent

| Work | Record | Verdict |
| --- | --- | --- |
| Pearl & Bareinboim, "Transportability of Causal and Statistical Relations: A Formal Approach" | AAAI 2011, 25(1):247–254, DOI `10.1609/aaai.v25i1.7861` | **THREAT** |
| Bareinboim & Pearl, "Transportability of Causal Effects: Completeness Results" | AAAI 2012, 26(1):698–704, DOI `10.1609/aaai.v26i1.8232` | **THREAT** |
| Bareinboim & Pearl, "Meta-Transportability of Causal Effects: A Formal Approach" | AISTATS 2013, PMLR 31:135–143 | **THREAT** |
| Bareinboim & Pearl, "A General Algorithm for Deciding Transportability of Experimental Results" | J. Causal Inference 1(1):107–134, 2013, DOI `10.1515/jci-2012-0004`, `arXiv:1312.7485` | **THREAT** |
| Pearl & Bareinboim, "External Validity: From Do-Calculus to Transportability Across Populations" | Statistical Science 29(4):579–595, 2014, DOI `10.1214/14-STS486` | **THREAT** |
| Bareinboim & Pearl, "Causal inference and the data-fusion problem" | PNAS 113(27):7345–7352, 2016, DOI `10.1073/pnas.1510507113` | **THREAT** |
| Jalaldoust, Bellot & Bareinboim, "Partial Transportability for Domain Generalization" | NeurIPS 37:137768–137805, 2024, `arXiv:2503.23605` | DISTINCT — bounding/estimation, not a decision procedure |
| Jalaldoust & Bareinboim, "Adapting, Fast and Slow: On Few-Shot Transportability of Compositions" | `arXiv:2512.22777` | DISTINCT — generalization guarantees, not a licence gate |
| Mishra, "Local verification cannot detect non-transportability…" | `arXiv:2608.11252` | COSTUME — unrefereed single-author preprint; cochain exactness with an FX application |

The `sID` signature (AAAI 2012, p. 702) is the load-bearing overlap:

```
function S ID(y, x, P*, I, D)
INPUT:  x, y value assignments, P* observational distribution
        in Π*, I set of interventional distributions in Π, D a
        selection diagram, S set of selection nodes.
OUTPUT: Expression for Px*(y) in terms of P*, I or FAIL(F, F').
```

with Theorem 6 (soundness), Theorem 7 and Corollary 3 (completeness).

## B. Structure-mapping — owns the role/relation conjunct

| Work | Record | Verdict |
| --- | --- | --- |
| Gentner, "Structure-Mapping: A Theoretical Framework for Analogy" | Cognitive Science 7(2):155–170, 1983, DOI `10.1207/s15516709cog0702_3` | DISTINCT — graded match, no licence |
| Falkenhainer, Forbus & Gentner, "The structure-mapping engine: Algorithm and examples" | Artificial Intelligence 41(1):1–63, 1989, DOI `10.1016/0004-3702(89)90077-5` | DISTINCT — produces ranked candidate mappings |
| Forbus, Gentner & Law, "MAC/FAC: A Model of Similarity-Based Retrieval" | Cognitive Science 19(2):141–205, 1995, DOI `10.1207/s15516709cog1902_1` | DISTINCT — two-stage retrieval filter |

## C. Case-based reasoning

| Work | Record | Verdict |
| --- | --- | --- |
| Aamodt & Plaza, "Case-Based Reasoning: Foundational Issues, Methodological Variations, and System Approaches" | AI Communications 7(1):39–59, 1994, DOI `10.3233/AIC-1994-7104` | DISTINCT — 4R survey, no gating verdict |
| Leake, Kinley & Wilson, "Case-Based Similarity Assessment: Estimating Adaptability from Experience" | AAAI-97, pp. 674–679 | DISTINCT — closest CBR item; real-valued adaptability estimate, no abstention |
| Smyth & Keane, "Remembering To Forget: A Competence-Preserving Case Deletion Policy…" | IJCAI-95, Vol. 1, pp. 377–382 | DISTINCT — **case-base maintenance, not applicability gating.** Must not be cited as "when is a case reusable" |

## D. Selective prediction / deferral / conformal — owns the abstain channel

| Work | Record | Verdict |
| --- | --- | --- |
| Cortes, DeSalvo & Mohri, "Learning with Rejection" | ALT 2016, LNCS pp. 67–82, DOI `10.1007/978-3-319-46379-7_5` | DISTINCT — scalar risk threshold |
| Geifman & El-Yaniv, "Selective Classification for Deep Neural Networks" | NIPS 2017, pp. 4878–4887 | DISTINCT — risk/coverage tradeoff |
| Madras, Pitassi & Zemel, "Predict Responsibly: Improving Fairness and Accuracy by Learning to Defer" | NeurIPS 2018, pp. 6150–6160, `arXiv:1711.06664` | DISTINCT — learned deferral policy |
| Wang & Qiao, "Conformal Prediction Under Generalized Covariate Shift with Posterior Drift" | `arXiv:2502.17744`, AISTATS 2025 | DISTINCT — closest; abstention mounted on transfer, but threshold-triggered, not structure-triggered |

## E. Analogy / transfer benchmarks named in #487 — all verified, none a threat

| Work | Record | Verdict |
| --- | --- | --- |
| Stevenson, Pafford, van der Maas & Mitchell, "Can Large Language Models Generalize Analogy Solving Like Children Can?" | TACL 14:612–626, 2026, ACL `2026.tacl-1.28`, DOI `10.1162/tacl.a.614`, `arXiv:2411.02348` | DISTINCT — accuracy under domain shift, no per-transfer verdict |
| Li et al., "ReTRE: Benchmarking LLM Transfer Robustness with Structure-Preserving Variants" | ACL 2026 Long, pp. 44257–44268, ACL `2026.acl-long.2048`, DOI `10.18653/v1/2026.acl-long.2048` | DISTINCT — structure-preservation is a construction property, not a runtime check |
| Petersen, Stevenson & van der Plas, "Modelling Analogies and Analogical Reasoning: Connecting Cognitive Science Theory and NLP Research" | TACL 14:711–732, 2026, ACL `2026.tacl-1.32`, DOI `10.1162/tacl.a.632`, `arXiv:2509.09381` | DISTINCT — survey; framing prior art |
| Chen, Chen, Sun & Zhang, "Analogical Deep Research: Retrieving and Integrating Historical Analogies for Foresight Analysis" | `arXiv:2607.13602` | DISTINCT — closest of this set; generates and scores analogies, no bound QoI or reject verdict |
| Liu et al., "Reason Analogically via Cross-domain Prior Knowledge: An Empirical Study…" | `arXiv:2604.05396` | DISTINCT — describes when transfer works, does not license it |
| Das & Balke, "From Prototypical to Relational: How LLMs Navigate Complex Analogies" | INLG 2025, pp. 465–485, ACL `2025.inlg-main.28` | DISTINCT — this *is* the analogy-similarity evaluation the claim contrasts against |
| Sourati, Ilievski, Sommerauer & Jiang, "ARN: Analogical Reasoning on Narratives" | TACL 12:1063–1086, **2024** (not 2026), ACL `2024.tacl-1.59`, DOI `10.1162/tacl_a_00688` | DISTINCT — binary validity, no abstention |
| Peltonen, Rønberg, Plesner & Wattenhofer, "GraphARC: A Comprehensive Benchmark for Graph-Based Abstract Reasoning" | `arXiv:2605.31031` | COSTUME — shares only "abstraction" vocabulary |
| Kirichenko, Ibrahim, Chaudhuri & Bell, "AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions" | `arXiv:2506.09038` | DISTINCT — abstention on *answerability*, not on a *transfer* |

## F. Contemporary reusable-experience governance

| Work | Record | Verdict |
| --- | --- | --- |
| El Hattami, Chapados & Pal, "SKILL.nb: Selective Formalization and Gated Execution for Durable Agent Workflows" | `arXiv:2606.08049` | DISTINCT — **nearest live contemporary; requires an explicit distinguishing paragraph** |
| Hu, Long & Wang, "When Continual Learning Moves to Memory: A Study of Experience Reuse in LLM Agents" | `arXiv:2604.27003` | DISTINCT — documents negative transfer, does not gate it |
| Ravindran, "Portable Agent Memory: A Protocol for Cryptographically-Verified Memory Transfer…" | `arXiv:2605.11032` | COSTUME — Merkle-DAG integrity, not epistemic licensing |

## G. CANNOT_CHECK

Two targeted searches returned no primary record. Recorded as genuine negative
results, not as absence of threat.

1. **A CBR mechanism returning an explicit three-way reusable / not-reusable /
   cannot-determine verdict.** Queries: `case-based reasoning adaptation
   knowledge "applicability conditions" reuse gating Leake Wilke Bergmann
   survey`; `Leake Kinley Wilson "adaptation-guided retrieval" case-based
   reasoning adaptability assessment 1996`; `Smyth Keane "Remembering to Forget"
   competence-preserving case deletion IJCAI 1995`.

2. **A benchmark scoring a three-way accept / reject / abstain decision on a
   TRANSFER** (rather than on answerability). Queries: `benchmark three-way
   decision accept reject abstain knowledge transfer LLM 2026 "cannot
   determine"`; `benchmark evaluating whether analogy transfer is valid
   "reject" invalid analogies abstain insufficient information 2026 ACL`;
   `"domain adaptation" OR "transfer learning" benchmark "abstain" three-way
   "transfer or not" decision negative transfer detection gate`; `2026 benchmark
   "transfer" decision "license" OR "licence" abstain three-way reuse research
   experience contract LLM`.

Item 2 is the cleanest open lane for the paper.
