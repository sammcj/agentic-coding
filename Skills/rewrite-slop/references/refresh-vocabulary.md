# Refreshing the register vocabulary

Read this only when the user has asked to update the skill's vocabulary against current data. Nothing here runs as part of a rewrite.

## What the vocabulary is

Tier 2's five groups and the `GROUPS` table in `scripts/check_output.py` hold the same words under the same group names. They are a curated snapshot of one cluster's highest-lift vocabulary, taken from louisabraham.github.io/load-bearing.

That project samples GitHub pull request descriptions daily, clusters them by vocabulary alone, and ranks each cluster's words by how much more often they appear inside it than outside. One cluster grew from under 1% of the sample to over a third across 2025 and 2026; its ranking is the source.

## Steps

1. Clone or update the data: `git clone https://github.com/louisabraham/load-bearing ~/git/load-bearing`, or `git -C ~/git/load-bearing pull` if it is already there.
2. Run `python3 scripts/refresh_markers.py` (add `--data PATH` if the clone is elsewhere). It reports; it changes nothing.
3. Judge each candidate it prints. Keep a word only if it is a **style** tell. Send **subject matter** to the script's `DECLINED` set so later refreshes stop proposing it.
4. Apply keeps to `GROUPS` in `check_output.py` and to the matching Tier 2 bullet in `SKILL.md`. The two must stay in step, because the script prints the group names the rubric uses.
5. Re-run `scripts/check_output.py` over `resources/*.md`. Those files are target prose: a group that flags them has taken in a word that is ordinary English, so pull it back out.
6. Record what changed in `CHANGELOG.md`.

## What counts as style rather than subject matter

The source corpus is pull request descriptions, mostly about testing and CI, so its ranking lifts topic words alongside style words. Three tests, in order:

- Would the word be reachable in a book review or a policy brief? `plainly` and `carries` travel; `mutation-tested` and `goldens` do not.
- Is the word ordinary English? `byte-identical` is jargon and belongs in `DECLINED`; `precisely` is not.
- Does it fit one of the five groups? A word matching none of them is usually topic, not register. Add a sixth group only if the ranking shows a genuine new pattern, and give it a cure in Tier 2, not just a list.

Function words (`every`, `its`, `never`, `rather`, `half`) rank high by volume and are unusable individually. `never` and `nothing` earn their place only inside the negation group, where the whole group's rate is what is read.

## Re-checking the bands

`ELEVATED`, `HEAVY`, `LEAST` and `SHORT` in `check_output.py` were set by scoring the source corpus's own descriptions from opposite ends of its range: at the current values, 0.3% of January 2025 descriptions over 200 words flag against 45.2% of August 2026 ones.

Re-derive them the same way after any large vocabulary change, using `data/days/*.jsonl` from the clone (one JSON object per line, `body` is the text, and authors ending `[bot]` or `-bot` are excluded from the source's own counts). Check the result against `resources/*.md`, which should stay silent. Two gates matter: a rate alone flags clean short prose carrying one marker, which is why `LEAST` and `SHORT` exist.

## A second source, for the older register

Tier 3's marketing vocabulary is measured by Kobak et al., `github.com/berenslab/llm-excess-vocab` (MIT). It ships 900 annotated words and a 362,442 × 15 matrix of yearly PubMed counts, and its baseline is real: pre-2023 years are the human era, so a word's 2024 excess is a human-versus-LLM ratio rather than a cluster comparison.

Derive a word's ratio as observed 2024 frequency over a counterfactual extrapolated linearly from 2021 and 2022. Two cautions, both of which cost a wrong conclusion the first time round:

- Read the raw 2024 count beside every ratio. Under about 500 abstracts the ratio is noise (backstop appears in 6, vacuous in 10).
- A ratio near 1.0 is not innocence. The corpus is biomedical, so subject-matter words drown any stylistic signal in legitimate use (features appears in 75,119 abstracts, modalities in 14,352).

Its data ends in 2024, which makes it good on Tier 3's register and blind to Tier 2's.

## Spelling

Every list matches on meaning, not spelling. When adding a word with British and American forms, add both, and write out each alternation in any regex (`revolutioni[sz]e`, `recogni[sz]ed`). A rule carrying one spelling silently passes half its inputs. The rewrite itself keeps whichever convention the input uses.

## The limit worth stating

The ranking compares one cluster against the other nine of the same corpus. It is not a comparison against human writing, and a high lift means "characteristic of this way of writing", not "only AI does this". A word absent from the ranking is not thereby innocent: most of Tier 3's marketing vocabulary never clears the source's 50-account floor because pull request authors rarely write it at all.
