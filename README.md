# JNCA submission

Active journal: **Journal of Network and Computer Applications** (Elsevier, elsarticle).

Main manuscript: [paper_a/venue_jnca/manuscript.tex](paper_a/venue_jnca/manuscript.tex). The final Chinese-revised science and English translation are preserved, with JNCA bibliography additions and minimal table formatting changes.

Standalone source code and experiments: https://github.com/js110/ZCRSC-PAPER

Only the active submission's English LaTeX chapters, eight figures, bibliography, Highlights, cover letter and CI build are retained on main. The complete earlier JISA and Cybersecurity material, analysis assets and duplicated experiments remain in [archive/pre-jnca-20261018](https://github.com/js110/Apaper/tree/archive/pre-jnca-20261018), and are recoverable through Git history.

Build: `cd paper_a/venue_jnca && latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript.tex`. Requires standard TeX Live with elsarticle.cls, elsarticle-harv.bst and mathematics/graphics packages. CI produces manuscript.pdf and a submission source ZIP. Compiling the source ZIP requires the standard Elsevier elsarticle TeX Live package.

Before actual submission, independently confirm the corresponding author's email, funder grant identifiers (including ambiguous characters in D2O25O185), author approval and required publication declarations.

Figures 1–3 use vector PDF artwork with companion SVG files. Image-model redraws, exact-label corrections and reproducible tracing instructions are documented in [figure_sources/README.md](paper_a/venue_jnca/figure_sources/README.md). The submission source archive includes all three required figure PDFs.
