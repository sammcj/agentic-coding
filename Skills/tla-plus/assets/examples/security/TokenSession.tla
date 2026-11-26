---------------------------- MODULE TokenSession ----------------------------
(***************************************************************************)
(* Bearer-token sessions with revocation and token theft, in PlusCal       *)
(* (P-syntax).                                                             *)
(*                                                                         *)
(* Abstraction decisions:                                                  *)
(*   - A token is an opaque value; unguessability is assumed, so the       *)
(*     attacker can only use tokens that leaked.                           *)
(*   - Expiry and logout are the same event here: the server moves the     *)
(*     token from valid to revoked.                                        *)
(*   - Validation and use are one atomic step.  A real resource server     *)
(*     that caches validation results has a wider window; model that by    *)
(*     splitting the step with a label.                                    *)
(*   - used is a history variable recording who used which token.          *)
(***************************************************************************)
EXTENDS FiniteSets

CONSTANTS Users, Tokens, NoToken, Mallory

ASSUME ConstantsOK ==
  /\ NoToken \notin Tokens
  /\ Mallory \notin Users

(* --algorithm TokenSession

variables
  valid = {},      \* tokens the server currently accepts
  revoked = {},    \* tokens the server has revoked
  leaked = {},     \* tokens the attacker has obtained
  used = {};       \* history: <<token, principal>> for each accepted use

define
  TypeOK ==
    /\ valid \subseteq Tokens
    /\ revoked \subseteq Tokens
    /\ leaked \subseteq Tokens
    /\ used \subseteq Tokens \X (Users \cup {Mallory})

  \* A revoked token is never valid again.
  RevocationIsFinal == valid \cap revoked = {}

  \* The attacker only ever uses tokens that leaked.
  NoForgery == \A u \in used : u[2] = Mallory => u[1] \in leaked
end define;

process user \in Users
variable held = NoToken;
begin
  session:
    while TRUE do
      either
        \* log in: the server issues a token it has never issued before
        await held = NoToken;
        with t \in Tokens \ (valid \cup revoked) do
          held := t;
          valid := valid \cup {t};
        end with;
      or
        \* use the token; the server accepts it only while it is valid
        await held \in valid;
        used := used \cup {<<held, self>>};
      or
        \* log out: the server revokes the token
        await held # NoToken;
        valid := valid \ {held};
        revoked := revoked \cup {held};
        held := NoToken;
      or
        \* the token leaks (XSS, log file, stolen device)
        await held # NoToken;
        leaked := leaked \cup {held};
      end either;
    end while;
end process;

process attacker = Mallory
begin
  replay:
    while TRUE do
      with t \in leaked do
        if t \in valid then
          used := used \cup {<<t, Mallory>>};
        end if;
      end with;
    end while;
end process;

end algorithm; *)
\* BEGIN TRANSLATION
VARIABLES valid, revoked, leaked, used

(* define statement *)
TypeOK ==
  /\ valid \subseteq Tokens
  /\ revoked \subseteq Tokens
  /\ leaked \subseteq Tokens
  /\ used \subseteq Tokens \X (Users \cup {Mallory})


RevocationIsFinal == valid \cap revoked = {}


NoForgery == \A u \in used : u[2] = Mallory => u[1] \in leaked

VARIABLE held

vars == << valid, revoked, leaked, used, held >>

ProcSet == (Users) \cup {Mallory}

Init == (* Global variables *)
        /\ valid = {}
        /\ revoked = {}
        /\ leaked = {}
        /\ used = {}
        (* Process user *)
        /\ held = [self \in Users |-> NoToken]

user(self) == \/ /\ held[self] = NoToken
                 /\ \E t \in Tokens \ (valid \cup revoked):
                      /\ held' = [held EXCEPT ![self] = t]
                      /\ valid' = (valid \cup {t})
                 /\ UNCHANGED <<revoked, leaked, used>>
              \/ /\ held[self] \in valid
                 /\ used' = (used \cup {<<held[self], self>>})
                 /\ UNCHANGED <<valid, revoked, leaked, held>>
              \/ /\ held[self] # NoToken
                 /\ valid' = valid \ {held[self]}
                 /\ revoked' = (revoked \cup {held[self]})
                 /\ held' = [held EXCEPT ![self] = NoToken]
                 /\ UNCHANGED <<leaked, used>>
              \/ /\ held[self] # NoToken
                 /\ leaked' = (leaked \cup {held[self]})
                 /\ UNCHANGED <<valid, revoked, used, held>>

attacker == /\ \E t \in leaked:
                 IF t \in valid
                    THEN /\ used' = (used \cup {<<t, Mallory>>})
                    ELSE /\ TRUE
                         /\ used' = used
            /\ UNCHANGED << valid, revoked, leaked, held >>

Next == attacker
           \/ (\E self \in Users: user(self))

Spec == Init /\ [][Next]_vars

\* END TRANSLATION

\* A define block cannot mention process variables, so the type of held is stated here.
ProcTypeOK == held \in [Users -> Tokens \cup {NoToken}]

(***************************************************************************)
(* An action property: no step records a new use of a token that is        *)
(* already revoked.  It constrains pairs of states, so it is written       *)
(* [][...]_vars and checked under PROPERTY, not INVARIANT.                 *)
(***************************************************************************)
NoUseAfterRevoke ==
  [][\A u \in used' \ used : u[1] \notin revoked]_vars

=============================================================================
