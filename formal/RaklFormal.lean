/-
  Machine-checked core results of Paper I — Epistemic Mechanics.

  Deliberately dependency-free (no mathlib): subsets are predicates and every
  hypothesis the paper relies on is passed explicitly rather than being supplied
  by a typeclass. That is not a limitation here — it is the point. The paper's
  own thesis is that lattice/authority language is only licensed once its
  hypotheses are declared, so making each hypothesis an explicit argument is the
  faithful formalization.

  Status: a theorem in this file is MECHANIZED in
  research/paper1_formal_closure/theorem_inventory.json. That status is the only
  reviewer-independent one available, because a proof accepted by the Lean kernel
  does not rest on the judgement of whoever wrote it.

  Proposal-only: nothing here grants scientific or promotion authority.
-/

namespace RaklFormal

universe u v w x

/-- A subset of `A`, encoded as a predicate. -/
def Sub (A : Type u) : Type u := A → Prop

/-- Subset inclusion. -/
def Incl {A : Type u} (X Y : Sub A) : Prop := ∀ a, X a → Y a

@[inherit_doc] infix:50 " ⊑ " => Incl

theorem Incl.refl {A : Type u} (X : Sub A) : X ⊑ X := fun _ h => h

theorem Incl.trans {A : Type u} {X Y Z : Sub A} (h₁ : X ⊑ Y) (h₂ : Y ⊑ Z) : X ⊑ Z :=
  fun a ha => h₂ a (h₁ a ha)

/-- Indexed intersection. -/
def iInter {A : Type u} {I : Type v} (f : I → Sub A) : Sub A := fun a => ∀ i, f i a

/-- Indexed union. -/
def iUnion {A : Type u} {I : Type v} (f : I → Sub A) : Sub A := fun a => ∃ i, f i a

/-! ## Theorem: No faithful scalarization of incomparability

Paper I, `02_compatibility_authority.tex:139`. This is the formal backbone of the
repo-wide prohibition on a single weighted score: `permits_scalar_ranking` is
pinned `false` in the external-agent registry schema precisely because of this.

Stated for an arbitrary *total* target order rather than specifically `ℝ`, which
is strictly more general and avoids needing a reals development. -/
theorem no_faithful_scalarization
    {P : Type u} (le : P → P → Prop)
    {R : Type v} (leR : R → R → Prop)
    (total : ∀ r s, leR r s ∨ leR s r)
    (x y : P)
    (hxy : ¬ le x y) (hyx : ¬ le y x)
    (s : P → R)
    (faithful : ∀ a b, le a b ↔ leR (s a) (s b)) :
    False := by
  rcases total (s x) (s y) with h | h
  · exact hxy ((faithful x y).mpr h)
  · exact hyx ((faithful y x).mpr h)

/-! ## Proposition: Projection-collision impossibility

Paper I, `02d_projection_sufficiency.tex:15`. Once a projection `π` erases a
distinction, no deterministic policy over the projected interface can be correct
on both worlds. Note this is scoped to deterministic policies *over the
projection* — it makes no claim that the erased fact is uninferable in principle. -/
theorem projection_collision
    {S : Type u} {Z : Type v} {Act : Type w}
    (π : S → Z) (astar : S → Act)
    (x y : S) (hπ : π x = π y) (hne : astar x ≠ astar y)
    (f : Z → Act) :
    ¬ (f (π x) = astar x ∧ f (π y) = astar y) := by
  rintro ⟨h₁, h₂⟩
  apply hne
  rw [← h₁, ← h₂, hπ]

/-! ## Theorem: Unrestricted open-world completeness is not finitely certifiable

Paper I, `04_owmd.tex:95`. Two worlds agreeing on the entire finite observed
transcript cannot be separated by any decision function over that transcript.
This is why the codebase has no `ABSOLUTELY_COMPLETE` state and why
`absolute_complete` is pinned `false` in the saturation schema. -/
theorem open_world_not_finitely_certifiable
    {World : Type u} {Transcript : Type v}
    (obs : World → Transcript)
    (noUndiscoveredMechanism : World → Prop)
    (w₁ w₂ : World)
    (hsame : obs w₁ = obs w₂)
    (h₁ : noUndiscoveredMechanism w₁)
    (h₂ : ¬ noUndiscoveredMechanism w₂)
    (cert : Transcript → Prop)
    (sound : ∀ w, cert (obs w) → noUndiscoveredMechanism w)
    (complete : ∀ w, noUndiscoveredMechanism w → cert (obs w)) :
    False := by
  have hc : cert (obs w₁) := complete w₁ h₁
  rw [hsame] at hc
  exact h₂ (sound w₂ hc)

/-! ## Theorem: Closure-system lattice

Paper I, `02_compatibility_authority.tex:92`. Meets are intersections and joins
are closures of unions. Rather than asserting a `CompleteLattice` instance, each
half of the lattice claim is proved separately — closedness, bound, and
extremality — which is exactly the content the paper's proof establishes. -/
structure ClosureOp (A : Type u) where
  cl : Sub A → Sub A
  extensive : ∀ X, X ⊑ cl X
  monotone : ∀ X Y, X ⊑ Y → cl X ⊑ cl Y
  idempotent : ∀ X a, cl (cl X) a ↔ cl X a

/-- A set is closed when the operator fixes it. -/
def Closed {A : Type u} (c : ClosureOp A) (X : Sub A) : Prop := ∀ a, c.cl X a ↔ X a

section Lattice

variable {A : Type u} {I : Type v} (c : ClosureOp A) (f : I → Sub A)

/-- Meets: an intersection of closed sets is closed. -/
theorem iInter_closed (hf : ∀ i, Closed c (f i)) : Closed c (iInter f) := by
  intro a
  constructor
  · intro h i
    have hsub : iInter f ⊑ f i := fun _ hb => hb i
    exact (hf i a).mp (c.monotone _ _ hsub a h)
  · intro h
    exact c.extensive _ a h

/-- The intersection is a lower bound. -/
theorem iInter_lower (i : I) : iInter f ⊑ f i := fun _ h => h i

/-- The intersection is the *greatest* lower bound. -/
theorem iInter_greatest (Y : Sub A) (hlb : ∀ i, Y ⊑ f i) : Y ⊑ iInter f :=
  fun a ha i => hlb i a ha

/-- Joins: the closure of a union is closed. -/
theorem cl_iUnion_closed : Closed c (c.cl (iUnion f)) := fun a => c.idempotent _ a

/-- The closure of the union is an upper bound. -/
theorem cl_iUnion_upper (i : I) : f i ⊑ c.cl (iUnion f) :=
  fun a ha => c.extensive _ a ⟨i, ha⟩

/-- The closure of the union is the *least* closed upper bound. -/
theorem cl_iUnion_least (Y : Sub A) (hY : Closed c Y) (hub : ∀ i, f i ⊑ Y) :
    c.cl (iUnion f) ⊑ Y := by
  intro a ha
  have hsub : iUnion f ⊑ Y := by
    rintro b ⟨i, hb⟩
    exact hub i b hb
  exact (hY a).mp (c.monotone _ _ hsub a ha)

end Lattice

/-! ## Theorem: Finite-basis saturation

Paper I, `04_owmd.tex:162`. The least-fixed-point and stabilization halves are
mechanized here. The cardinality bound (`at most |U| - |K₀|` strict-growth steps)
needs a finiteness development and is mechanized in the `Finiteness` section at
the end of this file. -/
def Iter {A : Type u} (F : Sub A → Sub A) (K₀ : Sub A) : Nat → Sub A
  | 0 => K₀
  | n + 1 => F (Iter F K₀ n)

/-- Every iterate stays below any pre-fixed point above `K₀`. -/
theorem iter_below_prefixed
    {A : Type u} (F : Sub A → Sub A)
    (mono : ∀ X Y, X ⊑ Y → F X ⊑ F Y)
    (K₀ Y : Sub A) (hY : F Y ⊑ Y) (h₀ : K₀ ⊑ Y) :
    ∀ n, Iter F K₀ n ⊑ Y := by
  intro n
  induction n with
  | zero => exact h₀
  | succ k ih => exact fun a ha => hY a (mono _ _ ih a ha)

/-- At the first non-strict step the iteration has reached a fixed point. -/
theorem stabilized_is_fixed
    {A : Type u} (F : Sub A → Sub A)
    (infl : ∀ X, X ⊑ F X)
    (K₀ : Sub A) (n : Nat)
    (hstop : Iter F K₀ (n + 1) ⊑ Iter F K₀ n) :
    ∀ a, F (Iter F K₀ n) a ↔ Iter F K₀ n a :=
  fun a => ⟨fun ha => hstop a ha, fun ha => infl _ a ha⟩

/-- The stabilized state is the least fixed point above `K₀`. -/
theorem stabilized_is_least
    {A : Type u} (F : Sub A → Sub A)
    (mono : ∀ X Y, X ⊑ Y → F X ⊑ F Y)
    (K₀ : Sub A) (n : Nat)
    (Y : Sub A) (hY : F Y ⊑ Y) (h₀ : K₀ ⊑ Y) :
    Iter F K₀ n ⊑ Y :=
  iter_below_prefixed F mono K₀ Y hY h₀ n

/-! ## The non-escalation family

Paper I proves four separate propositions by the same argument:

* Proposal non-sovereignty (`01_introduction_foundations_state.tex:173`)
* Experience-routing non-escalation (`02b_v3_epistemic_projection.tex:25`)
* Derived-view authority non-escalation (`02bb_task_conditioned_erasure.tex:18`)
* Training-update non-sovereignty (`02c_training_time_projection.tex:30`)

