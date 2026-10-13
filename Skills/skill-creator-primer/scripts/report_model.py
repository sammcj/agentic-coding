"""What render_report's page shows, minus the HTML: each finding and how it ranks, the verdict, and the brief."""

import contextlib
import io
import json
import os
import sys
from pathlib import Path
from typing import NamedTuple

import validate_skill as vs  # pyright: ignore[reportMissingImports]

RANK = {"certain": 0, "probable": 1, "possible": 2}

# Each verdict level: its word, the ramp step that colours it, and its rank. See assess() for what sets each.
LEVELS = {"fail": ("Fail", "certain", 0), "work": ("Needs work", "probable", 1), "judge": ("Pass", "", 2)}
CELLS = ("budget", "structure", "wording", "agent")
VERDICT_REASONS = 3
# Lexical no-ops need work from 2 per 1000 words, and never on fewer than 3 hits. Calibrated over 64 installed skills:
# over half carry none, and 2.0 flags the top 8%, where the words are a habit rather than a slip.
NOOP_RATE, NOOP_LEAST = 2.0, 3
SPEC_SKIPPED = "Spec checks skipped"

# The primer's own review grades (Reviewing a Skill), placed on the ramp for colour. Spec and primer violations block;
# a judgement call is the agent's read and carries the possible step's caveat.
GRADES = {"spec": "certain", "primer": "probable", "judgement": "possible"}


class AgentFinding(NamedTuple):
    """One finding from the agent that ran the review, passed in with --findings."""

    grade: str  # spec | primer | judgement
    finding: str
    where: str = ""  # path or path:line, relative to the skill
    fix: str = ""
    cite: str = ""  # the primer section or failure mode it rests on

    @property
    def conf(self):
        return GRADES[self.grade]


def load_agent_findings(path):
    """[AgentFinding] from a JSON array, or "-" for stdin. Raises ValueError naming the first bad entry, since the
    agent that wrote the file is the one reading the error."""
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError("--findings is not valid JSON: %s" % err) from None
    if not isinstance(data, list):
        raise ValueError("--findings must be a JSON array of finding objects")
    out = []
    for i, item in enumerate(data):
        if not isinstance(item, dict) or not str(item.get("finding", "")).strip():
            raise ValueError("--findings entry %d needs a non-empty \"finding\"" % i)
        if not isinstance(item.get("grade"), str) or item["grade"] not in GRADES:
            raise ValueError("--findings entry %d: \"grade\" must be one of %s"
                             % (i, ", ".join(GRADES)))
        out.append(AgentFinding(**{k: str(item.get(k) or "").strip() for k in AgentFinding._fields}))
    return out


def why_for(rule):
    """The rule's reason, with its caveat if it has one. The caveat travels with the reason everywhere the reason
    goes: caption, tooltip, mark and brief."""
    text = WHY.get(rule, "")
    if rule in vs.POSSIBLE:
        text = "%s Possible only: %s." % (text, vs.POSSIBLE[rule])
    return text


def confidence(rule):
    """What the reader should think of a mark: possible carries a caveat from the validator, certain cannot be
    argued with, and the rest is probable."""
    if rule in vs.POSSIBLE:
        return "possible"
    return "certain" if rule in vs.CERTAIN else "probable"

# The copied brief is read by an agent with a context budget, so it stays about a page: the kinds worth acting on, with
# a few instances of each to find them by.
BRIEF_MAX, BRIEF_EXAMPLES = 12, 6

