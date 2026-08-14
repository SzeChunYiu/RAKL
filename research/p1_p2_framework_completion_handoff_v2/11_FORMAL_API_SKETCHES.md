# Formal API Sketches

These are implementation interfaces, not production code.

```python
def propose_representations(observations, problem_fibre):
    # Proposal-only; never writes canonical authority.
    ...

def progressive_align(examples, abstraction_levels, constraints):
    # Return alignments, rerepresentation proposals, alignable differences.
    ...

def induce_schema(alignments, anti_unifier):
    # Common relational schema + explicit lost/non-common structure.
    ...

def representation_discriminator(candidates, admissible_probes, cost_model):
    # Choose a load-bearing discriminating probe.
    ...

def validate_typed_morphism(witness, registry):
    # LICENSED / REJECTED / CANNOT_CHECK + certificate/obstruction.
    ...

def generate_explanations(state, anomalies):
    # Each explanation exports predictions and assumptions.
    ...

def choose_fibre_probe(hypotheses, actions, decision_loss, cost_model):
    # VOI / worst-case discriminator; proposal-only.
    ...

def audit_voi_saturation(fibre, admissible_actions, metalevel_model):
    # SATURATED_SCOPED / NOT_SATURATED / CANNOT_CERTIFY.
    ...

def revise_assumption_environment(state, evidence):
    # Append-only revision of support/nogood/attack structure.
    ...

def audit_source_monitoring(claim, memory_state):
    # Reject familiarity/repetition as authority evidence.
    ...

def evaluate_triangulation(evidence_roots, bias_registry):
    # Common-bias exclusion / CANNOT_CHECK; no truth minting.
    ...

def certify_decision_projection(full_state, projection, decision_class):
    # Sufficiency / collision witness / CANNOT_CHECK.
    ...

def consolidate_schema(episodes, replay_battery):
    # Slow-store proposal; episodes immutable; authority floor.
    ...

def revive_negative(epoch, attribution, candidate_levers):
    # Material mechanism change only; threshold/seed shopping invalid.
    ...

def recursive_framework_saturation(domain_waves, mechanic_registry):
    # Bounded saturation over mechanic classes, not citation count.
    ...
```

## Required shared types

```text
RepresentationProposal
SchemaProposal
AlignmentBundle
MorphismWitness
MorphismCertificate
Obstruction
ExplanationProposal
ProbeProposal
EvidenceAcquisitionProposal
ArgumentEnvironment
Nogood
AttackEdge
SourceMonitoringRecord
BiasSignature
TriangulationCertificate
ProjectionCertificate
RevivalPlan
FrameworkSaturationReceipt
```

All proposal types carry:
`subject_hash`, `created_before_outcome`, `scope`, `assumptions`, `grants_authority=false`.
