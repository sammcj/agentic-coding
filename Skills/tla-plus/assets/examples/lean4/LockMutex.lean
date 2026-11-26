/-
The Lean 4 half of LockMutex.tla.  No Mathlib: core Lean only.

Correspondence with the TLA+ module:

  TLA+                                Lean 4
  ----------------------------------  ------------------------------------
  VARIABLES lock, pc                  structure State
  lock = NoProc                       lock = none        (Option Proc)
  state predicate  Init, Inv          State Proc → Prop
  action  Acquire(p), Next            State Proc → State Proc → Prop
  pc' = [pc EXCEPT ![p] = "crit"]     s'.pc = fun q => if q = p then .crit else s.pc q
  Spec == Init /\ [][Next]_vars       inductive Reachable
  Spec => []P                         ∀ s, Reachable s → P s
  TypeOK                              (discharged by the type checker)
-/
namespace LockMutex

inductive PC where
  | idle
  | crit
  deriving DecidableEq, Repr

structure State (Proc : Type) where
  lock : Option Proc
  pc : Proc → PC

variable {Proc : Type} [DecidableEq Proc]

def Init (s : State Proc) : Prop :=
  s.lock = none ∧ ∀ p, s.pc p = PC.idle

def Acquire (p : Proc) (s s' : State Proc) : Prop :=
  s.lock = none ∧ s.pc p = PC.idle ∧
  s'.lock = some p ∧ s'.pc = fun q => if q = p then PC.crit else s.pc q

def Release (p : Proc) (s s' : State Proc) : Prop :=
  s.pc p = PC.crit ∧
  s'.lock = none ∧ s'.pc = fun q => if q = p then PC.idle else s.pc q

def Next (s s' : State Proc) : Prop :=
  ∃ p, Acquire p s s' ∨ Release p s s'

/-- The states of all behaviours satisfying `Init ∧ □[Next]_vars`.
Stuttering steps add no states, so they need no constructor. -/
inductive Reachable : State Proc → Prop where
  | init {s} : Init s → Reachable s
  | step {s s'} : Reachable s → Next s s' → Reachable s'

def MutualExclusion (s : State Proc) : Prop :=
  ∀ p q, s.pc p = PC.crit → s.pc q = PC.crit → p = q

/-- The inductive invariant: a process is critical exactly when it holds the lock. -/
def Inv (s : State Proc) : Prop :=
  ∀ p, s.pc p = PC.crit ↔ s.lock = some p

omit [DecidableEq Proc] in
theorem inv_init {s : State Proc} (h : Init s) : Inv s := by
  intro p
  obtain ⟨hl, hp⟩ := h
  simp [hl, hp]

theorem inv_next {s s' : State Proc} (hinv : Inv s) (h : Next s s') : Inv s' := by
  obtain ⟨p, hacq | hrel⟩ := h
  · obtain ⟨hl, _, hl', hpc'⟩ := hacq
    intro q
    rw [hl', hpc']
    by_cases hq : q = p
    · simp [hq]
    · have hidle : s.pc q ≠ PC.crit := fun hc => by
        have := (hinv q).mp hc
        rw [hl] at this
        cases this
      have hne : p ≠ q := fun e => hq e.symm
      simp [hq, hidle, hne]
  · obtain ⟨hc, hl', hpc'⟩ := hrel
    intro q
    rw [hl', hpc']
    by_cases hq : q = p
    · simp [hq]
    · have hidle : s.pc q ≠ PC.crit := fun hcq => by
        have h1 := (hinv q).mp hcq
        have h2 := (hinv p).mp hc
        rw [h1] at h2
        exact hq (Option.some.inj h2)
      simp [hq, hidle]

omit [DecidableEq Proc] in
theorem inv_mutex {s : State Proc} (h : Inv s) : MutualExclusion s := by
  intro p q hp hq
  have h1 := (h p).mp hp
  have h2 := (h q).mp hq
  rw [h1] at h2
  exact Option.some.inj h2

theorem inv_reachable {s : State Proc} (h : Reachable s) : Inv s := by
  induction h with
  | init h0 => exact inv_init h0
  | step _ hn ih => exact inv_next ih hn

/-- `Spec ⇒ □MutualExclusion`. -/
theorem safety {s : State Proc} (h : Reachable s) : MutualExclusion s :=
  inv_mutex (inv_reachable h)

end LockMutex