# A rule name says nothing to someone reading the page without the primer open beside it, and nothing to an agent handed
# the brief. One line per kind: what it caught, and what to do instead.
WHY = {
    "opener": "A discourse marker opening a sentence. It announces a turn the "
              "sentence already makes. Delete it and start on the claim.",
    "puffery": "An adjective asserting quality instead of stating it. It survives "
               "the deletion test nowhere: cut it, or replace it with the measurement.",
    "filler-verb": "A verb reaching for weight it does not carry. Name the action: "
                   "'use', 'add', 'read', 'run'.",
    "metaphor-tic": "A figure the model reaches for by habit. Say what the thing is or does.",
    "byte-identical": "\"Byte-identical\" more than once. Say it once, or say what was compared.",
    "negation-antithesis": "A not-X-but-Y contrast. Apply the swap test - if the "
                           "reversal reads as well, the contrast carries nothing. "
                           "State the claim directly.",
    "americanism": "An American spelling. Australian English is the house style, so "
                   "use the -ise, -our, -re or doubled-l form. Words whose Australian "
                   "form turns on noun versus verb, and technical terms spelled -iz- "
                   "everywhere, are not flagged.",
    "blob": f"A text unit of {vs.BLOB_WORDS}+ words, in any shape. Long enough to "
            "bury the instruction inside it, so the agent acts on the prose it "
            "remembers. Split it into steps, or cut it.",
    "dense-run": f"{vs.DENSE_RUN}+ consecutive units of {vs.DENSE_WORDS}+ words, or "
                 f"{vs.DENSE_LIST_RUN}+ list items of {vs.DENSE_LIST_WORDS}+, not every one "
                 "of them a blob. A wall with nowhere to rest: split it, or cut the units "
                 "that restate one another.",
    "hard-wrap": "A paragraph or list item broken across source lines by hand. Markdown joins the lines when it "
                 "renders, so the breaks buy nothing, and every later edit reflows the paragraph and spreads a "
                 "one-word change across the diff. Put each paragraph or item on one line.",
    "invisible": "A character that renders as nothing or as an ordinary space - a "
                 "no-break space, a zero-width space, a private-use glyph - usually "
                 "pasted in from a web page. It breaks a command or a trigger phrase "
                 "it sits in, and no editor shows it. Replace it with a plain space, "
                 "or delete it.",
    "code": f"A fenced block over {vs.CODE_FENCE_LINES} lines. Scripts belong in "
            "scripts/ and templates in assets/, where they cost nothing until run.",
    "table": f"A table holding a cell over {vs.TABLE_CELL_MAX} characters. Tables are "
             "read as a grid, and a sentence in a cell has to be read linearly, so "
             "the reader pays the grid's cost and gets none of its benefit - and the "
             "row wraps the moment the column is narrow. Use bullets for the text, "
             "and keep tables for short structured values.",
    "bold-emphasis": "Bold dropped into running sentences. Emphasis works by being "
                     "rare, so when everything is bold nothing is, and the one "
                     "instruction the skill needed to land stops standing out. "
                     "Bold that opens a line is a label and is exempt: keep it for "
                     "a bullet lead, and let the sentence carry the rest.",
    "load": "Worst-case load is SKILL.md plus the largest reference - what one "
            "branch firing costs. Move branch-only content into references/, and "
            "delete lines the agent would obey anyway.",
    "spec-error": "A violation of the Agent Skills spec. The skill will not load "
                  "or will fail validation until it is fixed.",
    "spec-warning": "Valid, but flagged: usually an unrecognised frontmatter field "
                    "or a description over its word ceiling.",
    "when-to-use": "A \"When to use\" section in the body. The body is only read "
                   "once the description has already fired, so the section answers "
                   "a question the agent settled before it opened the file. Delete "
                   "it, and move any trigger it names that the description lacks "
                   "into the description. \"When not to use\" and \"When to use X "
                   "instead of Y\" are exempt: those still change what happens.",
    "description-length": "The description is the only part of a skill loaded on "
                          "every turn of every session, fired or not, so its length "
                          "is charged to every conversation the user has. Over the "
                          "ceiling it also triggers worse: the match spreads across "
                          "padding instead of concentrating on the trigger words. "
                          "Cut a trigger branch, not the wording around one.",
}


class Finding(NamedTuple):
    """One entry in the findings list, in the form the page and the brief share.

    Both read this list rather than each walking the validator again, so the
    brief cannot disagree with the page it was copied from.
    """

    rule: str  # what fired; also the grouping key in the brief
    n: int  # how many, counted in `unit`
    unit: str  # what n counts, so the brief can say "3 text units"
    example: str  # the term itself, or where the block sits
    kind: str  # blob | code | filler, which cell shows it
    what: str  # middle column: the term, or the unit's opening words
    size: int  # the count as the page prints it: 412w, 14L, 3
    where: str = ""  # right column: path:line
    term: str = ""  # selection and search key, terms only
    goto: str = ""  # anchor id, for rows that scroll the document
    share: float = 0.0  # bar width 0..1, for a row measured against a threshold
                        # rather than against the other rows' counts

    @property
    def why(self):
        return why_for(self.rule)

    @property
    def possible(self):
        return self.rule in vs.POSSIBLE

    @property
    def conf(self):
        """The row's step on the ramp; bold has none, being a density rather than a defect at any span. A description
        past only the soft ceiling is probable, matching the validator's warning."""
        if self.kind == "descw":
            return "probable"
        return "" if self.kind == "em" else confidence(self.rule)