Each says: operators of some class have codomain outside canonical scientific
state, so no composition of them moves the canonical projection until a
separately certified update occurs. Rather than mechanize four near-duplicates,
the shared principle is proved once and each proposition is an instantiation.

This also **repairs a defect**. The derived-view proof argues "by construction it
can inherit but cannot mint authority certificates", which restates its hypothesis
instead of deriving the claim — a definition presented as a theorem. Here that
hypothesis is `uncertified_preserves`: an explicit field that must be discharged
at every instantiation. What was prose becomes an obligation the type checker
enforces. -/

section NonEscalation

variable {S : Type u} {K : Type v}

/-- An operator that leaves the canonical projection untouched. -/
def PreservesCanon (canon : S → K) (op : S → S) : Prop := ∀ s, canon (op s) = canon s

/-- Sequential composition of operators, applied left to right. -/
def runAll : List (S → S) → S → S
  | [], s => s
  | op :: rest, s => runAll rest (op s)

/-- Any finite composition of canon-preserving operators preserves the canonical
projection. This is the induction the four paper proofs perform informally. -/
theorem runAll_preserves_canon (canon : S → K) :
    ∀ (ops : List (S → S)), (∀ op ∈ ops, PreservesCanon canon op) →
      ∀ s, canon (runAll ops s) = canon s := by
  intro ops
  induction ops with
  | nil => intro _ s; rfl
  | cons op rest ih =>
    intro h s
    have hop : PreservesCanon canon op := h op (List.Mem.head _)
    have hrest : ∀ o ∈ rest, PreservesCanon canon o := fun o ho => h o (List.Mem.tail _ ho)
    show canon (runAll rest (op s)) = canon s
    rw [ih hrest (op s), hop s]

/-- An operator class carrying the authority contract.

`uncertified_preserves` is the hypothesis Paper I's derived-view proof leaves
implicit. Making it a field means no instantiation can quietly skip it. -/
structure OperatorClass (S : Type u) (K : Type v) where
  canon : S → K
  Certified : (S → S) → Prop
  uncertified_preserves : ∀ op, ¬ Certified op → PreservesCanon canon op

/-- **Non-escalation.** A composition containing no certified update leaves the
canonical scientific projection invariant.

Instantiating `S` as proposal state gives proposal non-sovereignty; as episode
ledger and routing policy, experience-routing non-escalation; as a derived
task-conditioned view, derived-view non-escalation; as model weights,
training-update non-sovereignty. -/
theorem no_uncertified_composition_changes_canon
    (C : OperatorClass S K) (ops : List (S → S))
    (h : ∀ op ∈ ops, ¬ C.Certified op) :
    ∀ s, C.canon (runAll ops s) = C.canon s :=
  runAll_preserves_canon C.canon ops fun op ho => C.uncertified_preserves op (h op ho)

/-- The guarantee is not vacuous: a certified operator genuinely can move
canonical state.

Without this, non-escalation would also be satisfied by a system that never
updates anything at all, which would make the result worthless rather than
strong. Stating it rules out the degenerate reading. -/
theorem certified_operator_may_change_canon :
    ∃ (C : OperatorClass Nat Nat) (op : Nat → Nat) (s : Nat),
      C.Certified op ∧ C.canon (op s) ≠ C.canon s :=
  ⟨{ canon := id
     Certified := fun _ => True
     uncertified_preserves := fun _ hop => absurd trivial hop },
   (· + 1), 0, trivial, by decide⟩

end NonEscalation

/-! ## Proposition: Negative-history monotonicity

Paper I, `01_introduction_foundations_state.tex:191`. Append-only archival keeps
negative history monotone. Load-bearing for saturation: without it a research
process could become "saturated" precisely by discarding the refutations that
narrow its theory space. -/
section NegativeHistory

variable {A : Type u}

/-- An update that never removes a recorded negative result. -/
def Extensive (upd : Sub A → Sub A) : Prop := ∀ X, X ⊑ upd X

/-- Finite compositions of append-only updates never lose negative history. -/
theorem negative_history_monotone :
    ∀ (upds : List (Sub A → Sub A)), (∀ u ∈ upds, Extensive u) →
      ∀ H, H ⊑ runAll upds H := by
  intro upds
  induction upds with
  | nil => intro _ H; exact Incl.refl H
  | cons u rest ih =>
    intro h H
    have hu : Extensive u := h u (List.Mem.head _)
    have hrest : ∀ v ∈ rest, Extensive v := fun v hv => h v (List.Mem.tail _ hv)
    show H ⊑ runAll rest (u H)
    exact Incl.trans (hu H) (ih hrest (u H))

end NegativeHistory

/-! ## Proposition: Pairwise compatibility does not imply an order-theoretic lattice

Paper I, `02_compatibility_authority.tex:36`. The paper gives two arguments and
both are mechanized here.

1. A witnessed compatibility relation is symmetric, and symmetry together with
   antisymmetry collapses a relation into equality. So the witness relation
   cannot itself serve as the order of a poset.
2. Even when a genuine partial order *is* supplied and every pair carries an
   upper-bound witness, joins can still fail to exist. A witness does not
   establish a universal property.

The prose hedge "a witnessed compatibility relation is generally symmetric" is
not itself a proof step; the two statements below are sharper than the prose. -/

section PairwiseNotLattice

/-- A symmetric relation relating two distinct elements is not antisymmetric,
hence cannot be the order of a partially ordered set. -/
theorem symmetric_compat_not_antisymmetric
    {A : Type u} (R : A → A → Prop)
    (symm : ∀ a b, R a b → R b a)
    (antisymm : ∀ a b, R a b → R b a → a = b)
    (a b : A) (hne : a ≠ b) (hab : R a b) :
    False :=
  hne (antisymm a b hab (symm a b hab))

/-- Five typed atoms. `a` and `b` sit below both `c` and `d`, which sit below the
top element `t`; `a,b` are incomparable and so are `c,d`. -/
inductive Atom where
  | a | b | c | d | t
  deriving DecidableEq

instance instDecidableForallAtom (p : Atom → Prop) [DecidablePred p] :
    Decidable (∀ z, p z) :=
  if h : p .a ∧ p .b ∧ p .c ∧ p .d ∧ p .t then
    isTrue fun z => match z with
      | .a => h.1
      | .b => h.2.1
      | .c => h.2.2.1
      | .d => h.2.2.2.1
      | .t => h.2.2.2.2
  else
    isFalse fun hall => h ⟨hall _, hall _, hall _, hall _, hall _⟩

instance instDecidableExistsAtom (p : Atom → Prop) [DecidablePred p] :
    Decidable (∃ z, p z) :=
  if h : p .a ∨ p .b ∨ p .c ∨ p .d ∨ p .t then
    isTrue (h.elim (fun k => ⟨Atom.a, k⟩) fun h =>
      h.elim (fun k => ⟨Atom.b, k⟩) fun h =>
        h.elim (fun k => ⟨Atom.c, k⟩) fun h =>
          h.elim (fun k => ⟨Atom.d, k⟩) fun k => ⟨Atom.t, k⟩)
  else
    isFalse fun hx => h (match hx with
      | ⟨.a, hp⟩ => Or.inl hp
      | ⟨.b, hp⟩ => Or.inr (Or.inl hp)
      | ⟨.c, hp⟩ => Or.inr (Or.inr (Or.inl hp))
      | ⟨.d, hp⟩ => Or.inr (Or.inr (Or.inr (Or.inl hp)))
      | ⟨.t, hp⟩ => Or.inr (Or.inr (Or.inr (Or.inr hp))))

/-- The declared order on `Atom`. -/
def below : Atom → Atom → Bool
  | .a, .a => true
  | .a, .c => true
  | .a, .d => true
  | .a, .t => true
  | .b, .b => true
  | .b, .c => true
  | .b, .d => true
  | .b, .t => true
  | .c, .c => true
  | .c, .t => true
  | .d, .d => true
  | .d, .t => true
  | .t, .t => true
  | _,  _  => false

/-- `below` really is a partial order, so the counterexample below is not an
artefact of a badly formed order. -/
theorem below_is_partial_order :
    (∀ p, below p p = true) ∧
    (∀ p q r, below p q = true → below q r = true → below p r = true) ∧
    (∀ p q, below p q = true → below q p = true → p = q) := by
  decide

/-- Every pair of atoms carries an upper-bound witness, yet `a` and `b` have no
least upper bound. Pairwise witnesses therefore do not deliver a lattice: the
universal property fails even though no pair is left unwitnessed. -/
theorem pairwise_witnesses_but_no_join :
    (∀ p q, ∃ w, below p w = true ∧ below q w = true) ∧
    ¬ ∃ j, below Atom.a j = true ∧ below Atom.b j = true ∧
        ∀ w, below Atom.a w = true → below Atom.b w = true → below j w = true := by
  decide

end PairwiseNotLattice

/-! ## Proposition: Three-context parity obstruction

Paper I, `02_compatibility_authority.tex:64`. Three two-variable charts that are
pairwise compatible on every overlap, with no global section. Pairwise
compatibility is stated in its exact form — the two charts sharing an overlap
restrict to the *same* set on it, and that set is all of `Bool`, so the overlap
exposes nothing. -/

section ParityObstruction

/-- The `xy` chart: agreement. -/
def chartXY (p q : Bool) : Prop := p = q

/-- The `yz` chart: agreement. -/
def chartYZ (p q : Bool) : Prop := p = q

/-- The `xz` chart: disagreement. -/
def chartXZ (p q : Bool) : Prop := p ≠ q

/-- Restriction of a two-variable chart to its first coordinate. -/
def restrFst {X : Type u} {Y : Type v} (S : X → Y → Prop) : X → Prop := fun p => ∃ q, S p q

