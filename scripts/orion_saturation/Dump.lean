/-
Extract a premise corpus and a candidate task population from a frozen set of
Mathlib modules.

Everything here is read out of the Lean environment rather than parsed from
source, so the premise corpus, the goal statements and the "gold" premise sets
are all produced by Lean itself and none of them are authored by ORION.

  * corpus  : every non-internal theorem reachable in the environment, recorded
              as its name plus the set of constants occurring in its *type*.
              This is the retrieval index.
  * pop     : candidate tasks, restricted to the frozen target modules. Each
              records the pretty-printed statement (used to restate the goal)
              and the constants occurring in the original *proof term*, which
              serve only as the mediating coverage coordinate — never as a
              retrieval input.
-/
import Mathlib.Data.List.Basic
import Mathlib.Data.Nat.Defs
import Mathlib.Data.Set.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.Group.Basic
import Mathlib.Logic.Basic

open Lean Elab Command Meta

/-- Constants occurring in an expression. -/
def exprConsts (e : Expr) : List Name :=
  (e.foldConsts ({} : NameSet) (fun n s => s.insert n)).toList

/-- The frozen population modules. Declared here so the freeze is in-repo. -/
def targetModules : List Name :=
  [`Mathlib.Data.List.Basic,
   `Mathlib.Data.Nat.Defs,
   `Mathlib.Data.Set.Basic,
   `Mathlib.Data.Finset.Basic,
   `Mathlib.Algebra.Group.Basic,
   `Mathlib.Logic.Basic]

elab "dump_all " corpusPath:str popPath:str : command => do
  let env ← getEnv
  let mods := env.header.moduleNames
  let mut corpus : Array String := #[]
  let mut pop : Array String := #[]
  let mut nPop := 0
  for (name, ci) in env.constants.toList do
    match ci with
    | .thmInfo ti =>
      if name.isInternal then continue
      let tyConsts := (exprConsts ti.type).map (·.toString)
      corpus := corpus.push <|
        (Json.mkObj [("name", Json.str name.toString),
                     ("ty", Json.arr ((tyConsts.map Json.str).toArray))]).compress
      match env.getModuleIdxFor? name with
      | some idx =>
        let m := mods[idx.toNat]!
        if targetModules.contains m then
          let ppStmt ← liftTermElabM do
            let f ← PrettyPrinter.ppExpr ti.type
            pure f.pretty
          let goldConsts := (exprConsts ti.value).map (·.toString)
          pop := pop.push <|
            (Json.mkObj [("name", Json.str name.toString),
                         ("module", Json.str m.toString),
                         ("stmt", Json.str ppStmt),
                         ("gold", Json.arr ((goldConsts.map Json.str).toArray))]).compress
          nPop := nPop + 1
      | none => pure ()
    | _ => pure ()
  IO.FS.writeFile corpusPath.getString (String.intercalate "\n" corpus.toList)
  IO.FS.writeFile popPath.getString (String.intercalate "\n" pop.toList)
  logInfo s!"corpus={corpus.size} pop={nPop}"

dump_all "/home/billy/orion-lean/corpus.jsonl" "/home/billy/orion-lean/population_raw.jsonl"
