# Event-report proof experiment

This is a reproducible software benchmark of the actual BN254/Groth16 circuit in `../prototype`, not a vehicular field test or a measurement of a roadside unit. The random authority and issuer keys and all signed event coordinates are generated in software. The experiment does not establish the physical truth of the event, report confidentiality, production readiness or throughput under a network workload.

From `../prototype`, run:

```sh
EVENT_BENCH_RUNS=30 go test -run '^TestBenchmarkExperiment$' -count=1 -timeout=30m -v | tee ../experiments/benchmark.log
```

Set `GOMAXPROCS` if comparing runs with a fixed worker limit. The first uncached run requires the Go modules pinned by `go.mod` and `go.sum`; package downloads and Go compilation are excluded from reported timings. Set `GOMODCACHE` or `GOPROXY` as appropriate for the network. To ensure a shell pipeline returns a failing Go test exit status, enable `pipefail` or redirect both streams to the log instead of piping through `tee`.

The opt-in test compiles the R1CS and performs circuit-specific Groth16 setup once; their wall-clock durations are reported separately and are not repeated 30 times. It creates one software fixture, runs one warm-up, then produces and verifies 30 proofs over different synthetic report/context statements. Each timed proof and verification is checked for an error and every proof is serialized using the gnark `WriteTo` method. Each raw sample logs proving and verification elapsed nanoseconds, serialized proof bytes and separately serialized public-witness bytes. Statements, signatures, witness creation and serialization are outside the prove and verify intervals; task creation, issuance, networking, state-store checks, encryption, key distribution and real hardware sensing are not measured. The source SHA-256 values in the log identify the relevant circuit, fixture, module files and experiment harness. Any subsequent circuit change requires rerunning the experiment.

The Groth16 setup generated here is local to a research run and does not demonstrate a secure production setup ceremony. Repeat on the desired platform and under a controlled load; sample timings may vary with scheduling, thermal conditions and background processes. Compare methods only after matching their functionality, threat assumptions, operations measured and runtime environment.

## Additional controlled experiments

- `context_ablation.log`: the full relation and a purpose-built no-context circuit were checked under original, substituted report, substituted challenge and substituted task contexts. The attacker retains a valid credential and original receipt, not the issuer key. The full relation is checked with the R1CS solver; the ablated relation is additionally proved and verified using Groth16. Run `go test -run '^TestContextBindingAblation$' -count=1 -v` in `prototype/`.
- `ablation_cost.log`: the full rectangle circuit and `bearerCircuit` use the same fixture, task and event and a fixed valid witness. Each uses a separately generated local setup, one warm-up and 30 sequential measured proofs and verifications. Run `EVENT_BINDING_COST=1 go test -run '^TestBindingCostExperiment$' -count=1 -v` in `prototype/`. Timed operations exclude fixture construction, setup and witness creation. This is an internal ablation, not an implementation of a published baseline.
- `region_scale_{4,6,8}.log`: 30 proof and verification measurements per independently compiled region circuit, with one warm-up and one setup each. The inputs are synthetic; all cells are populated, and the same event is proved. Run `python3 experiments/run_region_scaling.py` from the project directory. The script changes the compile-time depth in temporary copies; the eight-level production prototype is unchanged. Source hashes in each log identify the generated variant.

The experiments were run sequentially on the Apple M1 system recorded in the region logs; they are not field or network measurements. `tests_after_ablations.log` records the non-opt-in test suite after adding the new tests.