/-- Restriction of a two-variable chart to its second coordinate. -/
def restrSnd {X : Type u} {Y : Type v} (S : X → Y → Prop) : Y → Prop := fun q => ∃ p, S p q

/-- Every single-variable overlap restricts to the whole of `Bool` for both
charts that share it. -/
theorem parity_restrictions_are_total :
    (∀ q, restrSnd chartXY q) ∧ (∀ q, restrFst chartYZ q) ∧
    (∀ p, restrFst chartXY p) ∧ (∀ p, restrFst chartXZ p) ∧
    (∀ r, restrSnd chartYZ r) ∧ (∀ r, restrSnd chartXZ r) :=
  ⟨fun q => ⟨q, rfl⟩,
   fun q => ⟨q, rfl⟩,
   fun p => ⟨p, rfl⟩,
   fun p => ⟨!p, by cases p <;> intro hcon <;> exact Bool.noConfusion hcon⟩,
   fun r => ⟨r, rfl⟩,
   fun r => ⟨!r, by cases r <;> intro hcon <;> exact Bool.noConfusion hcon⟩⟩

/-- Pairwise compatibility in its exact form: the two charts sharing an overlap
restrict to the same set on it. -/
theorem parity_overlaps_agree :
    (∀ q, restrSnd chartXY q ↔ restrFst chartYZ q) ∧
    (∀ p, restrFst chartXY p ↔ restrFst chartXZ p) ∧
    (∀ r, restrSnd chartYZ r ↔ restrSnd chartXZ r) :=
  ⟨fun q => ⟨fun _ => parity_restrictions_are_total.2.1 q,
             fun _ => parity_restrictions_are_total.1 q⟩,
   fun p => ⟨fun _ => parity_restrictions_are_total.2.2.2.1 p,
             fun _ => parity_restrictions_are_total.2.2.1 p⟩,
   fun r => ⟨fun _ => parity_restrictions_are_total.2.2.2.2.2 r,
             fun _ => parity_restrictions_are_total.2.2.2.2.1 r⟩⟩

/-- **No global section.** The obstruction is transitivity of equality against a
disequality, so it is stated for an arbitrary type rather than for `Bool`. -/
theorem parity_no_global_section {T : Type u} :
    ¬ ∃ p q r : T, p = q ∧ q = r ∧ p ≠ r := by
  rintro ⟨p, q, r, hpq, hqr, hpr⟩
  exact hpr (hpq.trans hqr)

/-- The three charts have no global section despite pairwise compatibility. -/
theorem parity_charts_have_no_global_section :
    ¬ ∃ p q r : Bool, chartXY p q ∧ chartYZ q r ∧ chartXZ p r :=
  parity_no_global_section

end ParityObstruction

/-! ## Proposition: Coactivation does not imply compatibility

Paper I, `03_workspace.tex:82`. The workspace gate reads partition tags and
priorities; it has no compatibility input. Coselection therefore carries no
compatibility information — the same shape as `projection_collision`. -/

section Coactivation

/-- Reference workspace partitions. -/
inductive Partition where
  | core | challenge | novel | history
  deriving DecidableEq

/-- **Coactivation is not compatibility.** For any gate that reads only
partitions and priorities, and any pair it coselects, there is a compatibility
relation under which that pair is incompatible and the selection is unchanged. -/
theorem coactivation_not_compatibility
    {I : Type u} {P : Type v} {U : Type w}
    (pick : (I → P) → (I → U) → List I)
    (part : I → P) (prio : I → U) (a b : I)
    (ha : a ∈ pick part prio) (hb : b ∈ pick part prio) :
    ∃ compat : I → I → Prop,
      a ∈ pick part prio ∧ b ∈ pick part prio ∧ ¬ compat a b :=
  ⟨fun _ _ => False, ha, hb, id⟩

/-- Two atoms of a live debate. -/
inductive Debate where
  | claim | rebuttal
  deriving DecidableEq

/-- The rebuttal sits in the reserved CHALLENGE partition. -/
def debatePart : Debate → Partition
  | .claim => .core
  | .rebuttal => .challenge

/-- Explicit epistemic incompatibility between a claim and its rebuttal. -/
def debateCompat : Debate → Debate → Bool
  | .claim, .rebuttal => false
  | .rebuttal, .claim => false
  | _, _ => true

/-- Reservation-first selection at capacity two with one reserved CHALLENGE
slot, over the two-item pool. -/
def debatePick (part : Debate → Partition) (_prio : Debate → Nat) : List Debate :=
  let pool := [Debate.claim, Debate.rebuttal]
  let reserved := (pool.filter fun i => part i == Partition.challenge).take 1
  let rest := (pool.filter fun i => !(reserved.contains i)).take 1
  reserved ++ rest

/-- Non-vacuity: the reference gate really does coactivate a claim with the
rebuttal that contradicts it. The workspace is a debate surface, not a
consistency filter. -/
theorem coactivation_witness :
    Debate.claim ∈ debatePick debatePart (fun _ => 1) ∧
    Debate.rebuttal ∈ debatePick debatePart (fun _ => 1) ∧
    debateCompat Debate.claim Debate.rebuttal = false :=
  ⟨List.Mem.tail _ (List.Mem.head _), List.Mem.head _, rfl⟩

end Coactivation

/-! ## Proposition: Authority-preservation invariant

Paper I, `03_workspace.tex:72`. The proposition's hypothesis — a workspace-only
transition can write only workspace state — is here the explicit obligation
`(op s).1 = s.1`. The paper's one-line proof is a valid but thin derivation from
that hypothesis; making the hypothesis an argument is what gives it teeth. -/

section AuthorityPreservation

/-- **Authority preservation.** If every transition in a composition returns the
canonical component unchanged, any authority measure read off that component is
invariant. -/
theorem workspace_preserves_authority
    {K : Type u} {Wsp : Type v} {V : Type w}
    (α : K → V) (ops : List (K × Wsp → K × Wsp))
    (hws : ∀ op ∈ ops, ∀ s : K × Wsp, (op s).1 = s.1)
    (s : K × Wsp) :
    α (runAll ops s).1 = α s.1 := by
  have h : (runAll ops s).1 = s.1 :=
    runAll_preserves_canon (Prod.fst : K × Wsp → K) ops (fun op ho => hws op ho) s
  rw [h]

/-- The proposition in its stated "cannot increase" form, for any strict order on
the authority scale. -/
theorem workspace_cannot_increase_authority
    {K : Type u} {Wsp : Type v} {V : Type w}
    (α : K → V) (lt : V → V → Prop) (irrefl : ∀ v, ¬ lt v v)
    (ops : List (K × Wsp → K × Wsp))
    (hws : ∀ op ∈ ops, ∀ s : K × Wsp, (op s).1 = s.1)
    (s : K × Wsp) :
    ¬ lt (α s.1) (α (runAll ops s).1) := by
  rw [workspace_preserves_authority α ops hws s]
  exact irrefl _

/-- Non-vacuity: a workspace-only transition genuinely moves the transient
component. Computational access changes; authority does not. -/
theorem workspace_transition_changes_access :
    ∃ (op : Nat × Nat → Nat × Nat) (s : Nat × Nat),
      (∀ t : Nat × Nat, (op t).1 = t.1) ∧ (op s).2 ≠ s.2 :=
  ⟨fun t => (t.1, t.2 + 1), (0, 0), fun _ => rfl, by decide⟩

end AuthorityPreservation

/-! ## Instantiating the non-escalation family

`no_uncertified_composition_changes_canon` proves the shared principle. Each of
the four propositions is discharged below against its *own* state space and
operator form: the codomain obligation is proved for that form rather than
assumed, and each carries a non-vacuity witness showing the operator really does
move its non-canonical coordinates. -/

section NonEscalationInstances

/-- v3 state: canonical scientific state, proposal-bearing state, transient
computational state. -/
structure V3State (K : Type u) (Pr : Type v) (Tr : Type w) where
  canon : K
  proposals : Pr
  transient : Tr

/-- A proposal generator may read the whole state; its codomain is the
proposal/transient part. -/
def proposalGen {K : Type u} {Pr : Type v} {Tr : Type w}
    (g : V3State K Pr Tr → Pr × Tr) : V3State K Pr Tr → V3State K Pr Tr :=
  fun s => { canon := s.canon, proposals := (g s).1, transient := (g s).2 }

theorem proposalGen_preserves_canon {K : Type u} {Pr : Type v} {Tr : Type w}
    (g : V3State K Pr Tr → Pr × Tr) :
    PreservesCanon V3State.canon (proposalGen g) := fun _ => rfl

/-- **Proposal non-sovereignty**, discharged against v3 state. -/
theorem proposal_non_sovereignty {K : Type u} {Pr : Type v} {Tr : Type w}
    (ops : List (V3State K Pr Tr → V3State K Pr Tr))
    (hgen : ∀ op ∈ ops, ∃ g, op = proposalGen g)
    (s : V3State K Pr Tr) :
    (runAll ops s).canon = s.canon := by
  refine runAll_preserves_canon V3State.canon ops ?_ s
  intro op ho
  rcases hgen op ho with ⟨g, rfl⟩
  exact proposalGen_preserves_canon g

/-- Non-vacuity: a proposal generator really can change proposal state. -/
theorem proposalGen_changes_proposals :
    ∃ (g : V3State Nat Nat Nat → Nat × Nat) (s : V3State Nat Nat Nat),
      (proposalGen g s).canon = s.canon ∧ (proposalGen g s).proposals ≠ s.proposals :=
  ⟨fun t => (t.proposals + 1, t.transient), ⟨0, 0, 0⟩, rfl, by decide⟩

