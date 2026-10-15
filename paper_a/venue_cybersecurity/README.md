# Cybersecurity submission — Springer Nature sn-jnl

This directory contains a Research-article conversion of the Apaper manuscript, using the Springer Nature authoring class and numbered basic references.

- `manuscript_review.tex` — **double-anonymous review manuscript**. Use this for peer review, after completing the checks below. Identifying public repository links are intentionally withheld here.
- `manuscript_with_authors.tex` — **unblinded copy**, for author audit only. Do not upload this file as the anonymous reviewer manuscript.
- `sn-jnl.cls`, `sn-basic.bst`, `references.bib` and `figures/` — LaTeX dependencies.
- `cover_letter_draft.md` and `SUBMISSION_CHECKLIST.md` — editable material not intended as anonymous paper text.

## Build

Run from this directory: `latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript_review.tex` (BibTeX is run when needed).

## Template provenance

The Springer Nature template is the official submission format recommended by the journal, while this copy of its class and bibliography style is taken from a third-party public mirror (RasmussenLab/paper_template). Verify that the files match the current *official* Springer Nature package before submission: https://www.springernature.com/gp/authors/campaigns/latex-author-support (December 2024 ZIP, official source).

The journal specifically requests double line spacing, line/page numbers, a 150–250-word abstract, 3–10 keywords, and separate title-page metadata under double-anonymous review.

## Important

This package is an editorially converted draft, **not confirmation of a fully compliant submission**. In particular, all coauthor contact details, competing-interest declarations, funding roles, mandatory disclosure of LLM use under the journal policy, and a truly anonymized reproducibility link must be finalized by the authors. Do not assert approvals that have not been obtained.
