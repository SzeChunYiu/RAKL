namespace PaperVAssurance

universe u v

/-- The noncompensatory mathematical research-authority coordinates.
    `value` is retained as a separate research-selection coordinate; the strict
    load-bearing promotion gate below requires specification, theorem truth,
    novelty evidence, and verifier trust. -/
structure Authority where
  specification : Bool
  truth : Bool
  novelty : Bool
  value : Bool
  verifierTrust : Bool
  deriving Repr, DecidableEq

/-- Strict load-bearing research promotion.  A missing specification, truth,
    novelty, or verifier-trust coordinate cannot be compensated by another one. -/
def promotable (a : Authority) : Prop :=
  a.specification = true ∧
  a.truth = true ∧
  a.novelty = true ∧
  a.verifierTrust = true

/-- P5-T1: proposal-generator error is contained by a sound exact-statement
    checker whenever the promotion rule requires checker acceptance. -/
theorem generator_error_containment
    {Statement : Type u}
    {ProofArtifact : Type v}
    (isTrue : Statement → Prop)
    (checker : ProofArtifact → Statement → Bool)
    (promotes : ProofArtifact → Statement → Prop)
    (checkerSound : ∀ p t, checker p t = true → isTrue t)
    (promotionRequiresCheck : ∀ p t, promotes p t → checker p t = true)
    {p : ProofArtifact}
    {t : Statement}
    (hPromote : promotes p t) :
    isTrue t := by
  exact checkerSound p t (promotionRequiresCheck p t hPromote)

/-- P5-T2: a promoted mathematical research result carries every load-bearing
    coordinate.  No scalar or strong sibling coordinate can erase a missing one. -/
theorem promotion_noncompensation
    (a : Authority)
    (h : promotable a) :
    a.specification = true ∧
    a.truth = true ∧
    a.novelty = true ∧
    a.verifierTrust = true := by
  exact h

/-- A bounded literature expansion can revise novelty authority without changing
    the theorem-truth coordinate of the already checked formal statement. -/
def literatureExpansion (a : Authority) : Authority :=
  { a with novelty := false }

/-- P5-T3: truth and novelty have different update behaviour.  This theorem is
    an existence statement about the typed state transition, not a global
    novelty certificate for any concrete mathematical result. -/
theorem truth_stable_novelty_can_drop :
    ∃ before after : Authority,
      before.truth = true ∧
      before.novelty = true ∧
      after.truth = true ∧
      after.novelty = false := by
  let before : Authority := {
    specification := true
    truth := true
    novelty := true
    value := true
    verifierTrust := true
  }
  let after := literatureExpansion before
  exact ⟨before, after, rfl, rfl, rfl, rfl⟩

/-- Transitive dependency evidence for a proof DAG. -/
inductive DepClosure {α : Type u} (edge : α → α → Prop) : α → α → Prop where
  | direct {a b : α} : edge a b → DepClosure edge a b
  | step {a b c : α} : edge a b → DepClosure edge b c → DepClosure edge a c

/-- P5-T4: direct dependency followed by a dependency-chain witness composes
    into a transitive dependency witness. -/
theorem dependency_closure_two_step
    {α : Type u}
    {edge : α → α → Prop}
    {a b c : α}
    (hab : edge a b)
    (hbc : edge b c) :
    DepClosure edge a c := by
  exact DepClosure.step hab (DepClosure.direct hbc)

/-- Research/search state deliberately separates proposal contents from
    mathematical authority. -/
structure ResearchState where
  authority : Authority
  proposalCount : Nat
  deriving Repr, DecidableEq

/-- Proposal generation may change the pursuit/search plane. -/
def proposalStep (s : ResearchState) : ResearchState :=
  { s with proposalCount := s.proposalCount + 1 }

/-- P5-T5: proposal generation by itself cannot move mathematical authority. -/
theorem proposal_noninterference (s : ResearchState) :
    (proposalStep s).authority = s.authority := by
  rfl

end PaperVAssurance