/-- Episode ledger and experience-conditioned routing policy alongside canonical
state. -/
structure ExperienceState (K : Type u) (E : Type v) (R : Type w) where
  canon : K
  episodes : E
  routing : R

/-- An episode-storage or routing update: codomain is experience/policy state. -/
def experienceUpdate {K : Type u} {E : Type v} {R : Type w}
    (g : ExperienceState K E R → E × R) : ExperienceState K E R → ExperienceState K E R :=
  fun s => { canon := s.canon, episodes := (g s).1, routing := (g s).2 }

theorem experienceUpdate_preserves_canon {K : Type u} {E : Type v} {R : Type w}
    (g : ExperienceState K E R → E × R) :
    PreservesCanon ExperienceState.canon (experienceUpdate g) := fun _ => rfl

/-- **Experience-routing non-escalation**, discharged, in the proposition's
"cannot increase any authority coordinate" form. -/
theorem experience_routing_non_escalation
    {K : Type u} {E : Type v} {R : Type w} {V : Type x}
    (α : K → V) (lt : V → V → Prop) (irrefl : ∀ v, ¬ lt v v)
    (ops : List (ExperienceState K E R → ExperienceState K E R))
    (hgen : ∀ op ∈ ops, ∃ g, op = experienceUpdate g)
    (s : ExperienceState K E R) :
    ¬ lt (α s.canon) (α (runAll ops s).canon) := by
  have h : (runAll ops s).canon = s.canon := by
    refine runAll_preserves_canon ExperienceState.canon ops ?_ s
    intro op ho
    rcases hgen op ho with ⟨g, rfl⟩
    exact experienceUpdate_preserves_canon g
  rw [h]
  exact irrefl _

/-- Non-vacuity: routing really can change, which is the point — search order
moves while authority does not. -/
theorem experienceUpdate_changes_routing :
    ∃ (g : ExperienceState Nat Nat Nat → Nat × Nat) (s : ExperienceState Nat Nat Nat),
      (experienceUpdate g s).canon = s.canon ∧ (experienceUpdate g s).routing ≠ s.routing :=
  ⟨fun t => (t.episodes, t.routing + 1), ⟨0, 0, 0⟩, rfl, by decide⟩

/-- Pinned content-addressed source together with a task-conditioned derived
view. -/
structure ViewState (K : Type u) (Z : Type v) where
  source : K
  view : Z

/-- A derived-view operator recomputes the view and leaves the pinned source
untouched. -/
def derivedView {K : Type u} {Z : Type v} (q : ViewState K Z → Z) :
    ViewState K Z → ViewState K Z :=
  fun s => { source := s.source, view := q s }

theorem derivedView_preserves_source {K : Type u} {Z : Type v} (q : ViewState K Z → Z) :
    PreservesCanon ViewState.source (derivedView q) := fun _ => rfl

/-- Certificate inheritance: every certificate the view carries is already
reachable from the pinned source. Paper I's proof *asserts* this ("by
construction it can inherit but cannot mint authority certificates"); here it is
an obligation carried explicitly through the composition. -/
def Inherits {K : Type u} {Z : Type v} {C : Type w}
    (srcCerts : K → C → Prop) (viewCerts : Z → C → Prop) (s : ViewState K Z) : Prop :=
  ∀ c, viewCerts s.view c → srcCerts s.source c

/-- **Derived-view authority non-escalation**, discharged. A composition of
derived-view operators leaves the pinned source fixed *and* mints no
certificate. This is the repair of the paper's circular proof: what the prose
restates as a hypothesis is here an inductive invariant. -/
theorem derived_view_non_escalation {K : Type u} {Z : Type v} {C : Type w}
    (srcCerts : K → C → Prop) (viewCerts : Z → C → Prop) :
    ∀ (ops : List (ViewState K Z → ViewState K Z)),
      (∀ op ∈ ops, ∃ q, op = derivedView q ∧
        ∀ t, Inherits srcCerts viewCerts t → ∀ c, viewCerts (q t) c → srcCerts t.source c) →
      ∀ s, Inherits srcCerts viewCerts s →
        (runAll ops s).source = s.source ∧ Inherits srcCerts viewCerts (runAll ops s) := by
  intro ops
  induction ops with
  | nil => intro _ s hs; exact ⟨rfl, hs⟩
  | cons op rest ih =>
    intro h s hs
    rcases h op (List.Mem.head _) with ⟨q, rfl, hq⟩
    have hs' : Inherits srcCerts viewCerts (derivedView q s) := hq s hs
    have hrest : ∀ o ∈ rest, ∃ q, o = derivedView q ∧
        ∀ t, Inherits srcCerts viewCerts t → ∀ c, viewCerts (q t) c → srcCerts t.source c :=
      fun o ho => h o (List.Mem.tail _ ho)
    exact ih hrest (derivedView q s) hs'

/-- The proposition's "cannot increase authority" form follows from source
invariance. -/
theorem derived_view_cannot_increase_authority
    {K : Type u} {Z : Type v} {C : Type w} {V : Type x}
    (srcCerts : K → C → Prop) (viewCerts : Z → C → Prop)
    (α : K → V) (lt : V → V → Prop) (irrefl : ∀ v, ¬ lt v v)
    (ops : List (ViewState K Z → ViewState K Z))
    (h : ∀ op ∈ ops, ∃ q, op = derivedView q ∧
        ∀ t, Inherits srcCerts viewCerts t → ∀ c, viewCerts (q t) c → srcCerts t.source c)
    (s : ViewState K Z) (hs : Inherits srcCerts viewCerts s) :
    ¬ lt (α s.source) (α (runAll ops s).source) := by
  rw [(derived_view_non_escalation srcCerts viewCerts ops h s hs).1]
  exact irrefl _

/-- Non-vacuity: a derived view really can change. Computational suppression of a
coordinate is a real operation, not a no-op. -/
theorem derivedView_changes_view :
    ∃ (q : ViewState Nat Nat → Nat) (s : ViewState Nat Nat),
      (derivedView q s).source = s.source ∧ (derivedView q s).view ≠ s.view :=
  ⟨fun t => t.view + 1, ⟨0, 0⟩, rfl, by decide⟩

/-- Model parameters and learner-state measurements alongside canonical state. -/
structure TrainState (K : Type u) (Θ : Type v) (M : Type w) where
  canon : K
  params : Θ
  metrics : M

/-- An optimizer step with its training projection: codomain is
model/computational state. -/
def trainStep {K : Type u} {Θ : Type v} {M : Type w}
    (g : TrainState K Θ M → Θ × M) : TrainState K Θ M → TrainState K Θ M :=
  fun s => { canon := s.canon, params := (g s).1, metrics := (g s).2 }

theorem trainStep_preserves_canon {K : Type u} {Θ : Type v} {M : Type w}
    (g : TrainState K Θ M → Θ × M) :
    PreservesCanon TrainState.canon (trainStep g) := fun _ => rfl

/-- **Training-update non-sovereignty**, discharged. -/
theorem training_update_non_sovereignty
    {K : Type u} {Θ : Type v} {M : Type w} {V : Type x}
    (α : K → V) (lt : V → V → Prop) (irrefl : ∀ v, ¬ lt v v)
    (ops : List (TrainState K Θ M → TrainState K Θ M))
    (hgen : ∀ op ∈ ops, ∃ g, op = trainStep g)
    (s : TrainState K Θ M) :
    ¬ lt (α s.canon) (α (runAll ops s).canon) := by
  have h : (runAll ops s).canon = s.canon := by
    refine runAll_preserves_canon TrainState.canon ops ?_ s
    intro op ho
    rcases hgen op ho with ⟨g, rfl⟩
    exact trainStep_preserves_canon g
  rw [h]
  exact irrefl _

/-- Non-vacuity: a training step really can change behaviour. The separation is
between behaviour and authority, not a claim that training does nothing. -/
theorem trainStep_changes_params :
    ∃ (g : TrainState Nat Nat Nat → Nat × Nat) (s : TrainState Nat Nat Nat),
      (trainStep g s).canon = s.canon ∧ (trainStep g s).params ≠ s.params :=
  ⟨fun t => (t.params + 1, t.metrics), ⟨0, 0, 0⟩, rfl, by decide⟩

end NonEscalationInstances

/-! ## Proposition: New substantive knowledge reopens saturation

Paper I, `04_owmd.tex:193`. History is ordered most-recent-first. The rule is
non-compensatory by construction: a round is flat only when *every* coordinate of
its progress vector is zero. This is the claim enforced behaviourally by
`PFC-SATURATION-REOPENS-ON-GROWTH` in `src/rakl/paper_framework_consistency.py`. -/

section SaturationReopens

/-- A round's substantive-progress vector: one non-negative coordinate per
tracked kind of change. -/
abbrev Delta : Type := List Nat

/-- Flatness requires every coordinate to be zero. -/
def Flat (d : Delta) : Prop := ∀ n ∈ d, n = 0

/-- **Non-compensatory.** One non-zero coordinate destroys flatness however large
the other coordinates are: ten new paragraphs cannot cancel one counterexample. -/
theorem flatness_is_non_compensatory (d : Delta) (n : Nat) (hn : n ∈ d) (hne : n ≠ 0) :
    ¬ Flat d := fun h => hne (h n hn)

/-- The consecutive-flat-round rule: the most recent `m ≥ 1` rounds must all be
flat. -/
def BoundedSaturated (m : Nat) (history : List Delta) : Prop :=
  1 ≤ m ∧ m ≤ history.length ∧ ∀ d ∈ history.take m, Flat d

