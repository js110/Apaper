Dear Editors of the Journal of Information Security and Applications,

We wish to submit “Zero-Knowledge Certification of Robust Spacetime Compliance under Byzantine Evidence for Vehicular Crowdsensing” for consideration as a research article.

The manuscript addresses a security gap in privacy-preserving location verification. A zero-knowledge proof over one hidden coordinate can be cryptographically valid even when the underlying event is uncertain or some authenticated evidence sources are Byzantine. We therefore certify a stronger object: whether all threshold-supported states implied by private signed uncertainty evidence satisfy an authorized spacetime policy.

The contribution is a report-bound security relation and its implementation, rather than a new cryptographic primitive. Two Groth16/BN254 circuit backends verify EdDSA/MiMC-signed evidence and bind each proof to the task, issuer roster, report, threshold, challenge, and expiry. The gateway prototype rejects evidence tampering, decision/report substitution, stale or unknown challenges, and cross-challenge replay. A same-stack hidden-point circuit is included only as a lower-bound reference for the additional cost of authenticated robust evidence semantics.

The evaluation combines adversarial protocol tests, 64,800 synthetic event-condition observations, matched miscoverage-budget diagnostics, a 787-state measured reference-trajectory replay with simulated evidence, real proof-generation measurements, resource-bounded circuit compilation, and a pinned same-runner reproduction of the open-source ZKLP implementation. The analysis directly records the number of honest boxes missing the true event and observes no wrong decisive output when the theorem premise $M\le r$ holds in the tested focus conditions. The manuscript explicitly separates cryptographic guarantees from physical calibration and does not present simulated evidence as field validation.

We believe the work fits JISA because its primary contribution is an applied information-security mechanism combining privacy-preserving verification, authenticated evidence, Byzantine fault assumptions, replay-resistant context binding, and reproducible cryptographic implementation. Vehicular crowdsensing is the application domain rather than the source of the security claim.

Sincerely,

Lei Zhang, corresponding author, on behalf of Lili He, Sheng Jiang, Linghui Lyu, and Lei Zhang

College of Information and Electronic Technology, Jiamusi University

8213662@163.com

