import RaklFormal

namespace RaklFormal

universe u
variable {I : Type u}

def ReservationExchange [DecidableEq I]
    (u : I → Nat) (mandatory : List I) (feasible : List I → Prop) : Prop :=
  ∀ sel : List I, Distinct sel → feasible sel →
    ∀ i : I, i ∈ mandatory → ¬ i ∈ sel →
      ∃ j : I, j ∈ sel ∧ ¬ j ∈ mandatory ∧ u j ≤ u i ∧
        feasible (i :: dropOne j sel)

theorem not_mem_dropOne_of_not_mem [DecidableEq I] (a j : I) (l : List I)
    (ha : ¬ a ∈ l) : ¬ a ∈ dropOne j l := by
  intro h
  exact ha (mem_of_mem_dropOne j a l h)

theorem length_swapIn [DecidableEq I] (i j : I) (l : List I) (hj : j ∈ l) :
    (i :: dropOne j l).length = l.length := by
  show (dropOne j l).length + 1 = l.length
  exact length_dropOne j l hj

theorem mandatory_mem_survives_swap [DecidableEq I]
    (mandatory sel : List I) (i j a : I)
    (haM : a ∈ mandatory) (haS : a ∈ sel) (hjM : ¬ j ∈ mandatory) :
    a ∈ i :: dropOne j sel := by
  have hne : a ≠ j := by
    intro h
    exact hjM (h ▸ haM)
  exact List.Mem.tail _ (mem_dropOne j a sel haS hne)

theorem normalize_reservations [DecidableEq I]
    (u : I → Nat) (allMandatory : List I) (feasible : List I → Prop)
    (hex : ReservationExchange u allMandatory feasible) :
    ∀ (todo sel : List I),
      (∀ i ∈ todo, i ∈ allMandatory) →
      Distinct sel → feasible sel →
      ∃ norm : List I,
        Distinct norm ∧ feasible norm ∧
        (∀ i ∈ todo, i ∈ norm) ∧
        (∀ a ∈ allMandatory, a ∈ sel → a ∈ norm) ∧
        sumU u sel ≤ sumU u norm ∧
        norm.length = sel.length := by
  intro todo
  induction todo with
  | nil =>
      intro sel _ hd hf
      exact ⟨sel, hd, hf, (fun i hi => nomatch hi),
        (fun _ _ h => h), Nat.le_refl _, rfl⟩
  | cons i rest ih =>
      intro sel htodo hd hf
      have hiM : i ∈ allMandatory := htodo i (List.Mem.head _)
      have hrestM : ∀ a ∈ rest, a ∈ allMandatory := by
        intro a ha
        exact htodo a (List.Mem.tail _ ha)
      cases hb : memB i sel with
      | true =>
          have hiS : i ∈ sel := mem_of_memB i sel hb
          rcases ih sel hrestM hd hf with ⟨norm, hdn, hfn, hrest, hpres, hsum, hlen⟩
          refine ⟨norm, hdn, hfn, ?_, hpres, hsum, hlen⟩
          intro a ha
          cases ha with
          | head => exact hpres i hiM hiS
          | tail _ h => exact hrest a h
      | false =>
          have hiS : ¬ i ∈ sel := by
            intro h
            rw [memB_of_mem i sel h] at hb
            exact Bool.noConfusion hb
          rcases hex sel hd hf i hiM hiS with ⟨j, hjS, hjM, hji, hswapF⟩
          let swapped := i :: dropOne j sel
          have hswapD : Distinct swapped := by
            exact Distinct.cons (not_mem_dropOne_of_not_mem i j sel hiS) (distinct_dropOne j sel hd)
          have hswapSum : sumU u sel ≤ sumU u swapped := sum_swap_ge u sel i j hjS hji
          have hswapLen : swapped.length = sel.length := length_swapIn i j sel hjS
          rcases ih swapped hrestM hswapD hswapF with
            ⟨norm, hdn, hfn, hrest, hpresSwap, hsum2, hlen2⟩
          have hiSwap : i ∈ swapped := List.Mem.head _
          refine ⟨norm, hdn, hfn, ?_, ?_, Nat.le_trans hswapSum hsum2, ?_⟩
          · intro a ha
            cases ha with
            | head => exact hpresSwap i hiM hiSwap
            | tail _ h => exact hrest a h
          · intro a haM haS
            exact hpresSwap a haM (mandatory_mem_survives_swap allMandatory sel i j a haM haS hjM)
          · exact hlen2.trans hswapLen