/-- **New substantive knowledge reopens saturation.** A round with a non-zero
progress vector makes the newest flat run empty, so no positive flat-round
requirement can be satisfied. -/
theorem growth_reopens_saturation
    (m : Nat) (d : Delta) (history : List Delta) (hgrow : ¬ Flat d) :
    ¬ BoundedSaturated m (d :: history) := by
  rintro ⟨hm, _, hflat⟩
  cases m with
  | zero => exact absurd hm (Nat.not_succ_le_zero 0)
  | succ k => exact hgrow (hflat d (List.Mem.head _))

/-- Membership in a prefix taken from the left summand stays in that summand. -/
theorem mem_take_append_left {A : Type u} :
    ∀ (n : Nat) (l r : List A), n ≤ l.length → ∀ a ∈ (l ++ r).take n, a ∈ l := by
  intro n
  induction n with
  | zero => intro _ _ _ _ ha; cases ha
  | succ k ih =>
    intro l r hlen a ha
    cases l with
    | nil => exact absurd hlen (Nat.not_succ_le_zero k)
    | cons z zs =>
      cases ha with
      | head => exact List.Mem.head _
      | tail _ h' => exact List.Mem.tail _ (ih zs r (Nat.le_of_succ_le_succ hlen) a h')

/-- Appending on the left never shortens a list. -/
theorem le_length_append {A : Type u} : ∀ (l r : List A), l.length ≤ (l ++ r).length := by
  intro l
  induction l with
  | nil => intro _; exact Nat.zero_le _
  | cons _ zs ih => intro r; exact Nat.succ_le_succ (ih r)

/-- Saturation is reopened, not destroyed: once the required number of flat
rounds has been observed again the rule is satisfied again. Without this,
`growth_reopens_saturation` would also be satisfied by a system that can never
re-saturate. -/
theorem saturation_returns_after_required_flat_rounds
    (m : Nat) (hm : 1 ≤ m) (fresh old : List Delta)
    (hlen : m ≤ fresh.length) (hfresh : ∀ d ∈ fresh, Flat d) :
    BoundedSaturated m (fresh ++ old) :=
  ⟨hm, Nat.le_trans hlen (le_length_append fresh old),
   fun d hd => hfresh d (mem_take_append_left m fresh old hlen d hd)⟩

end SaturationReopens

/-! ## Proposition: Freshness-horizon expiry

Paper I, `04_owmd.tex:207`. The content is that the release gate is
non-compensatory across *kinds* of obligation: a certificate can discharge every
flat-round obligation and still fail, and only rerunning the freshness route
repairs it. -/

section Freshness

/-- A bounded saturation certificate records the cutoff its freshness route
actually reached, along with the number of consecutive flat rounds observed. -/
structure SaturationCert (T : Type u) where
  cutoff : T
  flatRoundsObserved : Nat

/-- The release gate: the flat-round requirement *and* the freshness
requirement. -/
def ReleaseAdmissible {T : Type u} (le : T → T → Prop)
    (required : T) (m : Nat) (c : SaturationCert T) : Prop :=
  m ≤ c.flatRoundsObserved ∧ le required c.cutoff

/-- **Freshness expiry.** A certificate that discharges its entire flat-round
obligation still fails the gate once the required cutoff moves past the one its
route reached. -/
theorem freshness_expiry
    {T : Type u} (le : T → T → Prop)
    (c : SaturationCert T) (required : T) (m : Nat)
    (_hflat : m ≤ c.flatRoundsObserved)
    (hstale : ¬ le required c.cutoff) :
    ¬ ReleaseAdmissible le required m c :=
  fun h => hstale h.2

/-- More flat rounds cannot repair staleness: the certificate fails for every
flat-round count, so freshness is not compensable. -/
theorem freshness_not_compensable_by_flat_rounds
    {T : Type u} (le : T → T → Prop)
    (c : SaturationCert T) (required : T)
    (hstale : ¬ le required c.cutoff) :
    ∀ n : Nat, ¬ ReleaseAdmissible le required n { c with flatRoundsObserved := n } :=
  fun _ h => hstale h.2

/-- Rerunning the freshness route through at least the required cutoff is what
restores admissibility. The obligation is discharged by work, not by waiting. -/
theorem freshness_rerun_restores
    {T : Type u} (le : T → T → Prop)
    (c : SaturationCert T) (required tNew : T) (m : Nat)
    (hflat : m ≤ c.flatRoundsObserved)
    (hrerun : le required tNew) :
    ReleaseAdmissible le required m { c with cutoff := tNew } :=
  ⟨hflat, hrerun⟩

/-- Non-vacuity: an otherwise perfect certificate — flat-round obligation
over-discharged — is refused, and the rerun repairs exactly that. -/
theorem freshness_expiry_witness :
    ¬ ReleaseAdmissible (fun a b : Nat => a ≤ b) 7 5 { cutoff := 3, flatRoundsObserved := 5 } ∧
    ReleaseAdmissible (fun a b : Nat => a ≤ b) 7 5 { cutoff := 8, flatRoundsObserved := 5 } :=
  ⟨fun h => absurd (show (7 : Nat) ≤ 3 from h.2) (by decide),
   ⟨show (5 : Nat) ≤ 5 by decide, show (7 : Nat) ≤ 8 by decide⟩⟩

end Freshness

/-! ## Theorem: Finite-basis saturation — the cardinality bound

Paper I, `04_owmd.tex:162`. The least-fixed-point and stabilization halves are
mechanized above. This section adds the counting half: at most `|U| - |K₀|`
strict-growth steps.

Encoding decisions, stated rather than hidden — each is a place where a
predicate encoding has to re-supply something the paper gets from typing:

* Subsets are predicates, so `F : P(U_B) → P(U_B)` is not a typing fact here.
  "`F` maps subsets of `U` to subsets of `U`" is the explicit hypothesis
  `hFuniv`, and `K₀ ⊆ U` is `hK₀univ`.
* The finite universe is an explicit enumeration `univ : List A`. `Distinct univ`
  is what makes `keep`-length the true cardinality rather than a multiset count.
* "Every strict inclusion adds at least one element" is supplied as a **witness
  function** `w`, naming the element each step adds, rather than as a bare `∃`.
  Turning `∃ a, P a` into list data requires `Classical.choice`, which would put
  `choice` into the axiom report and destroy the development's central claim.
  Requiring the witness is therefore a genuine strengthening of the hypothesis
  relative to the paper's sentence, and it is recorded as such in the inventory.
* The bound is primarily stated **additively** (`card K₀ + n ≤ |U|`). Natural
  subtraction truncates, so the additive form is the faithful one; the paper's
  literal `|U| - |K₀|` reading is derived from it as a corollary.

The iterates themselves are never required to be decidable. Only `K₀` is, which
is what lets the whole development stay constructive. -/

section Finiteness

variable {A : Type u}

/-- Duplicate-freeness, defined here rather than imported so that the counting
lemmas depend on nothing outside this file. -/
inductive Distinct : List A → Prop
  | nil : Distinct []
  | cons {x : A} {xs : List A} : ¬ x ∈ xs → Distinct xs → Distinct (x :: xs)

/-- Remove the first occurrence of `a`. -/
def dropOne [DecidableEq A] (a : A) : List A → List A
  | [] => []
  | x :: xs => if x = a then xs else x :: dropOne a xs

/-- Removing one occurrence of a member shortens the list by exactly one. -/
theorem length_dropOne [DecidableEq A] (a : A) :
    ∀ l : List A, a ∈ l → (dropOne a l).length + 1 = l.length := by
  intro l
  induction l with
  | nil => intro h; cases h
  | cons x xs ih =>
    intro h
    show (if x = a then xs else x :: dropOne a xs).length + 1 = xs.length + 1
    split
    · rfl
    · next hne =>
      have hmem : a ∈ xs := by
        cases h with
        | head => exact absurd rfl hne
        | tail _ h' => exact h'
      show (dropOne a xs).length + 1 + 1 = xs.length + 1
      rw [ih hmem]

/-- Removal keeps every other member. -/
theorem mem_dropOne [DecidableEq A] (a b : A) :
    ∀ l : List A, b ∈ l → ¬ b = a → b ∈ dropOne a l := by
  intro l
  induction l with
  | nil => intro h _; cases h
  | cons x xs ih =>
    intro h hne
    show b ∈ (if x = a then xs else x :: dropOne a xs)
    split
    · next hxa =>
      cases h with
      | head => exact absurd hxa hne
      | tail _ h' => exact h'
    · cases h with
      | head => exact List.Mem.head _
      | tail _ h' => exact List.Mem.tail _ (ih h' hne)

/-- **Pigeonhole.** A duplicate-free list contained in another list is no longer
than it. This is the sub-lemma the whole counting bound rests on. -/
theorem distinct_length_le [DecidableEq A] :
    ∀ (l m : List A), Distinct l → (∀ a ∈ l, a ∈ m) → l.length ≤ m.length := by
  intro l
  induction l with
  | nil => intro _ _ _; exact Nat.zero_le _
  | cons x xs ih =>
    intro m hd hsub
    cases hd with
    | cons hx hxs =>
      have hxm : x ∈ m := hsub x (List.Mem.head _)
      have hsub' : ∀ a ∈ xs, a ∈ dropOne x m := fun a ha =>
        mem_dropOne x a m (hsub a (List.Mem.tail _ ha)) (fun heq => hx (heq ▸ ha))
      have h1 : xs.length ≤ (dropOne x m).length := ih (dropOne x m) hxs hsub'
      have h2 : (dropOne x m).length + 1 = m.length := length_dropOne x m hxm
      show xs.length + 1 ≤ m.length
      rw [← h2]
      exact Nat.succ_le_succ h1

/-- Elements satisfying a decidable predicate, in order. -/
def keep (p : A → Bool) : List A → List A
  | [] => []
  | x :: xs => if p x then x :: keep p xs else keep p xs

