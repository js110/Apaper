# Paper A — Robust Spacetime Compliance

Research manuscript and prototype for **Beyond Point Claims: Zero-Knowledge
Certification of Robust Spacetime Compliance in Vehicular Crowdsensing**.
Target journal: *Vehicular Communications* (Elsevier). This is an author-review
draft, not a submitted or accepted article.

## Files

- [Current manuscript PDF](paper_a/paper_a.pdf)
- [LaTeX source](paper_a/paper_a.tex) and [references](paper_a/references.bib)
- [Flat LaTeX package](paper_a/paper_a_vehcom_latex_draft.zip)
- [Implementation and experiment guide](paper_a/README.md)
- `paper_a/prototype/`: Python geometry and Go/gnark proof circuits and gateway.
- `paper_a/experiments/`: experiment scripts and recorded results.
- `paper_a/figures/`: manuscript figures, plotting code and data tables.
- `paper_a/evidence/`: dated provenance, checks and revision records.
- [Remaining author confirmations](paper_a/submission_confirmations_zh.md)

## Build and test

```sh
cd paper_a
latexmk -pdf -interaction=nonstopmode -halt-on-error paper_a.tex
python3 -m unittest discover -s prototype -p 'test_*.py'
cd prototype/zkdepth
go test ./...
```

Go dependencies are pinned in `go.mod`/`go.sum`. Experiment and plotting scripts
use NumPy and Matplotlib; see the paper-level guide for the individual workflows.

Third-party raw UrbanNav and GraphGNSSLib files are intentionally excluded while
redistribution permissions remain unverified. Restore them from the original
sources and verify the hashes described in `paper_a/README.md` before running
the receiver/replay experiments or full artifact audit. Historical successful
audit reports describe the original local environment, not a clean-clone run.
The DOI metadata helper also requires the separately installed citation-management
skill parser; it is not needed to compile the paper or run the prototype tests.

## Repository scope and workflow

The initial commit imports the current Paper A files on 2026-09-23 without the
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