def term_key(hit):
    """The term a finding is grouped under. Matches validate_skill's own grouping
    so the ranked list and the marks in the source agree on what is one term."""
    return " ".join(str(hit).split()[:8]).lower()


def anchor(index, lineno):
    """DOM id for one source line, keyed by the file's position in the load order.

    Keyed by position rather than by path so two paths differing only in
    punctuation cannot collide on one id and send a jump to the wrong file.
    """
    return "L-%d-%d" % (index, lineno)


def loadable_files(skill_dir):
    """[(relative path, path)] over the Markdown that actually loads, in load order.

    The single source of the relative path every other function keys on.
    """
    root = Path(skill_dir).resolve()
    return [(str(p.relative_to(root) if p.is_relative_to(root) else p), p)
            for p in vs.referenced_md_files(skill_dir)]


def per_file_tokens(skill_dir, use_tiktoken=False):
    """{relative path: tokens} over the Markdown that actually loads, largest first."""
    count = vs.tiktoken_tokens if use_tiktoken else vs.estimate_tokens
    sized = {rel: count(path.read_text(encoding="utf-8-sig", errors="ignore"))
             for rel, path in loadable_files(skill_dir)}
    return dict(sorted(sized.items(), key=lambda kv: (-kv[1], kv[0])))


def worst_case_load(sized):
    """SKILL.md plus the largest reference - the figure the rating gate judges."""
    main = sized.get("SKILL.md", 0)
    refs = [n for name, n in sized.items() if name != "SKILL.md"]
    return main + (max(refs) if refs else 0)


def spec_findings(skill_dir):
    """(errors, warnings) from the spec checks, or the name of the missing dependency.

    Caught rather than predicted, because an import probe cannot see either
    failure: lint() exits the process when skills-ref is absent, and raises a
    plain ImportError when it is present but partial. Both would otherwise lose
    the whole page over one cell.

    The description-length rule is the primer's own, not the spec's, and needs
    only PyYAML - so it still runs when skills-ref is missing. Routing it solely
    through lint() meant a 119-word description reported nothing at all on a
    machine without an optional third-party install, which is the one finding on
    this page that costs every agent context on every turn.
    """
    if vs.yaml is None:
        return "PyYAML"
    try:
        # lint() prints its own install hint on the way out; the CLI's stdout is the report path alone, so the hint is
        # swallowed and restated in the cell.
        with contextlib.redirect_stdout(io.StringIO()):
            return vs.lint(Path(skill_dir))
    except (SystemExit, ImportError):
        errors, warnings = vs.description_findings(vs.skill_description(skill_dir))
        warnings.append(SPEC_SKIPPED + ": skills-ref is not installed, so only the primer's own "
                        "description rule ran. Re-run under uv run for the rest.")
        return errors, warnings


class Issue(NamedTuple):
    """One thing the verdict rests on, in the cell the reader looks to for it."""

    level: str  # fail | work | judge
    cell: str  # one of CELLS
    text: str