/-- A member satisfying the predicate survives the filter. -/
theorem mem_keep (p : A → Bool) :
    ∀ (l : List A) (a : A), a ∈ l → p a = true → a ∈ keep p l := by
  intro l
  induction l with
  | nil => intro a h _; cases h
  | cons x xs ih =>
    intro a h hp
    show a ∈ (if p x then x :: keep p xs else keep p xs)
    cases h with
    | head =>
      rw [if_pos hp]
      exact List.Mem.head _
    | tail _ h' =>
      split
      · exact List.Mem.tail _ (ih a h' hp)
      · exact ih a h' hp

/-- A predicate and its negation partition the list. -/
theorem length_keep_add_not (p : A → Bool) :
    ∀ l : List A, (keep p l).length + (keep (fun a => !p a) l).length = l.length := by
  intro l
  induction l with
  | nil => rfl
  | cons x xs ih =>
    show (if p x then x :: keep p xs else keep p xs).length
        + (if !p x then x :: keep (fun a => !p a) xs else keep (fun a => !p a) xs).length
        = xs.length + 1
    cases hx : p x with
    | true =>
      show (keep p xs).length + 1 + (keep (fun a => !p a) xs).length = xs.length + 1
      rw [Nat.add_right_comm, ih]
    | false =>
      show (keep p xs).length + (keep (fun a => !p a) xs).length + 1 = xs.length + 1
      rw [ih]

/-- Every iterate stays inside the declared universe. -/
theorem iter_within_univ (F : Sub A → Sub A) (K₀ : Sub A) (univ : List A)
    (hK₀univ : ∀ a, K₀ a → a ∈ univ)
    (hFuniv : ∀ X : Sub A, (∀ a, X a → a ∈ univ) → ∀ a, F X a → a ∈ univ) :
    ∀ n a, Iter F K₀ n a → a ∈ univ := by
  intro n
  induction n with
  | zero => exact hK₀univ
  | succ k ih => exact hFuniv (Iter F K₀ k) ih

/-- The iteration is increasing in its index. Note this needs *only*
inflationarity, not monotonicity — matching the paper's own "Inflationarity gives
`K_n ⊆ K_{n+1}`", and worth keeping visible so the counting half is not silently
credited to a hypothesis it does not use. -/
theorem iter_index_monotone (F : Sub A → Sub A)
    (infl : ∀ X, X ⊑ F X) (K₀ : Sub A) :
    ∀ i j, i ≤ j → Iter F K₀ i ⊑ Iter F K₀ j := by
  intro i j
  induction j with
  | zero =>
    intro h
    have : i = 0 := Nat.eq_zero_of_le_zero h
    subst this
    exact Incl.refl _
  | succ k ih =>
    intro h
    rcases Nat.eq_or_lt_of_le h with heq | hlt
    · subst heq; exact Incl.refl _
    · exact Incl.trans (ih (Nat.le_of_lt_succ hlt)) (infl _)

/-- `witnesses w n = [w (n-1), …, w 0]`. -/
def witnesses (w : Nat → A) : Nat → List A
  | 0 => []
  | k + 1 => w k :: witnesses w k

theorem length_witnesses (w : Nat → A) : ∀ n, (witnesses w n).length = n := by
  intro n
  induction n with
  | zero => rfl
  | succ k ih => show (witnesses w k).length + 1 = k + 1; rw [ih]

theorem mem_witnesses (w : Nat → A) :
    ∀ n a, a ∈ witnesses w n → ∃ i, i < n ∧ w i = a := by
  intro n
  induction n with
  | zero => intro a h; cases h
  | succ k ih =>
    intro a h
    cases h with
    | head => exact ⟨k, Nat.lt_succ_self k, rfl⟩
    | tail _ h' =>
      rcases ih a h' with ⟨i, hi, hw⟩
      exact ⟨i, Nat.lt_succ_of_lt hi, hw⟩

/-- The elements added by distinct strict-growth steps are distinct. This is the
step the paper compresses into "every strict inclusion adds at least one
element": if `w i = w j` for `i < j` then the element added at step `i` is
already present at stage `j`, contradicting the fact that step `j` adds it. -/
theorem distinct_witnesses (F : Sub A → Sub A)
    (infl : ∀ X, X ⊑ F X)
    (K₀ : Sub A) (w : Nat → A) :
    ∀ n, (∀ i, i < n → Iter F K₀ (i + 1) (w i) ∧ ¬ Iter F K₀ i (w i)) →
      Distinct (witnesses w n) := by
  intro n
  induction n with
  | zero => intro _; exact Distinct.nil
  | succ k ih =>
    intro hw
    refine Distinct.cons ?_ (ih fun i hi => hw i (Nat.lt_succ_of_lt hi))
    intro hmem
    rcases mem_witnesses w k (w k) hmem with ⟨i, hi, hwi⟩
    have h1 : Iter F K₀ (i + 1) (w i) := (hw i (Nat.lt_succ_of_lt hi)).1
    have h2 : Iter F K₀ k (w i) := iter_index_monotone F infl K₀ (i + 1) k hi (w i) h1
    exact (hw k (Nat.lt_succ_self k)).2 (hwi ▸ h2)

/-- **Finite-basis saturation, cardinality bound.** `n` strict-growth steps force
`|K₀| + n ≤ |U|`, so there can be at most `|U| - |K₀|` of them. -/
theorem finite_basis_strict_growth_bound [DecidableEq A]
    (univ : List A) (_huniv : Distinct univ)
    (K₀ : Sub A) [DecidablePred K₀]
    (F : Sub A → Sub A)
    (infl : ∀ X, X ⊑ F X)
    (hK₀univ : ∀ a, K₀ a → a ∈ univ)
    (hFuniv : ∀ X : Sub A, (∀ a, X a → a ∈ univ) → ∀ a, F X a → a ∈ univ)
    (w : Nat → A) (n : Nat)
    (hw : ∀ i, i < n → Iter F K₀ (i + 1) (w i) ∧ ¬ Iter F K₀ i (w i)) :
    (keep (fun a => decide (K₀ a)) univ).length + n ≤ univ.length := by
  have hsub : ∀ a ∈ witnesses w n, a ∈ keep (fun a => !decide (K₀ a)) univ := by
    intro a ha
    rcases mem_witnesses w n a ha with ⟨i, hi, hwi⟩
    have hmemU : w i ∈ univ :=
      iter_within_univ F K₀ univ hK₀univ hFuniv (i + 1) (w i) (hw i hi).1
    have hnotK : ¬ K₀ (w i) := fun hk =>
      (hw i hi).2 (iter_index_monotone F infl K₀ 0 i (Nat.zero_le i) (w i) hk)
    have hb : (!decide (K₀ (w i))) = true := by
      rw [decide_eq_false hnotK]
      rfl
    exact hwi ▸ mem_keep _ univ (w i) hmemU hb
  have hle : (witnesses w n).length ≤ (keep (fun a => !decide (K₀ a)) univ).length :=
    distinct_length_le (witnesses w n) _
      (distinct_witnesses F infl K₀ w n hw) hsub
  rw [length_witnesses] at hle
  rw [← length_keep_add_not (fun a => decide (K₀ a)) univ]
  exact Nat.add_le_add_left hle _

/-- `n + k ≤ L → n ≤ L - k`, proved here rather than taken from core: the core
lemma `Nat.le_sub_of_add_le` depends on `propext`, which would show up in the
axiom report and break the development's central claim. -/
theorem le_sub_of_add_le : ∀ (k n L : Nat), n + k ≤ L → n ≤ L - k := by
  intro k
  induction k with
  | zero => intro _ _ h; exact h
  | succ j ih =>
    intro n L h
    cases L with
    | zero => exact absurd h (Nat.not_succ_le_zero _)
    | succ m =>
      have hs : (m + 1) - (j + 1) = m - j := Nat.succ_sub_succ m j
      rw [hs]
      exact ih n m (Nat.le_of_succ_le_succ h)

/-- The paper's literal `|U| - |K₀|` reading. Natural subtraction truncates, so
the additive statement above is the primary one and this is derived from it. -/
theorem finite_basis_strict_growth_bound_sub [DecidableEq A]
    (univ : List A) (huniv : Distinct univ)
    (K₀ : Sub A) [DecidablePred K₀]
    (F : Sub A → Sub A)
    (infl : ∀ X, X ⊑ F X)
    (hK₀univ : ∀ a, K₀ a → a ∈ univ)
    (hFuniv : ∀ X : Sub A, (∀ a, X a → a ∈ univ) → ∀ a, F X a → a ∈ univ)
    (w : Nat → A) (n : Nat)
    (hw : ∀ i, i < n → Iter F K₀ (i + 1) (w i) ∧ ¬ Iter F K₀ i (w i)) :
    n ≤ univ.length - (keep (fun a => decide (K₀ a)) univ).length := by
  have h := finite_basis_strict_growth_bound univ huniv K₀ F infl hK₀univ hFuniv w n hw
  rw [Nat.add_comm] at h
  exact le_sub_of_add_le _ n univ.length h

/-- Non-vacuity: the bound is attained, so it is not an idle inequality. Over a
one-element universe with `K₀` empty, exactly one strict-growth step is possible
and the bound reads `0 + 1 ≤ 1`. -/
theorem finite_basis_bound_is_attained :
    (keep (fun a => decide ((fun _ => False) a)) [()]).length + 1 = ([()] : List Unit).length :=
  rfl

end Finiteness

/-! ## Ingredients of: Optimality of reservation-first greedy selection

Paper I, `03_workspace.tex:48`.

**This section does NOT prove the theorem.** It proves three ingredients its
proof uses — the exchange step (`sum_swap_ge`), the existence of a swap partner
(`exchange_partner_exists`), and top-`k` optimality (`top_subset_optimal`). The
assembly — iterating the exchange across reserved partitions while carrying
feasibility, then splitting the objective across the reserved/fill boundary — is
not mechanized, so no part of the optimality *statement* is machine-checked here.
The claim accordingly stays `PAPER_PROOF_COMPLETE` in the inventory rather than
being upgraded on the strength of its lemmas.

Utilities are `Nat`. That is a real restriction and is recorded in the inventory
rather than glossed: the paper states `u_i ≥ 0` over the reals. `Nat` supplies
non-negativity — assumption (iii) — for free, and the argument below uses only
`+`, `≤`, transitivity and `add_le_add`, so nothing depends on `Nat` beyond
those. The statement as mechanized is nonetheless a special case.

"The top `r_p` candidates" is not well defined under utility ties, and the
implementation picks *some* tie-broken set. `IsTopSubset` therefore quantifies
over **any** maximal `k`-subset rather than a unique one. That is the precision
point recorded against the paper's statement. -/

section Greedy

variable {I : Type u}

/-- Additive utility of a selection — assumption (iii), and unit costs are the
fact that each member contributes exactly one term. -/
def sumU (u : I → Nat) : List I → Nat
  | [] => 0
  | x :: xs => u x + sumU u xs

/-- Boolean membership. Defined here because core's `List.elem`/`Mem` bridge
depends on `propext`, which the axiom audit forbids. -/
def memB [DecidableEq I] (a : I) : List I → Bool
  | [] => false
  | x :: xs => if x = a then true else memB a xs

theorem mem_of_memB [DecidableEq I] (a : I) : ∀ l : List I, memB a l = true → a ∈ l := by
  intro l
  induction l with
  | nil => intro h; exact Bool.noConfusion h
  | cons x xs ih =>
    intro h
    revert h
    show (if x = a then true else memB a xs) = true → a ∈ x :: xs
    split
    · next heq => intro _; exact heq ▸ List.Mem.head _
    · intro h; exact List.Mem.tail _ (ih h)

theorem memB_of_mem [DecidableEq I] (a : I) : ∀ l : List I, a ∈ l → memB a l = true := by
  intro l
  induction l with
  | nil => intro h; cases h
  | cons x xs ih =>
    intro h
    show (if x = a then true else memB a xs) = true
    split
    · rfl
    · next hne =>
      cases h with
      | head => exact absurd rfl hne
      | tail _ h' => exact ih h'

/-- Removing a member and adding back its utility recovers the original sum. -/
theorem sumU_dropOne [DecidableEq I] (u : I → Nat) :
    ∀ (l : List I) (j : I), j ∈ l → u j + sumU u (dropOne j l) = sumU u l := by
  intro l
  induction l with
  | nil => intro j h; cases h
  | cons x xs ih =>
    intro j h
    show u j + sumU u (if x = j then xs else x :: dropOne j xs) = u x + sumU u xs
    split
    · next heq => rw [heq]
    · next hne =>
      have hmem : j ∈ xs := by
        cases h with
        | head => exact absurd rfl hne
        | tail _ h' => exact h'
      show u j + (u x + sumU u (dropOne j xs)) = u x + sumU u xs
      rw [← ih j hmem, ← Nat.add_assoc, ← Nat.add_assoc, Nat.add_comm (u j) (u x)]

/-- **The exchange step.** Swapping a selected `j` for an unselected `i` of at
least equal utility never decreases the objective. This is the single move the
paper's first stage iterates. -/
theorem sum_swap_ge [DecidableEq I] (u : I → Nat) (sel : List I) (i j : I)
    (hj : j ∈ sel) (hle : u j ≤ u i) :
    sumU u sel ≤ sumU u (i :: dropOne j sel) := by
  show sumU u sel ≤ u i + sumU u (dropOne j sel)
  rw [← sumU_dropOne u sel j hj]
  exact Nat.add_le_add_right hle _

/-- A predicate and its negation split the utility of a selection. -/
theorem sumU_keep_split (u : I → Nat) (q : I → Bool) :
    ∀ l : List I, sumU u (keep q l) + sumU u (keep (fun a => !q a) l) = sumU u l := by
  intro l
  induction l with
  | nil => rfl
  | cons x xs ih =>
    show sumU u (if q x then x :: keep q xs else keep q xs)
        + sumU u (if !q x then x :: keep (fun a => !q a) xs else keep (fun a => !q a) xs)
        = u x + sumU u xs
    cases hx : q x with
    | true =>
      show u x + sumU u (keep q xs) + sumU u (keep (fun a => !q a) xs) = u x + sumU u xs
      rw [Nat.add_assoc, ih]
    | false =>
      show sumU u (keep q xs) + (u x + sumU u (keep (fun a => !q a) xs)) = u x + sumU u xs
      rw [← Nat.add_assoc, Nat.add_comm (sumU u (keep q xs)) (u x), Nat.add_assoc, ih]

theorem mem_of_mem_dropOne [DecidableEq I] (a b : I) :
    ∀ l : List I, b ∈ dropOne a l → b ∈ l := by
  intro l
  induction l with
  | nil => intro h; cases h
  | cons x xs ih =>
    intro h
    revert h
    show b ∈ (if x = a then xs else x :: dropOne a xs) → b ∈ x :: xs
    split
    · intro h; exact List.Mem.tail _ h
    · intro h
      cases h with
      | head => exact List.Mem.head _
      | tail _ h' => exact List.Mem.tail _ (ih h')

