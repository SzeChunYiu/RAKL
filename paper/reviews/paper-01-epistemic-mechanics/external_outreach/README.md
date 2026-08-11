# Paper 1 external-review outreach receipts

This directory is an operational layer for the immutable Paper 1 solicitation packet
in `../external_solicitation/`. It does **not** contain an external review.

## Public solicitation already made

GitHub issue [#41](https://github.com/SzeChunYiu/RAKL/issues/41) publicly requests
separate formal-methods, novelty/prior-art, and editorial/significance reviewers.
`PUBLIC_SOLICITATION_OBSERVATION.json` records the state observed at
`2026-08-11T03:34:26Z`: the issue was open, carried `help wanted` and `question`
labels, and had zero public comments.

That observation is deliberately narrow. A public issue is not a private delivery
receipt, a public comment is not automatically a qualified review, and zero public
comments cannot establish that no private response exists. No outbound private request
receipt or external response is supplied here.

## Why a second machine-readable object is needed

The existing `RESPONSE_TEMPLATE.json` records what a reviewer returns. It does not
record which exact packet and lens a coordinator actually sent, when the request body
was frozen, or whether private delivery evidence exists. `REQUEST_TEMPLATE.json`
provides that missing pre-response chronology while preserving privacy and authority
boundaries.

## Coordinator procedure

1. Keep reviewer identity, contact details, conflict evidence, and transport metadata
   outside the public repository.
2. Assign one four-character reviewer code and one lens. Use different people for the
   three lenses unless a later qualification receipt explicitly justifies otherwise.
3. Copy `REQUEST_TEMPLATE.json`. Bind the exact immutable packet-manifest hash, chosen
   track, reviewer code/role, artifact hashes, and response contract.
4. Freeze and hash the exact human-readable request payload before sending it. Send
   through the private channel, then hash the exact private transport confirmation
   bytes. Store only those two SHA-256 values in the public receipt.
5. Record UTC chronology satisfying:

   ```text
   concern code assigned
   <= request payload frozen
   <= request sent
   <= private delivery receipt recorded
   < response due
   ```

6. Set `request_status` to `frozen-outbound-solicitation-receipt`, replace every zero
   hash and `EXAMPLE ONLY` value, make every request attestation true, and set only
   `declaration.solicitation_sent` to true.
7. Validate from the repository root:

   ```bash
   python review/paper1/external_outreach/validate_request.py REQUEST.json
   ```

The success message means only that the receipt is structurally and relationally
bound. It does not prove reviewer identity, expertise, independence, response receipt,
review correctness, peer review, acceptance, or publication. A returned response must
still pass the existing response validator and a separate private coordinator
identity/COI/chronology qualification audit.

## Files

- `PUBLIC_SOLICITATION_OBSERVATION.json` — bounded observation of issue #41.
- `REQUEST_TEMPLATE.json` — not-sent example for one reviewer/lens.
- `SCHEMA.json` — standalone copy of the request schema.
- `validate_request.py` — packet, issue-observation, track, identity-code, return,
  chronology, privacy, and authority-boundary checks.
