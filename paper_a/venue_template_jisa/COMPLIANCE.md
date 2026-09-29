# JISA LaTeX and submission compliance notes

Checked: 2026-09-23.

## Target and template basis

Target journal: **Journal of Information Security and Applications (JISA)**, Elsevier, ISSN 2214-2126.

JISA does not expose a separate journal-specific LaTeX class in the sources that were accessible during this check. Elsevier's current LaTeX instructions recommend the **elsarticle** class and BibTeX, and provide a numbered-reference template. The JISA Guide for Authors endpoint on ScienceDirect returned HTTP 403 during this check, so no unsupported journal-specific layout requirement is asserted here.

Template sources checked:

- Elsevier LaTeX instructions: https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions
- Elsevier-maintained elsarticle repository: https://github.com/STM-Document-Engineering/elsarticle
- CTAN elsarticle package: https://ctan.org/pkg/elsarticle

CTAN reports **elsarticle 3.5, dated 2026-01-09**. Its published 2026 changelog records only copyright-year and support-email changes relative to 3.4c. The repository branch still exposes the 3.4c class body. The local submission class therefore uses that official maintained body with the documented 3.5 release metadata. This avoids retaining the older 3.4 class previously bundled for the Vehicular Communications draft.

## Manuscript layout

The manuscript uses:

```latex
\documentclass[preprint,review,12pt]{elsarticle}
```

This follows the Elsevier submission template. The `review` option increases line spacing for peer review. The manuscript does **not** attempt to reproduce the publisher's final 1p/3p/5p production layout.

References use `elsarticle-num.bst` and numeric citations.

## Editorial Manager packaging

Elsevier's current LaTeX instructions state that Editorial Manager does not process LaTeX submissions with subfolders. The exporter therefore:

1. rewrites all `figures/...` references to flat filenames;
2. places figures, `.tex`, `.bib`, `.bbl`, `.cls`, and `.bst` at one ZIP level;
3. checks that the ZIP contains no path separators;
4. writes a SHA-256 manifest.

Run:

```bash
python3 export_latex.py
```

Expected output:

```text
paper_a_jisa_latex_draft.zip
```

## Highlights

Elsevier's current generic guidance is 3--5 highlights, each no more than 85 characters including spaces. The draft `highlights.txt` has been rewritten to satisfy that limit. Elsevier's support page states highlights are generally supplied as a separate editable upload; the exact JISA submission-screen requirement should be confirmed when the authors open the final Editorial Manager submission.

## Still requiring author confirmation

These cannot be inferred from the manuscript or repository and must be confirmed before upload:

- competing-interest declaration;
- final CRediT contributions;
- sponsor/funder role wording;
- all-author approval;
- final generative-AI disclosure, if required by the submission form;
- public data/code release arrangement and third-party redistribution permissions;
- relationship to any prior/submitted PCVCS manuscript and confirmation of no prohibited overlap.

This file documents formatting provenance only. It is not publisher approval or a guarantee of editorial compliance.
