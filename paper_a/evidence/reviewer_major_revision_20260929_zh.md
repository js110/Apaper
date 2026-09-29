# 2026-09-29 major-revision triage

Base reviewed commit: `a7fd7c396d9f6ba369cee49ac0a3cfa990c16b00`.

This note records the disposition of the supplied review. The rule used was: adopt comments that identify a real scientific, security, privacy, presentation, or reproducibility weakness; do not fabricate unavailable field data or change text to satisfy claims that are inconsistent with the repository state.

## Disposition

1. **Physical calibration / coverage premise — partially adopted.** The concern is scientifically valid. No new real multisource vehicular dataset is available, so no field-calibration result is invented. The manuscript is narrowed further to a conditional finite-domain evidence-certificate layer, the failed single-receiver transfer diagnostic remains a limitation, and zero-error simulation language is tightened. The focus condition now reports a seed-cluster-level one-sided exact upper bound rather than treating 2,400 event rows as independent evidence of zero population error.

2. **Crowdsensing-system scope — adopted.** The introduction, system model, architecture caption, contribution statement, discussion, and conclusion now say explicitly that the implementation is a provisioned certificate layer. Recruitment, incentives, reputation, Sybil-resistant enrollment, anonymous transport, dynamic partial participation, and network availability remain outside the proved relation.

3. **Formal security boundary — adopted.** A composed conditional acceptance proposition now defines acceptance, coverage, and compliance events and gives a union-bound failure expression over SNARK, signature, MiMC prehash, context-map, and freshness-state failures. Concrete implementation parameters are stated without inventing a single aggregate bit-security figure. This is still not a mechanized end-to-end proof.

4. **Privacy / leakage — adopted.** The manuscript now states that the gateway receives raw report bytes, that the deterministic report-bound context is binding rather than hiding, and that low-entropy candidate reports can be tested offline when the remaining context is known. A role-by-role privacy table was added, and repeated four-valued queries are identified as an explicit leakage channel.

5. **Empty `tab:point-zk` — rejected as a factual claim about the cited base commit.** At commit `a7fd7c3`, the table already contains the 2D row `408 / 164 / 268` and the 3D row `612 / 164 / 396`. No artificial change was made to “fill” an already populated table. Its caption now records the generator/source path, 16-bit bounds, and same-stack gnark/Groth16/BN254 provenance.

6. **Evaluation statistics and deployment extrapolation — partially adopted.** Existing paired seed bootstrap evidence is retained. The new seed-cluster zero-error upper bound is generated into `results_summary.json`. Wording is tightened around synthetic and UrbanNav-with-simulated-evidence results. New OBU energy, network latency, real multisource field trials, and signature/range/geometry component ablations are not claimed because those measurements do not exist in the archived artifacts.

## Minor comments adopted

- The manuscript now explicitly states that gnark uses the BN254 twisted-Edwards EdDSA construction and that it is not Ed25519.
- Finite-domain exactness and conservative quantization are made more visible in the architecture caption.
- `inconsistent/evidence failure` is distinguished explicitly from protocol `abort`.
- Data/code availability now matches the repository's public visibility.
- CI now pins Python 3.13 and direct NumPy/Matplotlib versions and runs on pull requests to `main`.

## Deliberate non-changes

The title is retained because it describes certification of a relation “for vehicular crowdsensing” rather than claiming an end-to-end crowdsensing architecture. The revised abstract and body now make the certificate-layer scope explicit. No field reliability, issuer independence, report truth, or end-to-end availability claim is added without supporting evidence.