theorem sumU_append (u : I → Nat) :
    ∀ (a b : List I), sumU u (a ++ b) = sumU u a + sumU u b := by
  intro a
  induction a with
  | nil =>
      intro b
      show sumU u b = 0 + sumU u b
      exact (Nat.zero_add _).symm
  | cons x xs ih =>
      intro b
      show u x + sumU u (xs ++ b) = (u x + sumU u xs) + sumU u b
      rw [ih, Nat.add_assoc]

theorem mandatory_projection_members [DecidableEq I]
    (mandatory norm : List I)
    (hcontains : ∀ a ∈ mandatory, a ∈ norm) :
    ∀ a : I, a ∈ keep (fun x => memB x mandatory) norm ↔ a ∈ mandatory := by
  intro a
  constructor
  · intro h
    have hm := (mem_of_mem_keep (fun x => memB x mandatory) norm a h).2
    exact mem_of_memB a mandatory hm
  · intro h
    exact mem_keep _ norm a (hcontains a h) (memB_of_mem a mandatory h)

theorem residual_in_pool [DecidableEq I]
    (mandatory pool norm : List I) (hin : ∀ a ∈ norm, a ∈ pool) :
    ∀ a ∈ keep (fun x => !memB x mandatory) norm, a ∈ pool := by
  intro a ha
  exact hin a (mem_of_mem_keep _ norm a ha).1

theorem residual_eligible [DecidableEq I]
    (mandatory norm : List I) :
    ∀ a ∈ keep (fun x => !memB x mandatory) norm,
      (!memB a mandatory) = true := by
  intro a ha
  exact (mem_of_mem_keep _ norm a ha).2

/-- Machine-checked assembly of reservation-first greedy optimality for the
non-negative natural-valued case.  `ReservationExchange` is the explicit
operational consequence of disjoint reserved partitions and lower-bound
feasibility; `IsTopSubset` is the tie-safe global fill certificate. -/
theorem reservation_first_greedy_optimal [DecidableEq I]
    (u : I → Nat) (pool mandatory fill cand : List I) (k : Nat)
    (feasible : List I → Prop)
    (hMandD : Distinct mandatory)
    (hFillTop : IsTopSubset u (fun x => !memB x mandatory) pool fill k)
    (hCandD : Distinct cand) (_hCandPool : ∀ a ∈ cand, a ∈ pool)
    (hCandFeasible : feasible cand)
    (hFeasiblePool : ∀ sel : List I, feasible sel → ∀ a ∈ sel, a ∈ pool)
    (hCapacity : cand.length ≤ mandatory.length + k)
    (hExchange : ReservationExchange u mandatory feasible) :
    sumU u cand ≤ sumU u (mandatory ++ fill) := by
  rcases normalize_reservations u mandatory feasible hExchange mandatory cand
      (fun _ h => h) hCandD hCandFeasible with
    ⟨norm, hNormD, hNormF, hContains, _hPres, hCandNorm, hNormLen⟩
  let mandPart := keep (fun x => memB x mandatory) norm
  let resPart := keep (fun x => !memB x mandatory) norm
  have hMandMem : ∀ a : I, a ∈ mandPart ↔ a ∈ mandatory :=
    mandatory_projection_members mandatory norm hContains
  have hMandSum : sumU u mandPart = sumU u mandatory :=
    sumU_congr_mem u mandPart mandatory
      (distinct_keep _ norm hNormD) hMandD hMandMem
  have hMandLen : mandPart.length = mandatory.length :=
    length_congr_mem mandPart mandatory
      (distinct_keep _ norm hNormD) hMandD hMandMem
  have hResLen : resPart.length ≤ k := by
    have hsplit := length_keep_add_not (fun x => memB x mandatory) norm
    have hcapNorm : norm.length ≤ mandatory.length + k := by
      rw [hNormLen]
      exact hCapacity
    have hkey : mandPart.length + resPart.length ≤ mandatory.length + k := by
      exact hsplit.symm ▸ hcapNorm
    rw [hMandLen] at hkey
    rw [Nat.add_comm mandatory.length resPart.length, Nat.add_comm mandatory.length k] at hkey
    exact le_of_add_le_add_right mandatory.length _ _ hkey
  have hResOpt : sumU u resPart ≤ sumU u fill :=
    top_subset_optimal u (fun x => !memB x mandatory) pool fill resPart k
      hFillTop (distinct_keep _ norm hNormD)
      (residual_in_pool mandatory pool norm (hFeasiblePool norm hNormF))
      (residual_eligible mandatory norm) hResLen
  have hsplitU := sumU_keep_split u (fun x => memB x mandatory) norm
  have hNormGreedy : sumU u norm ≤ sumU u (mandatory ++ fill) := by
    rw [← hsplitU, hMandSum, sumU_append]
    exact Nat.add_le_add_left hResOpt _
  exact Nat.le_trans hCandNorm hNormGreedy

end RaklFormal
