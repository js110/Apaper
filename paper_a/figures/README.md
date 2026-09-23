# Paper A figure revision — updated 15 September 2026

Eight figures are included in the author-review manuscript: architecture, challenge sequence, integer counterexample, and five experimental plots. The latter retain measured/simulated source data, including adverse outcomes. The budget plot now has three panels with separate scales; the normal false-rejection interval extends below zero and is shown in full, not interpreted as a negative physical rate. Cost panels separate 2D and 3D shapes and de-emphasize, but retain, all raw timings. Receiver coverage counts are calculated directly from the plotted scores.

## Reproduce experimental plots

From `revision_vehcom/paper_a`, run:

```sh
MPLCONFIGDIR=/tmp/paper-a-mpl python3 figures/render_results.py
```

`figure_manifest.json` records source hashes, transformations, software versions and accessible descriptions. Adjacent CSV files provide the plotted data. PDF and SVG are vector outputs; PNG previews are exported at 600 dpi. These choices are not a journal-compliance certification. The source experiments were not rerun or adjusted for this visual revision.

- `availability`: radius sensitivity, seed means and normal 95% intervals.
- `backend_costs`: both implementations, constraints and all 300 proving timings. Bars show sample p5–p95, not confidence intervals.
- `budget_tradeoff`: matched honest-miscoverage budgets; retains residual errors and reduced availability.
- `receiver_diagnostic`: all 157 matched epochs, including the ten-epoch gap; maximum absolute horizontal component, not Euclidean distance. This is a retrospective static sequence.
- `compile_scalability`: complete signed-box R1CS constraint counts from the new bounded compilation sweep. Resource-limited outcomes are missing values, not zero or inferred counts; the manuscript table reports all five. Regenerate with `uv run --with matplotlib python figures/render_compile_sweep.py experiments/compile_sweep_20260915T010554Z`. Its separate `compile_scalability_manifest.json` records provenance and transformations.

## Architecture provenance and description

`system_architecture.png` is an unmodified copy of OpenAI image generation through Codex, generated 6 September 2026. The service did not return a model version. Original output: `exec-00d25c5f-997c-40fe-a998-cb4cc09bfb86.png`. It is a 1536 × 1024 raster, not a vector image; no upsampling is claimed. At 6.1 inches wide it has approximately 252 effective dpi. Submission-resolution requirements remain to be checked with the journal.

Design instructions: white landscape canvas; restrained navy/blue/teal outline icons; three columns for signed evidence issuers, vehicle/prover, and gateway. Signed boxes flow to the vehicle; report and proof flow to the gateway. A separate challenge arrow originates at the gateway and points back to the vehicle. Task policy configures the vehicle and gateway. Evidence remains private. Show robust decision and ZK proof generation; verification and nonce consumption; four outcomes, with acceptance only for Valid. No deployed infrastructure, blockchain, physical source independence, or measurement claims. Replace long prose with icons and short labels.

The revised final output is `exec-e9fb5389-2ec2-4d59-b794-b177a1f9053d.png`, replacing the earlier icon-only layout. The center now shows threshold fusion, exact four-valued classification, and the ZK certificate within a private boundary. Two intermediate outputs were rejected because the Invalid geometry thumbnail incorrectly overlapped the policy. The delivered version uses explicit set relations instead, checked against the manuscript definitions. No automated reviewer score is claimed.

Accessible description: Signed evidence documents enter a vehicle's private proof computation. Threshold fusion constructs the set F of states covered by at least k boxes. Four cards distinguish a nonempty F inside P, a nonempty F disjoint from P, F intersecting both P and its complement, and empty F. A ZK certificate binds signatures, context and the exact decision. A gateway issues a challenge and checks the returned task-bound proof. It consumes the verified challenge and accepts only the valid outcome. The public disclosure strip is outside the private witness boundary.

Elsevier's journal AI policy, verified 6 September 2026, permits explanatory schematics with disclosure and author oversight: https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals . This architecture is a manuscript explanatory figure, not a graphical abstract. Draft disclosures are in the caption and manuscript; author review, exact version information if available, and final approval are pending. Do not represent automated inspection as author approval.