theorem distinct_dropOne [DecidableEq I] (a : I) :
    ∀ l : List I, Distinct l → Distinct (dropOne a l) := by
  intro l
  induction l with
  | nil => intro _; exact Distinct.nil
  | cons x xs ih =>
    intro hd
    cases hd with
    | cons hx hxs =>
      show Distinct (if x = a then xs else x :: dropOne a xs)
      split
      · exact hxs
      · exact Distinct.cons (fun hmem => hx (mem_of_mem_dropOne a x xs hmem)) (ih hxs)

theorem not_mem_dropOne_self [DecidableEq I] (a : I) :
    ∀ l : List I, Distinct l → ¬ a ∈ dropOne a l := by
  intro l
  induction l with
  | nil => intro _ h; cases h
  | cons x xs ih =>
    intro hd
    cases hd with
    | cons hx hxs =>
      show ¬ a ∈ (if x = a then xs else x :: dropOne a xs)
      split
      · next heq => exact heq ▸ hx
      · next hne =>
        intro hmem
        cases hmem with
        | head => exact hne rfl
        | tail _ h' => exact ih hxs h'

/-- Utility depends only on the *set* of selected items, not on their order.
Needed because the greedy output and a competing selection agree as sets on
their shared part but not as lists. -/
theorem sumU_congr_mem [DecidableEq I] (u : I → Nat) :
    ∀ (l m : List I), Distinct l → Distinct m → (∀ a, a ∈ l ↔ a ∈ m) →
      sumU u l = sumU u m := by
  intro l
  induction l with
  | nil =>
    intro m _ _ hiff
    cases m with
    | nil => rfl
    | cons y ys => cases (hiff y).mpr (List.Mem.head _)
  | cons x xs ih =>
    intro m hdl hdm hiff
    cases hdl with
    | cons hx hxs =>
      have hxm : x ∈ m := (hiff x).mp (List.Mem.head _)
      have hiff' : ∀ a, a ∈ xs ↔ a ∈ dropOne x m := by
        intro a
        constructor
        · intro ha
          exact mem_dropOne x a m ((hiff a).mp (List.Mem.tail _ ha)) (fun heq => hx (heq ▸ ha))
        · intro ha
          have ham : a ∈ m := mem_of_mem_dropOne x a m ha
          cases (hiff a).mpr ham with
          | head => exact absurd ha (not_mem_dropOne_self _ m hdm)
          | tail _ h' => exact h'
      have heq : sumU u xs = sumU u (dropOne x m) :=
        ih (dropOne x m) hxs (distinct_dropOne x m hdm) hiff'
      show u x + sumU u xs = sumU u m
      rw [heq]
      exact sumU_dropOne u m x hxm

