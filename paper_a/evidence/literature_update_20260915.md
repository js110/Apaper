# Literature expansion — 15 September 2026

Scope: author-requested expansion to at least 20 references, with relevant Vehicular Communications work. No experiment or result was changed. This is a targeted contextual search, not a systematic review.

Searches used OpenAlex (`vehicular crowdsensing privacy`, eight discovery records), publisher-indexed web searches, DOI/Crossref content negotiation, and author/institutional repositories. Only public topic keywords and publication identifiers were sent externally. The unpublished manuscript and reviewer material were not uploaded.

There are now 24 individually cited entries: 21 scholarly works (including the two already-cited preprints BFT-PoLoc and CRSF) and three software/data/documentation resources. Five of the 14 additions are Vehicular Communications articles. No `nocite` command or uncited padding is used.

## Metadata and access record

`added_reference_metadata_20260915.json` preserves all 14 DOI content-negotiated BibTeX records returned by the citation-management converter. The final bibliography normalizes keys, UTF-8 page-range mojibake, LaTeX accents, escaped ampersands, acronym capitalization, and proceedings entry types. Original article numbers are retained as pages, not invented page ranges. Ganti's initials were cross-checked against the author's Stony Brook record. BCS-LPP is dated 2024 (volume 45), despite 2023 in its DOI.

The table below maps each addition to its intended claim and source locator. Summaries are deliberately restricted to the documented objective/method, without importing reported speedups or making unsupported claims of absence. Several publisher pages returned 403 or robot checks on direct retrieval; publisher-indexed abstracts and the explicitly listed abstract reprints were available instead. These are not full-text verification. Human verification and final scientific approval remain pending for all additions.

| Key | Manuscript use / locator | Content evidence and access scope |
| --- | --- | --- |
| Ganti2011 | Introduction: device-based collective sensing | [Author institution record](https://researchconnect.stonybrook.edu/en/publications/mobile-crowdsensing-current-state-and-future-challenges/), abstract and bibliographic fields opened |
| Ni2017 | Introduction and Related work 2.1: location-aware fog sensing, privacy and fairness | [Author-hosted IEEE paper](https://uwaterloo.ca/scholar/sites/ca.scholar/files/sshen/files/254.pdf), p.146 abstract/introduction and pp.147–148 architecture/applications opened |
| Basudan2017 | Introduction and Related work 2.1: private road-surface monitoring | DOI 10.1109/JIOT.2017.2666783; publisher title/metadata and OpenAlex abstract checked; IEEE page robot-blocked, no full-text check |
| Cheng2023 | Related work 2.1: anonymous authentication plus reliability/reputation | DOI 10.1109/JIOT.2023.3259961; publisher title/metadata and OpenAlex abstract checked; IEEE page robot-blocked, no full-text check |
| Shen2024 | Related work 2.1: BCS-LPP privacy and fairness design | [Publisher preview](https://www.sciencedirect.com/science/article/abs/pii/S2214209623001547), indexed abstract, highlights and introduction; direct page 403. DOI metadata and publisher API confirmed title and publication date. Full text not checked |
| Pham2018 | Related work 2.1: selective linkability and contextual event trust | [Publisher-authorized abstract reprint](https://trid.trb.org/View/1541044), abstract opened; ALRS and ATMS descriptions. Publisher preview cross-checked; full text not checked |
| Sultana2024 | Related work 2.1: cooperative Sybil association | [Publisher-authorized abstract reprint](https://trid.trb.org/View/2459281), abstract opened; DTW and roadside DST roles. Full text not checked |
| Mdee2022 | Related work 2.2: application effects of privacy mechanisms | [Author institution record](https://avesis.ncc.metu.edu.tr/yayin/11b20f7a-5013-44d5-ad96-a822fbb35318/impacts-of-location-privacy-preserving-schemes-on-vehicular-applications), abstract and metadata opened |
| Wang2025ZKAuth | Related work 2.2: ZK-based identity authentication | [Publisher-authorized abstract reprint](https://trid.trb.org/View/2608666) opened; [publisher preview](https://www.sciencedirect.com/science/article/pii/S2214209625001032) indexed abstract cross-checked. Formal proofs and experimental tables not checked |
| GeoInd2013 | Related work 2.2: randomized location disclosure versus policy decision | [Author preprint](https://arxiv.org/abs/1212.1984), abstract, author list and published CCS DOI opened |
| Douceur2002 | Evidence model: multiple identities do not imply independent authorities | [Author's Microsoft Research record](https://www.microsoft.com/en-us/research/publication/the-sybil-attack/), abstract opened |
| Groth2016 | Prototype: attribution of the implemented proof system | [UCL author repository](https://discovery.ucl.ac.uk/id/eprint/1501201/), abstract and published DOI opened |
| MiMC2016 | Prototype: attribution of the implemented hash family | [DTU author manuscript](https://backend.orbit.dtu.dk/ws/files/128048431/492.pdf), cover metadata and pp.1–3 abstract/introduction opened |
| Hoeffding1963 | Honest miscoverage paragraph: independence required for independent-summand bound | [Publisher record](https://www.tandfonline.com/doi/abs/10.1080/01621459.1963.10500830), indexed abstract and DOI metadata; direct page blocked. No new numerical application of this inequality |

Two existing metadata gaps were also resolved:

- UrbanNav: DOI content negotiation confirms journal name and article locator `navi.602` (volume 70, issue 4, 2023).
- GraphGNSSData: the GitHub API for commit `e9e4c6a4ded5dc7f2813265a76a56b280f714a3f` returned committer date `2021-06-01T00:12:23Z`. The bibliography year now refers explicitly to this repository snapshot, not the measurement or initial publication year. API: https://api.github.com/repos/weisongwen/GraphGNSSLib/commits/e9e4c6a4ded5dc7f2813265a76a56b280f714a3f

## Interpretation boundary

The comparison distinguishes published target functions from this manuscript's formal relation; it does not assert that all cited systems lack location validation, does not claim a new cryptographic primitive, and does not rank unmatched security or timing experiments. BCS-LPP is acknowledged as performing worker sensing-location verification. The narrower contribution is universal classification of a threshold-supported uncertainty set. Existing closest-work discussion and preprint labels are preserved.

Machine checks: `citation_validation.json` checks syntax, required fields, duplicates, count and manuscript agreement. `artifact_audit.json` also checks the rendered bibliography count. Neither record is a human source-verification certificate.
