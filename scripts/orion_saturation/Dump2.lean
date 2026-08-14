/-
Revival extraction (DESIGN-ITERATION-2).

Identical in kind to Dump.lean; the only change is the frozen module basis,
widened from six named modules to four Mathlib top-level areas. The lever is
population size — the v1 study attributed its null to power (11 discordant pairs
at n=112), not to the mechanism. Nothing about the arms, the retrieval routes,
the premise budget or the decision rule changes.
-/
import Mathlib

open Lean Elab Command Meta

def exprConsts (e : Expr) : List Name :=
  (e.foldConsts ({} : NameSet) (fun n s => s.insert n)).toList

/-- Frozen area basis for the revival run. -/
def targetPrefixes : List Name :=
  [`Mathlib.Data, `Mathlib.Order, `Mathlib.Algebra, `Mathlib.Logic]

def inTarget (m : Name) : Bool :=
  targetPrefixes.any (fun p => p.isPrefixOf m)

elab "dump2 " corpusPath:str popPath:str : command => do
  let env ← getEnv
  let mods := env.header.moduleNames
  let mut corpus : Array String := #[]
  let mut pop : Array String := #[]
  for (name, ci) in env.constants.toList do
    match ci with
    | .thmInfo ti =>
      if name.isInternal then continue
      match env.getModuleIdxFor? name with
      | some idx =>
        match mods[idx.toNat]? with
        | none => pure ()
        | some m =>
          if !inTarget m then continue
          let tyConsts := (exprConsts ti.type).map (·.toString)
          corpus := corpus.push <|
            (Json.mkObj [("name", Json.str name.toString),
                         ("ty", Json.arr ((tyConsts.map Json.str).toArray))]).compress
          -- Only small-support theorems are candidate tasks. Pretty-printing can
          -- throw on exotic declarations; such a declaration is skipped rather
          -- than allowed to abort the extraction.
          let goldConsts := (exprConsts ti.value).map (·.toString)
          if goldConsts.length ≤ 40 then
            let ppStmt? ← (do
              let s ← liftTermElabM do
                let f ← PrettyPrinter.ppExpr ti.type
                pure f.pretty
              pure (some s)) <|> pure none
            match ppStmt? with
            | none => pure ()
            | some ppStmt =>
              if ppStmt.length ≤ 400 && !ppStmt.isEmpty then
                pop := pop.push <|
                  (Json.mkObj [("name", Json.str name.toString),
                               ("module", Json.str m.toString),
                               ("stmt", Json.str ppStmt),
                               ("gold", Json.arr ((goldConsts.map Json.str).toArray))]).compress
      | none => pure ()
    | _ => pure ()
  IO.FS.writeFile corpusPath.getString (String.intercalate "\n" corpus.toList)
  IO.FS.writeFile popPath.getString (String.intercalate "\n" pop.toList)
  logInfo s!"corpus={corpus.size} pop={pop.size}"

dump2 "/home/billy/orion-lean/corpus2.jsonl" "/home/billy/orion-lean/population_raw2.jsonl"