theorem mem_of_mem_keep (q : I → Bool) :
    ∀ (l : List I) (a : I), a ∈ keep q l → a ∈ l ∧ q a = true := by
  intro l
  induction l with
  | nil => intro a h; cases h
  | cons x xs ih =>
    intro a h
    revert h
    show a ∈ (if q x then x :: keep q xs else keep q xs) → a ∈ x :: xs ∧ q a = true
    split
    · next hqx =>
      intro h
      cases h with
      | head => exact ⟨List.Mem.head _, hqx⟩
      | tail _ h' => exact ⟨List.Mem.tail _ (ih a h').1, (ih a h').2⟩
    · intro h
      exact ⟨List.Mem.tail _ (ih a h).1, (ih a h).2⟩

theorem distinct_keep (q : I → Bool) : ∀ l : List I, Distinct l → Distinct (keep q l) := by
  intro l
  induction l with
  | nil => intro _; exact Distinct.nil
  | cons x xs ih =>
    intro hd
    cases hd with
    | cons hx hxs =>
      show Distinct (if q x then x :: keep q xs else keep q xs)
      split
      · exact Distinct.cons (fun hmem => hx (mem_of_mem_keep q xs x hmem).1) (ih hxs)
      · exact ih hxs

/-- Duplicate-free lists with the same members have the same length. -/
theorem length_congr_mem [DecidableEq I] (l m : List I)
    (hdl : Distinct l) (hdm : Distinct m) (hiff : ∀ a, a ∈ l ↔ a ∈ m) :
    l.length = m.length :=
  Nat.le_antisymm
    (distinct_length_le l m hdl (fun a ha => (hiff a).mp ha))
    (distinct_length_le m l hdm (fun a ha => (hiff a).mpr ha))

/-- If every member of `X` is dominated by every member of `Y` and `Y` is at
least as long, then `X` is worth no more. Non-negativity is what lets the extra
slots of `Y` only help — this is where assumption (iii) does its work. -/
theorem sum_le_of_pointwise_dominated (u : I → Nat) :
    ∀ (X Y : List I), X.length ≤ Y.length → (∀ a ∈ X, ∀ b ∈ Y, u a ≤ u b) →
      sumU u X ≤ sumU u Y := by
  intro X
  induction X with
  | nil => intro _ _ _; exact Nat.zero_le _
  | cons x xs ih =>
    intro Y hlen hdom
    cases Y with
    | nil => exact absurd hlen (Nat.not_succ_le_zero _)
    | cons y ys =>
      have h1 : u x ≤ u y := hdom x (List.Mem.head _) y (List.Mem.head _)
      have h2 : sumU u xs ≤ sumU u ys :=
        ih ys (Nat.le_of_succ_le_succ hlen)
          (fun a ha b hb => hdom a (List.Mem.tail _ ha) b (List.Mem.tail _ hb))
      show u x + sumU u xs ≤ u y + sumU u ys
      exact Nat.add_le_add h1 h2

/-- Cancellation on the right. Proved here because core's
`Nat.le_of_add_le_add_left` and `Nat.le_of_add_le_add_right` both depend on
`propext` — the third such leak the axiom audit has caught in this development. -/
theorem le_of_add_le_add_right : ∀ (a b c : Nat), b + a ≤ c + a → b ≤ c := by
  intro a
  induction a with
  | zero => intro _ _ h; exact h
  | succ k ih => intro b c h; exact ih b c (Nat.le_of_succ_le_succ h)

/-- A maximal `k`-element selection of `q`-eligible pool members: every eligible
candidate left out is worth no more than every one taken.

This is the **tie-safe** reading of "the top `k`". It quantifies over any maximal
subset rather than a unique one, and — crucially for the reserved stage —
maximality is relative to the eligibility predicate `q`, not to the whole pool.
Whole-pool maximality would be false for a reserved partition, since a reserved
item may be worth less than an unselected item of another partition. -/
structure IsTopSubset (u : I → Nat) (q : I → Bool) (pool sel : List I) (k : Nat) : Prop where
  distinct : Distinct sel
  inPool : ∀ i ∈ sel, i ∈ pool
  eligible : ∀ i ∈ sel, q i = true
  card : sel.length = k
  maximal : ∀ a ∈ pool, q a = true → ¬ a ∈ sel → ∀ b ∈ sel, u a ≤ u b

/-- **Top-`k` optimality.** Any admissible selection of at most `k` eligible
candidates is worth no more than a maximal `k`-subset.

Applied to the whole eligible pool this is the paper's second stage — the
residual, once every lower bound is already met, is ordinary top-`k`. Applied per
partition it is what the first-stage exchange establishes: the reserved slots of
a partition may be taken by that partition's top `r_p`. -/
theorem top_subset_optimal [DecidableEq I]
    (u : I → Nat) (q : I → Bool) (pool sel cand : List I) (k : Nat)
    (htop : IsTopSubset u q pool sel k)
    (hcd : Distinct cand) (hcp : ∀ i ∈ cand, i ∈ pool) (hce : ∀ i ∈ cand, q i = true)
    (hck : cand.length ≤ k) :
    sumU u cand ≤ sumU u sel := by
  have hb1t1 : ∀ a, a ∈ keep (fun i => memB i sel) cand ↔ a ∈ keep (fun i => memB i cand) sel := by
    intro a
    constructor
    · intro ha
      have h := mem_of_mem_keep _ cand a ha
      exact mem_keep _ sel a (mem_of_memB a sel h.2) (memB_of_mem a cand h.1)
    · intro ha
      have h := mem_of_mem_keep _ sel a ha
      exact mem_keep _ cand a (mem_of_memB a cand h.2) (memB_of_mem a sel h.1)
  have hsum1 : sumU u (keep (fun i => memB i sel) cand)
      = sumU u (keep (fun i => memB i cand) sel) :=
    sumU_congr_mem u _ _ (distinct_keep _ cand hcd) (distinct_keep _ sel htop.distinct) hb1t1
  have hlen1 : (keep (fun i => memB i sel) cand).length
      = (keep (fun i => memB i cand) sel).length :=
    length_congr_mem _ _ (distinct_keep _ cand hcd) (distinct_keep _ sel htop.distinct) hb1t1
  have hlen2 : (keep (fun i => !memB i sel) cand).length
      ≤ (keep (fun i => !memB i cand) sel).length := by
    have hc := length_keep_add_not (fun i => memB i sel) cand
    have hs := length_keep_add_not (fun i => memB i cand) sel
    have key : (keep (fun i => memB i sel) cand).length
             + (keep (fun i => !memB i sel) cand).length
           ≤ (keep (fun i => memB i cand) sel).length
             + (keep (fun i => !memB i cand) sel).length := by
      rw [hc, hs, htop.card]
      exact hck
    rw [hlen1] at key
    rw [Nat.add_comm (keep (fun i => memB i cand) sel).length
          (keep (fun i => !memB i sel) cand).length] at key
    rw [Nat.add_comm (keep (fun i => memB i cand) sel).length
          (keep (fun i => !memB i cand) sel).length] at key
    exact le_of_add_le_add_right _ _ _ key
  have hdom : sumU u (keep (fun i => !memB i sel) cand)
      ≤ sumU u (keep (fun i => !memB i cand) sel) := by
    refine sum_le_of_pointwise_dominated u _ _ hlen2 ?_
    intro a ha b hb
    have ha' := mem_of_mem_keep _ cand a ha
    have hb' := mem_of_mem_keep _ sel b hb
    refine htop.maximal a (hcp a ha'.1) (hce a ha'.1) ?_ b hb'.1
    intro hmem
    have : memB a sel = true := memB_of_mem a sel hmem
    rw [this] at ha'
    exact Bool.noConfusion ha'.2
  have hc := sumU_keep_split u (fun i => memB i sel) cand
  have hs := sumU_keep_split u (fun i => memB i cand) sel
  rw [← hc, ← hs, hsum1]
  exact Nat.add_le_add_left hdom _

/-- Either a list is contained in `T`, or it exhibits a member outside `T`.
Decided rather than assumed: `memB` keeps this constructive, where the usual
"not a subset, therefore there exists a counterexample" step would need
classical logic. -/
theorem subset_or_witness [DecidableEq I] (T : List I) :
    ∀ l : List I, (∀ j ∈ l, j ∈ T) ∨ (∃ j, j ∈ l ∧ ¬ j ∈ T) := by
  intro l
  induction l with
  | nil => exact Or.inl (fun j hj => nomatch hj)
  | cons x xs ih =>
    cases hx : memB x T with
    | false =>
      refine Or.inr ⟨x, List.Mem.head _, ?_⟩
      intro hc
      rw [memB_of_mem x T hc] at hx
      exact Bool.noConfusion hx
    | true =>
      cases ih with
      | inl hsub =>
        refine Or.inl (fun j hj => ?_)
        cases hj with
        | head => exact mem_of_memB x T hx
        | tail _ h' => exact hsub j h'
      | inr hw =>
        rcases hw with ⟨j, hj, hnj⟩
        exact Or.inr ⟨j, List.Mem.tail _ hj, hnj⟩

/-- A duplicate-free list contained in a no-longer list exhausts it. -/
theorem distinct_subset_exhausts [DecidableEq I] (l m : List I)
    (hdl : Distinct l) (hsub : ∀ a ∈ l, a ∈ m) (hcard : m.length ≤ l.length) :
    ∀ a ∈ m, a ∈ l := by
  intro a ha
  cases hmb : memB a l with
  | true => exact mem_of_memB a l hmb
  | false =>
    exfalso
    have hnl : ¬ a ∈ l := by
      intro hc
      rw [memB_of_mem a l hc] at hmb
      exact Bool.noConfusion hmb
    have hsub' : ∀ b ∈ l, b ∈ dropOne a m := fun b hb =>
      mem_dropOne a b m (hsub b hb) (fun heq => hnl (heq ▸ hb))
    have h1 : l.length ≤ (dropOne a m).length := distinct_length_le l _ hdl hsub'
    have h2 : (dropOne a m).length + 1 = m.length := length_dropOne a m ha
    have h3 : l.length + 1 ≤ m.length := by rw [← h2]; exact Nat.succ_le_succ h1
    exact Nat.not_succ_le_self l.length (Nat.le_trans h3 hcard)

/-- **The swap partner always exists.** This is the counting step the paper
compresses into "suppose `S*` contains a reserved-slot candidate `j` whose
utility is lower than an unselected candidate `i`". If the selection already
meets partition `p`'s reservation but misses one of `p`'s top `r_p` candidates,
then it must contain some candidate of `p` outside that top set — which is
precisely the element the exchange swaps out.

Without this the exchange argument would be an assertion that a swap partner is
available; here its availability is derived from feasibility. -/
theorem exchange_partner_exists [DecidableEq I]
    (top selp : List I) (hsel : Distinct selp)
    (hcard : top.length ≤ selp.length)
    (i : I) (hitop : i ∈ top) (hisel : ¬ i ∈ selp) :
    ∃ j, j ∈ selp ∧ ¬ j ∈ top := by
  rcases subset_or_witness top selp with hsub | hw
  · exact absurd (distinct_subset_exhausts selp top hsel hsub hcard i hitop) hisel
  · exact hw

end Greedy

end RaklFormal
