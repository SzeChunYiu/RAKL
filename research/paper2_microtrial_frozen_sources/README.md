# Frozen source snapshots

Frozen batch contracts and execution packets bind source files by repository
path and sha256 **as the bytes existed when the experiment was frozen and
executed**. Source files legitimately evolve afterwards. Historical artifacts
must never be regenerated to track the live tree (that silently rewrites the
evidence record of completed experiments); instead the executed bytes are
archived here, and test resolution redirects a frozen binding to its snapshot
**only** when the snapshot bytes hash to exactly the sha256 recorded in the
frozen artifact. A snapshot can therefore never be used to bless drift: a
wrong or edited snapshot fails the very hash check it exists to satisfy.

| Snapshot | sha256 | Executed by | Archived from |
|---|---|---|---|
| `paper2_pendulum_microtrial_51f3e992.py.frozen` | `51f3e992206dcfeccceea98388fb799848c5f0b600361c7a52c1047dd9ce9590` | LUNARC jobs 3475193, 3475212, 3476520, 3476521, 3476524, 3476540, 3476564, 3476566 (run_manifest.json in each `native_job_*` directory records this sha) | `git show 8351c38^:src/rakl/paper2_pendulum_microtrial.py` |

The live `src/rakl/paper2_pendulum_microtrial.py` gained the V4.3.1 flat
materialize policy in 8351c38 (PR #270) and now hashes
`7bbf0acb03e064f0129bf639d00dfe37d712fc19816642175777604bc6213e8b`; the
V4.3.1 contract and job 3476576 bind that version. Both bindings are correct
for their own generation.

Resolution registry: `tests/frozen_source_snapshots.py`.
