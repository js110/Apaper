# Paper A — Robust Spacetime Compliance

Research repository for **Zero-Knowledge Certification of Robust Spacetime Compliance under Byzantine Evidence for Vehicular Crowdsensing**.

**Active target journal:** *Cybersecurity* (Springer Nature). Manuscript preparation is complete as a working draft, but **no submission or acceptance is claimed**.

## Current Cybersecurity submission materials

- [Chinese-derived English translation and template](paper_a/venue_cybersecurity/README.md) — active submission folder.
- [Anonymous review manuscript](paper_a/venue_cybersecurity/manuscript_review.tex) — compiled with the Springer Nature `sn-jnl` format.
- [Identified author manuscript](paper_a/venue_cybersecurity/manuscript_with_authors.tex) and [separate title page](paper_a/venue_cybersecurity/title_page.tex).
- [Translation source provenance](paper_a/venue_cybersecurity/TRANSLATION_SOURCE.md) — records the SHA-256 of the finalized revised Chinese manuscript and the chapter mapping.
- [Submission checklist](paper_a/venue_cybersecurity/SUBMISSION_CHECKLIST.md) and [cover-letter draft](paper_a/venue_cybersecurity/cover_letter_draft.md).
- PDF and self-contained source ZIP are produced by the **Cybersecurity manuscript build** GitHub Actions workflow. That workflow downloads the official Springer Nature LaTeX template before compilation.

The prior JISA English manuscript (`paper_a/paper_a.tex`), JISA template and historical evidence remain as an archive; **they are not the English prose source for the new Cybersecurity translation**.

## Research and reproducibility

- [Experiment and implementation guide](paper_a/README.md)
- [Original bibliography](paper_a/references.bib)
- [Canonical code and experiments](https://github.com/js110/ZCRSC-PAPER)
- `paper_a/prototype/`, `paper_a/experiments/` — retained manuscript audit snapshots
- `paper_a/figures/` — figures, source scripts, and plot data
- `paper_a/evidence/` — previous provenance and revision records

## Legacy JISA build and test

```sh
cd paper_a
latexmk -pdf -interaction=nonstopmode -halt-on-error paper_a.tex
python3 -m unittest discover -s prototype -p 'test_*.py'
cd prototype/zkdepth
go test ./...
```

Go dependencies are pinned in `go.mod`/`go.sum`. The manuscript CI pins Python 3.13 and the direct NumPy/Matplotlib versions in `paper_a/requirements.txt`; see the paper-level guide for the individual workflows.

Third-party raw UrbanNav and GraphGNSSLib files are intentionally excluded while
redistribution permissions remain unverified. Restore them from the original
sources and verify the hashes described in `paper_a/README.md` before running
the receiver/replay experiments or full artifact audit. GitHub Actions now exercises the core manuscript, semantic, Go, baseline, bibliography, and export path from a clean checkout. Historical full scientific audits that require excluded third-party raw files still describe the original local environment rather than a self-contained clean-clone reproduction.
The DOI metadata helper also requires the separately installed citation-management
skill parser; it is not needed to compile the paper or run the prototype tests.

## Repository scope and workflow

The initial commit imports the Paper A working files on 2026-09-23 without the
old IEEE/PCVCS repository history. Private keys, caches, build products, downloaded
raw third-party data and internal reviewer-assessment/response notes are excluded.
The original local working directory remains unchanged as a working archive.

Use this checkout for subsequent versioned changes:

```sh
git status
git add <changed-files>
git diff --cached
git commit -m "paper: describe revision"
git push
```

Do not synchronize by copying over newer changes without reviewing the diff.
No new license is assigned to author material by this import. Bundled Elsevier
template files retain their original license and notices.
