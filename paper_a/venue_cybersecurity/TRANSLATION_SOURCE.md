# Translation provenance and editorial scope

The research manuscript text in `translated_from_chinese/` was retranslated section-by-section **from the final six-chapter revised Chinese manuscript**. Its verified local source at translation time was `论文A_中文六章合并修订稿.md`, SHA-256:

`81e0e9bf2fde0c1d29b3ec7cf1a6c7cb1cb87a4f80abe17b780bac3134dfa0db`

That Chinese manuscript has six numbered chapters, Tables 1–14 and A.1, and eight figures. The source file is a user-reviewed local working artifact and is not embedded in this public repository's manuscript submission to avoid unintended duplication.

## Mapping

- `00_abstract.tex` — Chinese abstract and keywords
- `01_introduction.tex` — Section 1
- `02_related_work.tex` — Section 2 and Table 1
- `03a_system_model.tex`, `03b_decisions.tex`, `03c_protocol.tex`, `03d_circuits.tex` — Section 3 and Table 2
- `04a_security_model_soundness.tex`, `04b_security_protocol_privacy.tex` — Section 4 and Tables 3–4
- `05a_setup_and_protocol_tests.tex`, `05b_robustness_and_ablation.tex`, `05c_comparison_and_performance.tex`, `05d_discussion_conclusion.tex` — Sections 5–6 and Tables 5–14
- `06_appendix.tex` — Appendix A and Table A.1

The earlier English `paper_a/paper_a.tex` was **not** reused as the prose source of this translation. Existing BibTeX keys, numerical experiment records, figure assets, technical spellings, and cryptographic library configuration were consulted to preserve referential consistency; changes in technical substance need separate author review.

The anonymous manuscript includes these fragments with `\\input` directives. The identified manuscript uses exactly the same fragments; only author/title-page declarations differ. The official Springer Nature class and reference style are fetched from the publisher by the build workflow before compilation.

## Limits before manual submission

The translation needs a final bilingual editorial audit by the authors. All four authors must check attribution and contribution statements, corresponding email and institution, competing interests, grant code `D2O25O185` (letter O), the journal's required disclosure language, and source-code access compatible with anonymous review. Passing LaTeX compilation does not establish editorial or methodological acceptance.
