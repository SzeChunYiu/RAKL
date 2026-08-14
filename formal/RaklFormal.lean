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

universe u v w

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

end RaklFormal
