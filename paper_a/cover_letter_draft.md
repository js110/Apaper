# Cover letter — author-review draft

Dear Editors of the Journal of Information Security and Applications,

We wish to submit “Privacy-Preserving Robust Spacetime Compliance under Byzantine Evidence: A Zero-Knowledge Framework for Vehicular Crowdsensing” for consideration as a research article.

The manuscript studies a security gap in privacy-preserving location verification: a zero-knowledge proof over one hidden coordinate can be cryptographically correct even when the underlying event is uncertain or some authenticated evidence sources are malicious. We formulate the verification target as a robust four-valued relation over private signed uncertainty boxes, with explicit Byzantine and honest-miscoverage budgets.

The work implements two Groth16/BN254 circuit backends with in-circuit EdDSA/MiMC verification and binds each proof to the authorized task, issuer roster, report, challenge, threshold, and expiry. A local gateway prototype reconstructs trusted public inputs, rejects context substitution, and atomically consumes a successfully verified challenge to prevent same-challenge replay within the stated execution model.

The evaluation separates security-relation validation from physical deployment claims. It includes 64,800 synthetic event-condition observations, matched miscoverage-budget analyses, a 787-state measured reference trajectory replay with simulated evidence, 300 measured zero-knowledge proofs, and a resource-bounded circuit compilation sweep. The manuscript explicitly treats real multisource positioning calibration and field deployment as external validation requirements rather than inferring them from simulation. The revised analysis additionally records the number of honest uncertainty boxes that miss the true event on every synthetic observation: wrong decisive outputs are absent whenever the theorem's $M\le r$ coverage premise holds in the tested focus conditions and appear only after that premise or the Byzantine budget is violated. A same-stack private point-in-policy Groth16 circuit is also reported as a deliberately weaker lower bound, quantifying the additional circuit cost of authenticated robust evidence semantics without presenting it as an equivalent security protocol.

We believe the manuscript fits JISA because its primary contribution is a privacy-preserving security certification mechanism with explicit trust assumptions, adversarial evidence handling, authenticated context binding, and reproducible cryptographic implementation, while vehicular crowdsensing serves as the application domain.

Sincerely,

Lei Zhang, corresponding author, on behalf of Lili He, Sheng Jiang, Linghui Lyu, and Lei Zhang

College of Information and Electronic Technology, Jiamusi University

8213662@163.com

---

Internal preparation note — remove only after confirmation: This letter has not been sent. Confirm all authors approve this manuscript and submission, that it is not simultaneously under consideration elsewhere, how the previous PCVCS manuscript relates to this work, and all required JISA declarations. No exclusivity, originality, rights, conflict-of-interest, or all-author approval statement has been asserted without confirmation.
