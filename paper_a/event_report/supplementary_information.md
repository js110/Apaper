# Supplementary information

**Article:** Privacy-Preserving Report-Bound Spatiotemporal Verification for Vehicular Crowdsensing  
**Journal:** Telecommunication Systems  
**Authors:** Lili He, Sheng Jiang, Shuang Chen, Lei Zhang  
**Affiliation:** College of Information and Electronic Technology, Jiamusi University, Jiamusi 154007, China  
**Corresponding author:** Lei Zhang, 8213662@163.com

The `prototype/` directory contains the software prototype and tests. `experiments/` contains the experimental records and reproduction instructions. The context-hiding candidate is an exploratory base-circuit experiment described in `安全修订与候选方案.md`; it is separate from the main protocol and results reported in the manuscript. Alongside the zero-knowledge arms, `experiments/nonsnark_baseline.log` records two anonymous non-zero-knowledge baselines — a BBS+ selective-disclosure credential over BLS12-381 and an RFC 9578 Privacy Pass token over P-384 — and the weak trusted-issuer control, measured under the same task and event shape and the same three-message handshake; `experiments/README.md` gives the run commands and `experiments/nonsnark_baseline_stats.txt` the recomputed statistics for all four arms. Both baselines are implemented from their published constructions with off-the-shelf cryptographic libraries in this repository, not from a deployed issuer, Origin or verifier.
