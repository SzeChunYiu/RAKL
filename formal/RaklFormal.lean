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

Paper I, `04_owmd.tex:162`. The least-fixed-point half is mechanized here. The
cardinality bound (`at most |U| - |K₀|` strict-growth steps) is *not* mechanized —
it needs a finiteness/cardinality development — and is recorded as such in the
inventory rather than being claimed. -/
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

end RaklFormal
