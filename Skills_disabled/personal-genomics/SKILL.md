---
name: personal-genomics
description: Analyse personal DNA / genome files for pharmacogenomics, disease risk, carrier status, ancestry and traits. Use whenever the user mentions DNA or genome analysis, a raw genome file, gene names, drug-gene interactions, or wants to combine multiple DNA sources.
disable-agent-invocation: true
allowed-tools: Bash Read Glob SendUserFile
---

# Personal Genomics

Runs the local `personal-genomics` toolkit over one or more raw DNA files and reports the findings. All analysis is offline; genetic data never leaves the machine.

## First: track the workflow

Create a task for each step below, then work them to completion. The run is multi-step and the reporting step (surfacing findings safely) is the one most often skipped once the analysis file is written.

## Locate the toolkit

The scripts and their virtualenv live at `~/git/personal-genomics` (a `.venv/` with pandas/numpy/scipy/reportlab). Use that venv's Python: `~/git/personal-genomics/.venv/bin/python`.

If the repo or venv is missing, set it up before analysing:

```bash
cd ~/git/personal-genomics && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

If the toolkit lives elsewhere, ask the user for the path rather than guessing.

## Locate the input files

Ask the user where their DNA file(s) are if not already given. Common location is `~/Downloads/DNA/`. Supported inputs:

- Array exports: 23andMe, AncestryDNA, MyHeritage, FTDNA (tab-delimited rsid text)
- Sequencing: `.vcf` / `.vcf.gz` (whole genome or exome)

A `.cram.crai` on its own is not usable (it is only an index; the alignment data is in the `.cram` it points to). See Gotchas for what to do when the `.cram` itself is available.

## Choose single-source or combined

**One file** -> `comprehensive_analysis.py`:

```bash
~/git/personal-genomics/.venv/bin/python ~/git/personal-genomics/comprehensive_analysis.py <file> --out <dir>
```

**Two or more files** -> `combine_sources.py`, which merges them first:

```bash
~/git/personal-genomics/.venv/bin/python ~/git/personal-genomics/combine_sources.py <file1> <file2> ... --out <dir>
```

Always merge when more than one source exists. A variants-only VCF (the usual WGS export) lists only sites where the person differs from the reference, so every homozygous-reference site is absent. The marker analysis treats an absent rsID as "not tested" and skips it, which makes a rich WGS file yield *fewer* findings than an array on its own. Merging restores the array's reference/normal calls and keeps the WGS's rare variants, producing a strict superset. The combiner resolves contested sites to the sequencing call and writes `merge_stats.json` recording overlap, agreement, and strand-flip counts.

Outputs land in `<dir>` (suggest `~/dna-analysis/reports` for single, `~/dna-analysis/reports-combined` for merged): `agent_summary.json`, `full_analysis.json`, `report.txt`, `dashboard.html`.

## Report the findings

Read `agent_summary.json` (it is priority-sorted) - not `full_analysis.json`, and never echo the raw genotype data. Surface, in order:

1. `critical_alerts` - state each gene, genotype, and the recommended action verbatim.
2. `high_priority` - pharmacogenomics and actionable risk items.
3. A short read of `polygenic_risk_scores` (these are percentile *ranges* with confidence, not verdicts) and `apoe_status`.

Then offer the dashboard with `SendUserFile` (`display: render`).

Frame results as informational, not diagnostic. Recommend confirmatory clinical-grade testing and genetic counselling for any pathogenic hereditary-cancer variant, critical pharmacogenomic finding (e.g. DPYD, MT-RNR1, HLA-B risk alleles), APOE e4/e4, or carrier status with reproductive implications.

## Gotchas

- **Output directory write**: the tool writes to `~/dna-analysis/` by default, outside a sandboxed working tree. If the run fails with "Operation not permitted", re-run with filesystem write access (this is the user's own data on their own machine).
- **rsID matching is build-agnostic**: markers match by rsID, not position, so hg19 array data and hg38 WGS combine without liftover.
- **Strand flips**: ~0.1% of overlapping sites disagree purely by strand (A/T vs complement); the combiner detects these and resolves to the sequencing call. A non-trivial count of *real* conflicts in `merge_stats.json` is worth flagging to the user.
- **CRAM, when available**: the `.cram` (not the `.crai` index alone) holds the aligned reads, so marker positions can be genotyped directly — giving true hom-ref calls even at sites neither the array nor a variants-only VCF covered. Scripts live in `cram/`. Needs an hg38 reference FASTA matching the CRAM's contigs (the one it was aligned to) and `samtools`/`bcftools`/`tabix`. The marker sites file (`cram/marker_sites_hg38.vcf.gz`) is prebuilt; rebuild it with `cram/build_targets.py` only if markers change. Run:

  ```bash
  ~/git/personal-genomics/.venv/bin/python ~/git/personal-genomics/cram/genotype_cram.py \
    --cram <file.cram> --reference <hg38.fa> \
    --analyze --combine-with <array.txt> <genome.vcf.gz>
  ```

  This calls genotypes at the marker sites, merges them with the other sources, and writes a combined report to `~/dna-analysis/reports-cram`.
- **Empty `nutrition_insights` / `fitness_insights` or a duplicated marker row** are known quirks of the upstream tool, not data problems.
