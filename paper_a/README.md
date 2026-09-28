# Paper A — JISA manuscript and reproducible evidence

Updated 2026-09-27. Target: **Journal of Information Security and Applications (JISA)**, Research Article. The manuscript is framed around privacy-preserving security certification, authenticated uncertainty, Byzantine evidence, and zero-knowledge verification. Formatting, bibliography, reproducibility, and source-package checks are automated in CI; final author approval and any live Editorial Manager prompts remain outside the repository.

Open `paper_a.pdf` for the manuscript, `research_audit_zh.md` for the original internal
assessment, and `revision_response_zh.md` for the current response and unresolved
items. `paper_a.tex` and `references.bib` are the editable sources. The old
`../pcvcs_vehcom.tex` is a separate predecessor and is not the Paper A manuscript.

## What is implemented

- Four-valued robust compliance over inclusive quantized boxes.
- Native lower-corner maximum depth and exact threshold-subset enumeration.
- Two real Groth16/BN254 circuits with in-circuit EdDSA/MiMC signatures, coordinate
  checks, distinct-key checks, and authenticated context. EdDSA is not Ed25519.
- 30 proofs for each of five circuit shapes per backend: 300 measured proofs.
- 27 synthetic conditions × 30 seeds × 80 events = 64,800 observations.
- One UrbanNav reference trajectory: 787 states, 786 seconds, simulated evidence
  under two error models and 30 randomized evidence realizations per model.
- Seed denominators and undefined conditional rates are preserved; a paired
  bootstrap is recorded separately from marginal normal intervals.
- Matched r=0/1/2 miscoverage-budget ablation: 194,400 condition evaluations of
  the same 64,800 randomized base observations, not independent expanded data.
- A task/report/challenge-bound local gateway with real proof integration and
  race-detector tests, including eight-copy concurrent replay rejection.
- An exploratory diagnostic of published static receiver outputs: 157 matched
  epochs, 78 calibration / 10 gap / 69 evaluation; no multisource claim.
- A resource-bounded, compile-only sweep: 32 complete signed-box circuit
  configurations, 27 completed and five stopped at the sampled RSS limit.
  These measurements do not include setup or proof generation at larger sizes.
- A pinned reproduction of the public ZKLP implementation at commit
  `e8e321524982ddd9dddea37db6fa352529db62c4`, plus a same-runner subset
  benchmark of this work and a source-bounded 2024--2026 quantitative context table.

The JISA branch is compiled in GitHub Actions on every manuscript change and exports a flat Editorial Manager source package. Its bibliography currently contains 25 cited entries: 23 scholarly works and two data/software resources. Twenty of the 23 scholarly works are from 2022–2026; three original
method papers and the exact pinned dataset snapshot are the necessary older
sources. The current bibliography remains technically relevant, but the JISA revision should be rechecked for venue-specific literature positioning before submission. Current
selection, recency exceptions and source-access notes are in
`evidence/literature_recency_20260917.md`; the earlier search record is preserved
in `evidence/literature_update_20260915.md`. Author
confirmation items are in `submission_confirmations_zh.md`; the prepared cover
letter is `cover_letter.md`. These checks do not constitute editor or publisher approval.

The 2026-09-22/23 full recheck is documented in
`evidence/manuscript_recheck_20260923_zh.md`. The additional reproducibility audit
(`python3 audit_scientific.py --reproduce`) passes 29 checks, including complete
synthetic and trajectory replay regeneration without overwriting raw records.

The subsequent style revision used the installed `academic-deweight-hybrid`
skill. See `evidence/style_revision_20260923_zh.md` and the retained before/after
diff. Twelve protected-content checks pass; no AI-detector score is claimed.

After the style check, the user requested deferring figure and general AI
disclosures to submission preparation. These records now reside in
`submission_disclosure_notes.md`, together with a blank author-contribution
worksheet. The style audit describes the preceding version; its hashes are
historical, not a claim that the subsequent disclosure edits left captions unchanged.

Table 1 compares eight related systems and the present prototype in
three functional groups. The evaluation section additionally gives a quantitative
2024--2026 context table and a pinned same-runner ZKLP reproduction. Row-level
evidence and interpretation boundaries are in `evidence/comparison_table_20260917.md`;
raw comparison records are `experiments/zklp_same_runner.json`,
`experiments/ours_same_runner_subset_n3_d2.json`, and
`experiments/recent_work_comparison.json`.

The experiment uses a native subset oracle for geometry decisions. The semantic
output label `robust_depth` is historical; it does not indicate that the ZK depth
circuit was invoked for every simulation event. Neither simulation runs the full
proof pipeline per event. Cryptographic timings come only from Go benchmarks.

## Reproduction

```bash
cd paper_a/prototype
python3 -m unittest -v test_robust_depth.py
cd zkdepth
GOCACHE=/tmp/pcvcs-paper-a-go-cache go test -v ./...
GOCACHE=/tmp/pcvcs-paper-a-go-cache go test -race -run TestGatewayBoundReportAndReplay -v ./...
GOCACHE=/tmp/pcvcs-paper-a-go-cache go run ./cmd/bench --geometry subset --n 4 --d 3 --repetitions 30
GOCACHE=/tmp/pcvcs-paper-a-go-cache go run ./cmd/bench --geometry depth --n 4 --d 3 --repetitions 30
```