def assess(budget, found, agent, emphasis, words):
    """[Issue] behind the verdict, worst first, each level taken from a split the primer already makes.

    - fail: what validate_skill's exit code fails (a spec error, the description over its hard cap, a Poor load), and
      what the primer's review says blocks (an agent's spec or primer grade).
    - work: the validator's FACTS, always-loaded costs it reports without gating, and the SIGNALS that are habits by
      count or rate: lexical no-ops, abused bold, and reference blobs at the validator's warning count.
    - judge: every other SIGNAL, decided one by one. These never lower the verdict, so one flagged phrase cannot.

    `budget` is (rating, driver_is_main, within_budget, load), as _budget reports it.
    """
    rating, driver_is_main, within_budget, load = budget
    out = []
    if rating in ("OK", "Poor") and not within_budget:
        level = "fail" if rating == "Poor" else ("work" if driver_is_main else "judge")
        out.append(Issue(level, "budget", "worst-case load %d tokens rates %s" % (load, rating)))
    ref_blobs = [f for f in found if f.kind == "blob" and not f.where.startswith("SKILL.md:")]
    # Spec rows rather than the raw spec result: spec_rows has already folded the description errors into the
    # description row, and reading the raw list would print them twice.
    for f in found:
        if f.kind == "spec":
            out.append(Issue("fail", "structure", f.what))
        # The skipped-checks note is about this machine, not the skill; the verdict says so apart.
        elif f.kind == "specw" and not f.what.startswith(SPEC_SKIPPED):
            out.append(Issue("work", "structure", f.what))
        elif f.kind in ("desc", "descw"):
            out.append(Issue("fail" if f.kind == "desc" else "work", "structure", f.what))
        elif f.kind == "redundant":
            out.append(Issue("work", "structure", '"%s" section at %s' % (f.what, f.where)))
        elif f.kind == "blob" and f not in ref_blobs:
            out.append(Issue("work", "structure", "%dw blob in SKILL.md at %s" % (f.size, f.where)))
        elif f.kind in ("blob", "code", "table", "dense", "wrap"):
            out.append(Issue("judge", "structure", f.what))
    if len(ref_blobs) >= vs.REF_BLOB_WARN:
        out.append(Issue("work", "structure", "%d blobs in references" % len(ref_blobs)))
    if emphasis:
        out.append(Issue("work" if emphasis["band"] == "ABUSED" else "judge", "wording",
                         "bold %s at %.1f per 1000 words" % (emphasis["band"].lower(), emphasis["rate"])))
    terms = [f for f in found if f.kind == "filler"]
    out += [Issue("work", "wording", "invisible character %s" % f.term) for f in terms if f.rule == "invisible"]
    no_ops = [f for f in terms if f.rule not in ("invisible", "americanism")]
    hits = sum(f.n for f in no_ops)
    rate = 1000.0 * hits / max(words, 1)
    if hits >= NOOP_LEAST and rate >= NOOP_RATE:
        out.append(Issue("work", "wording", "%d lexical no-ops, %.1f per 1000 words" % (hits, rate)))
    else:
        out += [Issue("judge", "wording", f.term) for f in no_ops]
    out += [Issue("judge", "wording", f.term) for f in terms if f.rule == "americanism"]
    out += [Issue("judge" if a.grade == "judgement" else "fail", "agent", a.finding) for a in agent or ()]
    return sorted(out, key=lambda i: LEVELS[i.level][2])  # stable: within a level, cell order holds


def overall(issues):
    """The worst level among issues ranked worst first; judge alone passes."""
    return issues[0].level if issues else "judge"


def verdict_line(issues):
    """The verdict as one line of the brief, naming what it rests on."""
    level = overall(issues)
    top = ["%s: %s" % (i.cell, i.text.rstrip(".")) for i in issues if i.level == level][:VERDICT_REASONS]
    return "Verdict: %s%s." % (LEVELS[level][0], " (%s)" % "; ".join(top) if level != "judge" else "")


def spec_rows(spec, skill_dir):
    """Spec errors and warnings as findings, so they list where every other
    finding lists.

    A cell of their own said only that they came from a different checker, which
    is the report's business and not the reader's - and it printed the
    description-length error a second time, next to the row that already carried
    it. That row is dropped here, by matching the exact text the same check
    produced, rather than by sniffing the wording.
    """
    if isinstance(spec, str):
        return [Finding(rule="spec-warning", n=1, unit="warning", example="dependency",
                        kind="specw",
                        what=SPEC_SKIPPED + ": %s is not installed. Re-run under uv run."
                             % spec, size=0, where="")]
    errors, warnings = spec
    # Only a long description has a row of its own to carry these; a too-short one stays a spec row, or the page would
    # drop a finding the validator lists under FACTS.
    description = vs.skill_description(skill_dir)
    own = (set(sum(vs.description_findings(description), []))
           if vs.description_word_count(description) > vs.DESCRIPTION_WORDS_WARN else set())
    out = []
    for kind, rule, unit, group in (("spec", "spec-error", "error", errors),
                                    ("specw", "spec-warning", "warning", warnings)):
        for text in group:
            if text in own:
                continue
            out.append(Finding(rule=rule, n=1, unit=unit, example=text, kind=kind,
                               what=text, size=0, where=""))
    return out


def tally(filler):
    """{term: (category, count)}, one entry per term rather than per hit."""
    terms = {}
    for category, _rel, _line, hit in filler:
        key = term_key(hit)
        seen, count = terms.get(key, (category, 0))
        terms[key] = (seen, count + 1)
    return terms


def wrapped_by_file(wrapped):
    """{rel: [unit]} in file order, the grouping the row and the shading's jump back both key on."""
    out = {}
    for unit in wrapped:
        out.setdefault(str(unit[1]), []).append(unit)
    return out


