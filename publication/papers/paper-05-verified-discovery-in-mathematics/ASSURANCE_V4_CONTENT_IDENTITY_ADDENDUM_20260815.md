# Paper V — assurance v4 content-identity boundary (2026-08-15)

This is the final local identity-hardening addendum for the current research branch. It supersedes any implication that a field merely named `*_hash` is sufficient evidence identity.

`src/rakl/math_research_assurance_v4.py` narrows the v3 transitive receipt chain by requiring load-bearing actor/procedure/artifact identities to be lowercase SHA-256 content digests:

- current proposer identity;
- formalization informal/formal statement identities;
- proof statement and proof-source identities;
- theorem novelty fingerprint and literature-manifest identity;
- formalization/novelty/value review subject, procedure, reviewer and proposer identities;
- novelty dossier digest;
- verifier proof source, checker identity digest, verifier manifest, attestation procedure, attestor identity and proposer identity.

Human display labels such as `alice`, `reviewer-B`, `latest-literature` or `lean-current` are rejected on the authority path even when placed in fields named `*_hash`.

This closes the **local naming attack**. It does not prove that an external human, public key, source file or literature corpus truly corresponds to the bytes represented by a digest. That mapping is the explicit provenance/identity trust root and must be established by the external acquisition/review process. Recursing locally beyond that point would amount to self-certifying the external identity the paper is designed not to self-certify.

V4 remains conservative: it may narrow a v3 candidate path, never promote a record that v3 rejected. It grants no theorem, novelty, research-value, scientific or publication authority by itself.
