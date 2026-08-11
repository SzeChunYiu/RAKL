# Reference Verification Report

Date: 2026-08-09  
Scope: core bibliography currently used by the RAKL methods manuscript.  
Method: verify title, principal author metadata, year and stable identifier against the official publisher/proceedings page or arXiv record. For preprints, the arXiv identifier is treated as the canonical publication identity unless a separate version-of-record is explicitly verified.

## Verified entries

| Bib key | Status | Verified source | Notes |
|---|---|---|---|
| `gottweis2026coscientist` | VERIFIED | Nature DOI `10.1038/s41586-026-10644-y` | Title, Nature volume 655, pages 487-496, 2026 verified. |
| `ghareeb2026robin` | VERIFIED | Nature DOI `10.1038/s41586-026-10652-y` | Title, Nature volume 655, pages 497-505, 2026 verified. |
| `yamada2025aiscientistv2` | VERIFIED PREPRINT | arXiv:2504.08066 | Title, eight authors and 2025 submission verified. |
| `mitchener2025kosmos` | VERIFIED PREPRINT | arXiv:2511.02824 | Title, lead authors and 2025 identity verified. |
| `ghafarollahi2024sciagents` | VERIFIED PREPRINT | arXiv:2409.05556 | Title, authors Alireza Ghafarollahi and Markus J. Buehler, 2024 verified. |
| `skarlinski2024paperqa2` | VERIFIED PREPRINT | arXiv:2409.13740 | Title and nine authors verified. |
| `zhang2025dgm` | VERIFIED PREPRINT | arXiv:2505.22954 | Title and authors Jenny Zhang, Shengran Hu, Cong Lu, Robert Lange, Jeff Clune verified. |
| `alzubi2026evoskill` | VERIFIED PREPRINT | arXiv:2603.02766 | Title and five authors verified. |
| `shen2026skillfoundry` | VERIFIED PREPRINT | arXiv:2604.03964 | Title and six authors verified. |
| `gao2026evoagentbench` | VERIFIED PREPRINT | arXiv:2607.05202 | Title, year and author sequence beginning Xingze Gao, Chuanrui Hu, Hongda Chen verified. |
| `deng2026finevobench` | VERIFIED PREPRINT | arXiv:2608.06144 | Title, 2026 date and author sequence beginning Bo Deng, Kang Zhou, Lifan Guo verified. |
| `yang2026causalab` | VERIFIED PREPRINT | arXiv:2605.26029 | Title and ten-author record verified. |
| `gibson2026sheaves` | VERIFIED PREPRINT | arXiv:2605.08609 | Title and sole author Josh Gibson verified. |
| `vitali2026provenance` | VERIFIED PREPRINT | arXiv:2606.15246 | Title, Fabio Vitali and Valentina Pasqual verified. |
| `packer2023memgpt` | VERIFIED PREPRINT | arXiv:2310.08560 | Title and seven authors verified; current arXiv version revised in 2024 but original identity is 2023. |
| `sarthi2024raptor` | VERIFIED CONFERENCE | ICLR 2024 proceedings + arXiv:2401.18059 | Title, six authors and ICLR 2024 publication verified. |
| `jiang2023llmlingua` | VERIFIED CONFERENCE | ACL Anthology `2023.emnlp-main.825` | Title, five authors, EMNLP 2023, pages 13358-13376 and DOI verified. |
| `xu2023recomp` | VERIFIED PREPRINT | arXiv:2310.04408 | Title, authors Fangyuan Xu, Weijia Shi and Eunsol Choi verified. |
| `dwork2015reusable` | VERIFIED IDENTITY | Science DOI `10.1126/science.aaa9375`; arXiv:1506.02629 for expanded technical record | Title/author identity and adaptive-holdout claim are stable. Before journal submission, final reference style should be regenerated from Crossref/publisher metadata rather than hand-maintained. |

## Required pre-submission recheck

1. Re-run the bibliography through Crossref/official publisher sources shortly before submission so any version-of-record or metadata changes to 2025-2026 preprints are captured.
2. If an arXiv paper acquires a peer-reviewed version, choose one canonical citation and add an explicit version relation rather than keeping both as independent evidence.
3. Do not cite search-result summaries as bibliography authority. The final `.bib` must be generated or checked against publisher/arXiv metadata.
4. Keep the recent 2026 preprints labeled as preprints in prose where publication status matters to the novelty argument.
5. Reference verification establishes bibliographic identity only; it does not establish that a cited paper lacks an unmentioned RAKL capability.

## Current result

`CORE_BIBLIOGRAPHY = VERIFIED_FOR_PREPRINT_DRAFT`

This status is sufficient for the current arXiv methods/protocol build, subject to the explicit preprint labels above. It is **not** the final journal-submission reference audit.