def collect(blobs, long_code, filler, index_of, emphasis=None, dense=(),
            redundant=(), description=None, tables=(), wrapped=()):
    """Every finding as one ranked list: blocks first, then terms by frequency.

    The description and the "When to use" sections lead, ahead of every other
    block. Both are certain, and both cost more than anything under them: the
    description is charged to every session whether the skill fires or not, and a
    "When to use" section is a whole block of always-loaded text answering a
    question that was settled before the file was opened.

    The two panel cells filter this list and the brief groups it, so a finding
    can never appear on the page in a form the copied text disagrees with.

    Terms rank by confidence before count: a certain finding leads however
    rare, and a possible one sits below every probable one however common,
    since a page of "?" rows above the defects would bury them.

    Bold is one row however many spans it covers: it is a rate, and a hundred
    distinct bolded phrases would be a hundred rows in a list meant to name
    habits. It heads the frequency table for the same reason - it is the one
    finding there that describes the whole document rather than a word in it.
    """
    found = []
    if description:
        words, span, over = description
        found.append(Finding(
            rule="description-length", n=1, unit="description",
            example="SKILL.md:%d" % span[0], kind=desc_kind(words),
            what="description is %d words, over the %d-word %s"
                 % (words, over[0], over[1]),
            size=words, where="SKILL.md:%d" % span[0],
            goto=anchor(index_of.get("SKILL.md", 0), span[0]),
            share=min(1.0, words / vs.DESCRIPTION_WORDS_FAIL),
        ))
    for lines, rel, start, _end, heading in redundant:
        found.append(Finding(
            rule="when-to-use", n=1, unit="section", example=f"{rel}:{start}",
            kind="redundant", what=" ".join(heading.lstrip("#").split()[:9]),
            size=lines, where=f"{rel}:{start}",
            goto=anchor(index_of.get(str(rel), 0), start),
        ))
    if emphasis:
        found.append(Finding(
            rule="bold-emphasis", n=emphasis["total"], unit="span",
            # The band leads the example so the brief carries it too, rather than the page and the copied text
            # disagreeing about how bad it is.
            example="%s %.1f/1000 words; %s"
                    % (emphasis["band"], emphasis["rate"],
                       ", ".join(w for w, _ in emphasis["worst"][:3])),
            kind="em",
            what="%s: %.1f mid-sentence bolds per 1000 words (sloppy over %.0f, "
                 "abused at %.0f)" % (emphasis["band"], emphasis["rate"],
                                      vs.BOLD_RATE, vs.BOLD_ABUSED),
            size=emphasis["total"], term="bold-emphasis",
            where="%s:%d" % emphasis["where"][0],
            share=min(1.0, emphasis["rate"] / vs.BOLD_ABUSED),
        ))
    for kind, group, unit in (("blob", blobs, "text unit"), ("code", long_code, "code block"),
                              ("table", tables, "table")):
        for size, rel, start, _end, opening in group:
            found.append(Finding(
                rule=kind, n=1, unit=unit, example=f"{rel}:{start}", kind=kind,
                what=" ".join(opening.split()[:9]), size=size, where=f"{rel}:{start}",
                goto=anchor(index_of.get(str(rel), 0), start),
            ))
    for size, rel, start, _end, opening, count, longest, listed in dense:
        found.append(Finding(
            rule="dense-run", n=1, unit="run", example=f"{rel}:{start}", kind="dense",
            what="%d %s, longest %dw: %s" % (count, "list items" if listed else "units", longest,
                                             " ".join(opening.split()[:6])),
            size=size, where=f"{rel}:{start}", goto=anchor(index_of.get(str(rel), 0), start),
        ))
    # One row per file rather than per unit: a file wrapped by hand is wrapped everywhere, and a row per paragraph
    # would bury every other finding. The row jumps to the first; the source shades them all.
    for rel, group in wrapped_by_file(wrapped).items():
        first = group[0][2]
        found.append(Finding(
            rule="hard-wrap", n=len(group), unit="unit", example=f"{rel}:{first}", kind="wrap",
            what="%d paragraphs or list items wrapped by hand" % len(group),
            size=sum(g[0] for g in group), where=f"{rel}:{first}", goto=anchor(index_of.get(rel, 0), first),
        ))
    where = {}
    for _category, rel, line, hit in filler:
        where.setdefault(term_key(hit), f"{rel}:{line}")
    ranked = sorted(tally(filler).items(),
                    key=lambda kv: (RANK[confidence(kv[1][0])], -kv[1][1], kv[0]))
    for term, (category, count) in ranked:
        found.append(Finding(
            rule=category, n=count, unit="use", example=term, kind="filler",
            what=term, size=count, where=where.get(term, ""), term=term,
        ))
    return found


