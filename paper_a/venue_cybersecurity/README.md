# Cybersecurity submission — freshly translated from approved Chinese manuscript

This folder contains a **new English translation**, authored from the final revised Chinese six-chapter manuscript rather than by editing the former JISA English prose. The source file SHA-256 and section mapping are recorded in [TRANSLATION_SOURCE.md](TRANSLATION_SOURCE.md).

The journal's double-anonymous peer-review model requires distinct manuscripts and identified author metadata.

## Files

- `manuscript_review.tex` — anonymous reviewer manuscript. This is the manuscript to compile/upload for review after completing the checklist.
- `manuscript_with_authors.tex` — same newly translated body, unblinded for author audit.
- `title_page.tex` — separate identified title page; do **not** send this file as part of the anonymous reviewing manuscript.
- `translated_from_chinese/` — all English sections and tables, compiled via `\\input` from the two main documents.
- `references.bib`, `sn-jnl.cls`, `sn-basic.bst` — bibliography and Springer Nature format dependencies.
- `cover_letter_draft.md`, `SUBMISSION_CHECKLIST.md` — separate author-facing materials.

## Official template and reproducible build

The GitHub Actions workflow [Cybersecurity manuscript build](../../.github/workflows/cybersecurity_build.yml) **downloads the official Springer Nature LaTeX ZIP** from the publisher and places the official class and bibliography style into this directory for the CI build. A legacy public-mirror copy of the files is also checked in; the CI step overwrites it. For manual compilation, replace these with the official class/BST first:

https://www.springernature.com/gp/authors/campaigns/latex-author-support

From `paper_a/venue_cybersecurity`, run

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript_review.tex
```

The figure paths begin with `../figures/` and expect the folder layout from the parent `paper_a/` directory. The generated CI artifact packages the full LaTeX source tree with the corresponding images preserving this layout.

## Editorial checks remaining

Complete all items in `SUBMISSION_CHECKLIST.md` before manually submitting. Source translation and successful TeX compilation do not establish acceptance of authorship, grant identifiers, conflict declarations, AI-assistance disclosures, ethical/reproducibility requirements, or the anonymization of public research code.