```bash
cd paper_a/experiments
MPLCONFIGDIR=/tmp/pcvcs-mpl python3 run_semantic_evaluation.py
MPLCONFIGDIR=/tmp/pcvcs-mpl python3 run_semantic_evaluation.py --miscoverage-budget 1 --output semantic_results_r1.json
MPLCONFIGDIR=/tmp/pcvcs-mpl python3 run_semantic_evaluation.py --miscoverage-budget 2 --output semantic_results_r2.json
MPLCONFIGDIR=/tmp/pcvcs-mpl python3 summarize_ablation.py
MPLCONFIGDIR=/tmp/pcvcs-mpl python3 run_trace_evaluation.py
MPLCONFIGDIR=/tmp/pcvcs-mpl python3 summarize_results.py
python3 -m unittest -v test_receiver_calibration.py
python3 run_receiver_calibration.py
cd ..
/Library/TeX/texbin/latexmk -pdf -interaction=nonstopmode -halt-on-error paper_a.tex
python3 audit_artifacts.py
```

Python requires NumPy and Matplotlib. Go dependencies are pinned in `go.mod` and
`go.sum`. Rerunning a benchmark generates a fresh experimental setup and keys;
do not treat these as a production setup ceremony. The output flag is optional;
use a new filename to preserve historical measurements. No SUMO installation is
needed for these experiments.

## Evidence provenance and scope

The additional compilation sweep is recorded in
`experiments/compile_sweep_20260915T010554Z/`, including the fixed plan, source
hashes, per-case logs and all resource-limited outcomes. To run a new sweep:

```bash
uv run --with psutil python experiments/run_compile_sweep.py
```

To regenerate its plot from the existing results:

```bash
uv run --with matplotlib python figures/render_compile_sweep.py experiments/compile_sweep_20260915T010554Z
```

`experiments/zkdepth_*_formal.json` records the original depth runs;
`experiments/subset_*_formal.json` records the matched subset runs. Files without
`formal` in their name are preliminary runs and are excluded from manuscript
tables. The two backend batches were measured at different times on the same
machine, not interleaved. The `formal` suffix indicates 30 repetitions, not a
formal statistical certification.

UrbanNav source: https://github.com/IPNL-POLYU/UrbanNavDataset, the
UrbanNav-HK-Medium-Urban-1 Ground Truth link. Downloaded 2026-09-05.
`UrbanNav_TST_GT_raw.txt` SHA-256:
`9d48bb497878aafbd17290789560394c72ecafec20c9e0eaff448418695d92bf`.
The file is publicly downloadable; redistribution permission has not been
established. Do not include it in a public release before checking dataset terms.
Its positions are reference states; no measured receiver error or calibration is
inferred from them. Quantization and the local projection introduce additional
physical-model approximation not covered by the finite-box theorem.

`calibration_protocol.md` fixes the exploratory static-receiver diagnostic choices.
`receiver_calibration.json` preserves pinned GraphGNSSLib source URLs and hashes;
`receiver_residuals.csv` records the matched residuals and chronological segments.
The input files in `graphgnss_tst2/` are publicly downloadable but their data
redistribution permission remains unverified. The recorded RTKLIB output uses
combined processing, so its chronological split is retrospective, not a causal
online evaluation. Only one constant reference position and one receiver are
available. Appendix A reports failed transfer of the fixed radius (2/69 evaluation
containment), without tuning it against the evaluation segment or asserting a
general receiver failure rate. This is not the 2021 moving UrbanNav replay.

`gateway.go` now supplies a local task-authorized report-verification harness:
canonical task/report/challenge context, full-field signed digest, trusted-input
reconstruction, expiry and atomic in-process challenge consumption. Its tests
cover substitution, cross-challenge replay and eight concurrent copies. The
roster checks reject repeated configured trust-domain labels; they cannot prove
independent real-world control. Durable replay storage, network deployment,
physical issuer enrollment, report-content truth and network anonymity remain
outside the implementation. Fresh challenges can still carry duplicate reports.
A missing issuer causes abort.

## Formatting status

The JISA branch now uses the current Elsevier `elsarticle` submission structure with numeric references. Template provenance and unresolved journal-specific points are recorded in `venue_template_jisa/COMPLIANCE.md`. The previous bundled 3.4 class has been upgraded to the maintained 3.4c body aligned with the CTAN 3.5 (2026-01-09) release metadata. The manuscript selects `preprint,review,12pt` with line numbers; it does not try to emulate Elsevier's final production layout.

Run `python3 export_latex.py` after a fresh LaTeX/BibTeX compilation to create `paper_a_jisa_submission.zip`. The exporter refuses to package the manuscript if the two newly added JISA references are missing from `paper_a.bbl`. The exporter flattens figure paths and includes
the class, bibliography style and required figures, without experiment raw data.
The ZIP contains only neutral submission-source metadata and no internal draft banner.
The main manuscript remains `paper_a.tex`.

JISA is the current target venue. Its live Guide for Authors and Editorial Manager prompts should still be checked at upload because publisher instructions can change. Author order, affiliation, correspondence, funding, CRediT roles, AI-use disclosure, and data/code availability are represented in the current manuscript or repository records. The manuscript intentionally contains no competing-interest section at the author's request; any portal-level declaration should follow the live submission form. No external manuscript submission is performed by this repository.

GitHub Actions build: `.github/workflows/jisa-build.yml` regenerates semantic diagnostics and the backend-cost figure, reruns the Go prototype and point-ZK baseline, pins and reruns ZKLP on the same runner, rebuilds the recent-work comparison record, recompiles LaTeX/BibTeX, and exports the flat Editorial Manager source package.

## JISA-specific security diagnostics

The JISA revision records event-level honest-miscoverage counts in `experiments/jisa_security_diagnostics.json` and adds a same-stack point-in-policy Groth16 lower-bound circuit under `prototype/zkdepth/point_baseline.go`. The point circuit is intentionally weaker and is used only to quantify structural circuit overhead, not as an equivalent trust/security baseline. The manuscript also cites the 2026 JISA ADSC-SNARK work to clarify the boundary between authenticated-data SNARK primitives and the present robust uncertainty relation.
