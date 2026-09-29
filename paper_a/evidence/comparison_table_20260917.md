# Related-work comparison, Table 1 — revision 2

Date: 2026-09-17. Display ID: `tab:related-work`. Creator: Codex-assisted
authoring; accountable author review and scientific approval pending.

Scope: eight individually identified related systems plus the present prototype.
The former merged Marzullo/BFT-PoLoc and ZKLP/vehicle-policy rows were removed.
Marzullo remains cited in the prose as the original fusion foundation. BARM,
PPVDA, and BCS-LPP supply recent application context. The table is a functional
comparison, not an experimental benchmark or exhaustive feature-absence audit.

The four columns are Work, Checked object, Evidence / trust model, and Privacy /
output interface. The last column combines protected information and output to
fit the review page at 10-point type without image scaling. Three labelled groups
separate participation, fusion, and zero-knowledge certification. Every cited
system has its own row and year. No checkmark/cross matrix is used.

## Row-level evidence mapping

| Row | Source and locator | Bounded content |
| --- | --- | --- |
| BARM | DOI 10.1109/JIOT.2025.3552447; abstract access and metadata in `literature_recency_20260917.md` | Anonymous authentication, private reputation evaluation/updates and blockchain-assisted identity management. No new claim about its uncertainty geometry or Byzantine threshold. |
| PPVDA | DOI 10.1016/j.comcom.2024.02.022; publisher-indexed abstract and contributions, access limitations recorded in `literature_recency_20260917.md` | Private multidimensional inputs, inner-product aggregation, homomorphic MACs and secret sharing, malicious model, correctness/integrity verification. No performance number or claimed absence. |
| BCS-LPP | [Publisher preview](https://www.sciencedirect.com/science/article/abs/pii/S2214209623001547), indexed Abstract, Highlights, Introduction and Worker location privacy sections rechecked on this date; direct full-page access remains limited | Geohash, order-preserving encryption, deposits, selectable location privacy and submitted-location validation. The table explicitly credits location validation rather than implying no location check. |
| BFT-PoLoc | [Pinned author preprint](https://arxiv.org/abs/2403.13230v2), Abstract opened | IP-address localization from Internet delays, Byzantine-resistant geometry, distance inference and multilateration. Privacy is explicitly not assessed here; this does not assert absence of privacy protection. |
| PG | [Author institutional record](https://ir.cwi.nl/pub/34722), Abstract and citation metadata opened | Malicious sensors and aggregation servers, privacy of inputs and result, guaranteed output delivery. No matched performance comparison. |
| CRSF | [Current arXiv version](https://arxiv.org/abs/2609.01096v3), Abstract, version history, and evaluation summary inspected | Sensor-server collusion, agreement on submissions, private fusion, correctness with explicit abort and liveness. The bibliography is pinned to v3; the manuscript uses only source-supported headline performance context. |
| ZKLP | [UCL author record](https://discovery.ucl.ac.uk/id/eprint/10211442/), Abstract and metadata opened | Region membership/proximity proofs, private coordinates and floating-point geometry. No claim that the original system authenticates physical measurements or lacks other capabilities. |
| Vehicle policy | [Publisher chapter](https://link.springer.com/chapter/10.1007/978-3-032-00642-4_20), Abstract, Section 2.2 and system-model paragraphs on Prover/Verifier opened | A trusted witness signs location claims; the verifier checks a signed trajectory satisfying territorial requirements without disclosure of raw trajectory. Kept separate from single-coordinate geometric predicates. |
| This work | `paper_a.tex`, Sections 3–5; existing prototype and artifact evidence | All threshold-supported reference-event states; signed uncertainty boxes, fixed roster, separate Byzantine and honest-miscoverage budgets; private boxes/signatures and a portable four-valued decision proof. Missing signatures remain protocol abort, not the inconsistent decision. |

This is an original textual synthesis, not a copied table or reused graphic.
There are no axes, numerical denominators, or statistical population in this
conceptual comparison. Protocol-specific leakage and threat assumptions are
not interchangeable; the caption and note make that explicit. All restricted
source summaries remain limited to the recorded abstract/preview scope.

No experiments, measurements, bibliography entries, or author declarations were
changed. Human verification remains pending; local consistency and rendering
checks do not establish comparative security or novelty.


## Revision 3: quantitative recent-work context (2026-09-27)

The JISA revision adds a second, quantitative comparison layer in the evaluation section. This is intentionally separate from the functional Table 1 above.

1. **Pinned external reproduction.** The public ZKLP repository is pinned to commit `e8e321524982ddd9dddea37db6fa352529db62c4`. The first upstream ZKLP32 test vector is compiled and proved on the same GitHub Actions Ubuntu runner used for a fresh subset `(n,d)=(3,2)` benchmark of this work. Both use Groth16/BN254, but the upstream ZKLP code uses its gnark fork based on v0.9.1 while this work uses gnark v0.14.0. The two relations are not security-equivalent.
2. **Observed same-runner values.** ZKLP smoke: 19,467 constraints, 515.529 ms median proving time, 1.7385 ms median verification, 196-byte proof, 140-byte public witness. This work, subset `(3,2)`: 32,474 constraints, 645.136 ms median proving time, 1.5475 ms median verification, 164-byte proof, 556-byte public witness. Each timing summary uses 10 proofs after one setup.
3. **Historical upstream artifact.** ZKLP's repository also stores an m6i.xlarge benchmark artifact with 137 rows, 21,878 constraints and a 270.03 ms median proving time. Because the pinned current code compiles to 19,467 constraints in the smoke run, the manuscript explicitly treats this as artifact/code-version drift and does not infer a speedup or regression from the historical artifact.
4. **Source-reported context only.** BFT-PoLoc (2024), PG (2024), Vehicle ZK-PoL (2025), and CRSF (2026) are included with their reported evaluation scale and headline measurements. Their runtimes are not normalized against this work because their certified objects, hardware, and cryptographic/network protocols differ.

Generated records:
- `experiments/zklp_same_runner.json`
- `experiments/ours_same_runner_subset_n3_d2.json`
- `experiments/recent_work_comparison.json`
- CI workflow: `.github/workflows/jisa-build.yml`

The purpose is to provide reproducible external context without turning heterogeneous systems into an invalid ranking.
