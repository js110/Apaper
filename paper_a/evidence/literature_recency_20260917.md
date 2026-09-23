# Reference-recency revision — 2026-09-17

Scope: respond to the author's preference for references from the last five years,
except where an older original method or exact experimental source is necessary.
This note supersedes the selection counts in `literature_update_20260915.md`;
that earlier search record and its raw metadata are preserved as history.

## Selection

The revised manuscript cites 23 entries: 20 scholarly works (including two explicitly
labelled preprints), one software release, one pinned dataset snapshot, and one
documentation resource. Of the scholarly works, 17/20 are from 2022–2026; the
three older papers are original methods used in the study. Across all entry types,
19/23 are from 2022–2026. Five articles are from Vehicular Communications, all
published in 2022–2025. No uncited entries are retained.

The rolling five-year cutoff is 2021-09-17. There are no borderline late-2021
publications in the current selection. Documentation access years do not turn a
resource into a newly published research article; resource counts are reported
separately above.

## Necessary older sources

| Key | Year | Reason retained |
| --- | --- | --- |
| Marzullo1990 | 1990 | Original threshold-based fault-tolerant sensor-fusion foundation explicitly inherited by this work. |
| Groth2016 | 2016 | Original Groth16 argument system implemented in the prototype. |
| MiMC2016 | 2016 | Original hash construction used in the signed-box circuit. |
| GraphGNSSData | 2021 | Exact pinned June 1 repository snapshot used by the receiver diagnostic; changing its year or citing another dataset would misidentify the experimental source. |

## Replacement sources and bounded claim mapping

Public-topic searches used OpenAlex and web indexing; DOI metadata were retrieved
using publisher/Crossref content negotiation on 2026-09-16. The six raw BibTeX
responses are in `recent_reference_metadata_20260916.json`. No unpublished
manuscript or reviewer text was sent to these services. Page-range encoding was
normalized to BibTeX double hyphens; article titles/acronyms were brace-protected.

| Key and DOI | Source inspected and locator | Use in the manuscript |
| --- | --- | --- |
| Suhag2023 — 10.1016/j.sysarc.2023.102952 | [Publisher article](https://www.sciencedirect.com/science/article/pii/S1383762123001315), indexed abstract; [paper abstract mirror](https://www.researchgate.net/publication/372580992_A_COMPREHENSIVE_SURVEY_ON_MOBILE_CROWDSENSING_SYSTEMS), Abstract. Direct publisher fetch returned 403. | Introduction: mobile crowdsensing collects observations from participating devices. Replaces Ganti2011 background citation; no historical priority claim. |
| Zheng2025BARM — 10.1109/JIOT.2025.3552447 | [IEEE record](https://ieeexplore.ieee.org/document/10930917/), access restricted; [paper abstract mirror](https://www.researchgate.net/publication/389971013_BARM_Blockchain-Assisted_Anonymous_Authentication_and_Reputation_Management_for_Mobile_Crowdsensing_in_Internet_of_Vehicles), Abstract; OpenAlex W4408564350. | Introduction and Section 2.1: vehicular sensing applications and BARM's anonymous authentication, reputation evaluation and blockchain-assisted identity management. Replaces the old fog-centric background framing. |
| Zhou2024 — 10.1016/j.comcom.2024.02.022 | [Publisher article](https://www.sciencedirect.com/science/article/pii/S0140366424000781), indexed Abstract and contribution summary; direct full-page fetch returned 403. DOI metadata confirmed volume 218 and pp. 198–208. | Section 2.1: PPVDA uses homomorphic MACs and secret sharing for private, verifiable inner-product aggregation. Only abstract-level functionality is described; no numerical performance comparison or full-text verification is claimed. |
| Ghani2025 — 10.1016/j.vehcom.2025.100921 | [Author institutional record](https://research.nu.edu.kz/en/publications/enhancing-security-and-trust-using-efficient-privacy-preserving-a/), Abstract and citation metadata; [publisher article](https://www.sciencedirect.com/science/article/pii/S2214209625000488), indexed Abstract. | Section 2.2: PUF/password/nonce-based two-factor authentication. Replaces Pham2018 in the target-journal selection, with rewritten prose rather than transferring Pham's trust-management claims. |
| Atmaca2024 — 10.1109/OJVT.2024.3360302 | [Author-hosted published PDF](https://blitzwas.github.io/Publications/OJVT24.pdf), p. 262 Abstract and pp. 263–264 contributions. | Section 2.2: approximate geo-indistinguishability, bounded query-location obfuscation and dummy queries. Replaces the generic GeoInd2013 contrast with a recent vehicular application; does not reattribute the original GeoI definition. |
| Zhang2025Sybil — 10.1038/s41598-025-28854-1 | [Published PDF](https://www.nature.com/articles/s41598-025-28854-1.pdf), p. 1 Abstract; [PubMed record](https://pubmed.ncbi.nlm.nih.gov/41272015/). Article number 44966 enriched from publisher/Crossref CSL metadata and PubMed; absent in the raw BibTeX response. | Sections 2.2 and 3: RSU-authorized short-term pseudonyms illustrate authorization controls against identity multiplication. Replaces Douceur2002 without claiming to originate the Sybil concept or to implement this authentication protocol. |

Removed entries: Ganti2011, Ni2017, Basudan2017, Pham2018, Douceur2002,
GeoInd2013, Hoeffding1963. Six recent entries replace seven older ones. The
Hoeffding-specific aside was removed; the explicit independence condition,
Poisson-binomial calculation and dependence-agnostic bound remain unchanged.
No experiment, result, author detail, or declaration was changed in this revision.
Compilation also exposed a pre-existing duplicate PDF destination after the
appendix table counter reset; the appendix now uses a distinct hyperlink anchor
namespace without changing its displayed table numbering.

## Review status

Agent checks cover metadata retrieval, the accessible source scope described
above, citation matching, recency exceptions, and compilation. The source access
scope is not a claim of full-text review for restricted articles. Human scientific
verification and submission approval remain pending, consistent with the existing
project evidence record.