def brief(skill_dir, load, sized, ceiling, within_budget, spec, found, agent=None, issues=()):
    """The findings as text, sized to paste into another agent.

    Grouped by rule and carrying each rule's reason. A list of bare rule names
    leaves the receiving agent guessing, and one rule is one habit to drop
    however many times it fired.

    Lines are separated by a blank one, never wrapped: the brief is pasted into
    something that may render it as markdown, where a wrap reflows anyway.
    """
    rating = vs.token_rating(load)
    out = ["Skill report for %s. Load the skill-creator-primer skill, then fix the "
           "following. Cut words, not behaviour: every instruction the skill carries "
           "has to survive." % os.path.basename(str(skill_dir)), "",
           verdict_line(issues), ""]

    budget = ("Budget: %s. Worst-case load %d tokens (SKILL.md plus the largest "
              "reference) across %d file(s) that load."
              % (rating, load, len(sized)))
    if within_budget:
        budget += " Within the declared max-load-tokens %d." % ceiling
    elif rating in ("OK", "Poor"):
        budget += " " + WHY["load"]
    out += [budget, ""]

    if isinstance(spec, tuple):
        errors, warnings = spec
        if errors or warnings:
            out.append("Spec: %d error(s), %d warning(s)." % (len(errors), len(warnings)))
            out += ["- %s" % x for x in list(errors) + list(warnings)]
        else:
            out.append("Spec: clean.")
    else:
        out.append("Spec: not checked, %s was not installed." % spec)
    out.append("")

    # Listed one per line, never grouped: each is a sentence of its own rather than another hit of a rule.
    if agent:
        out.append("Agent findings (spec and primer grades block):")
        for a in sorted(agent, key=lambda a: RANK[a.conf]):
            out.append("- [%s]%s %s%s%s" % (a.grade, " %s:" % a.where if a.where else "", a.finding,
                                           " Fix: %s" % a.fix if a.fix else "",
                                           " (%s)" % a.cite if a.cite else ""))
        out.append("")

    groups = {}
    for f in found:
        n, unit, seen, why = groups.get(f.rule, (0, f.unit, [], f.why))
        if f.example not in seen and len(seen) < BRIEF_EXAMPLES:
            seen.append(f.example)
        groups[f.rule] = (n + f.n, unit, seen, why)

    if not groups:
        out.append("Nothing else flagged.")
        return "\n".join(out)

    # Two lists, so the receiving agent fixes one and reads the other. The caveat travels in each possible rule's
    # reason, since that agent has the file but not the page.
    shown = list(groups.items())[:BRIEF_MAX]
    for maybe, head in ((False, "Findings, fix these:"), (True, "Possible, read before changing:")):
        picked = [(rule, g) for rule, g in shown if (rule in vs.POSSIBLE) == maybe]
        if not picked:
            continue
        out.append(head)
        for rule, (n, unit, seen, why) in picked:
            out.append("- %s, %d %s (%s): %s"
                       % (rule, n, unit if n == 1 else unit + "s", ", ".join(seen), why))
    if len(groups) > BRIEF_MAX:
        out.append("- and %d further kinds, listed in the report."
                   % (len(groups) - BRIEF_MAX))
    return "\n".join(out)


BLOCK_RULE = {"blob": "blob", "code": "code", "dense": "dense-run", "table": "table", "wrap": "hard-wrap",
              "redundant": "when-to-use", "desc": "description-length", "descw": "description-length",
              # No span in the source: a spec finding names the file. Listed with the rest, never shaded.
              "spec": "spec-error", "specw": "spec-warning"}
# What the margin label prints beside each block, since every block now takes a shade from the same ramp and the
# colour alone no longer says which kind fired.
BLOCK_LABEL = {"blob": "%dw blob", "code": "%dL code", "dense": "%d units, dense run",
               "table": "%d prose cells, table", "redundant": '%dL "when to use"',
               "desc": "%dw description", "descw": "%dw description", "wrap": "%dL wrapped"}


def desc_kind(words):
    """desc past the hard cap, which the validator fails; descw past the soft ceiling, which it only warns on."""
    return "desc" if words > vs.DESCRIPTION_WORDS_FAIL else "descw"
