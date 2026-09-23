# Vehicular Communications format adaptation

Target: Vehicular Communications (Elsevier), full research article, initial submission.
Checked: 2026-09-05. Selection is based on topical fit, not predicted acceptance.

## Verified official sources

- Scope: https://shop.elsevier.com/journals/vehicular-communications/2214-2096
  Explicit topics include protocol design/testing/verification, security, data
  collection and dissemination, and Internet of vehicles. These match Paper A.
- Publisher LaTeX instructions:
  https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions
  Links the official elsarticle package and describes source submission.
- Downloaded package (link from the preceding page):
  https://assets.ctfassets.net/o78em1y1w4i4/4MpsJHO0MOJ2xZuwGTAbOZ/7bc64af36477c5d6cfce335a1f872363/elsarticle.zip
  Preserved as `elsarticle-official.zip`; extracted files remain unchanged.
  The downloaded bundle contains elsarticle 3.4 (2024), not the locally installed
  3.4c. This is the publisher-linked package, not a claim to the newest release.

SHA-256 of the downloaded ZIP:
`0b093093e84db49f99bcc9a7c3f69ed1fb61b0147c6d296427aff7963e7f50f6`.
Generated class:
`01addb492c5d075b320636ac3a30d8a5762fa937220dea07a5e107042d25384d`.
Numeric bibliography style:
`0db2e53b2378cbe5815e436c1afe9dcac67123a32406fa8f11fad7978808e202`.

## Applied layout choices

Use the numeric example, with `preprint,review,12pt`, and the example's optional
line numbering. Review spacing and line numbers are readability choices supported
by the official template, not verified journal-specific requirements. No margins,
fonts or class internals are overridden. Frontmatter, keywords, section/equation
numbers, editable tables, figures and numeric bibliography use elsarticle.
The supported `nopreprintline` option suppresses the template's automatic
"Preprint submitted to" footer because this draft has not actually been submitted.
Floats use `htbp` so the review line spacing does not defer all tables to the end.
The class is generated with its supplied installer and copied unchanged beside
the manuscript, together with the numeric bibliography style.

The publisher instructs that source submissions for Editorial Manager must be
flat (no subfolders). A local export script therefore copies only the required
manuscript, bibliography, class, style and figures into a flat review-source ZIP.
That archive is a draft artifact, not authorization to submit it.

## Unresolved journal-specific requirements

https://www.sciencedirect.com/journal/vehicular-communications/publish/guide-for-authors
and the legacy Elsevier journal-guide URL could not be read (HTTP 403). The local
browser connection also failed. Current limits, anonymity policy, mandatory
highlights/graphical abstract, and final declaration requirements remain unverified.
The existing author-review banner and pending author/declaration information stay
visible. We do not fabricate these fields or assert full submission compliance.

The source templates contain publisher example content; none of that content is
used as scientific text or author information in Paper A. Journal-produced final
two-column appearance is not asserted to be its initial-submission requirement.

## Author and funding metadata recheck — 2026-09-22

The current ScienceDirect guide, its ISSN-based route, and the legacy Elsevier
guide still returned HTTP 403; the browser attempt timed out. Current complete
journal-specific compliance therefore remains unverified.

An Elsevier-authored journal information pack hosted by Wuhan University was
opened: https://apps.lib.whu.edu.cn/ensci/editnew/upfile/730290.pdf . The document
itself is dated **17 September 2018**, despite recent search-index timestamps.
Its printed page 7 requires author names, affiliations and corresponding-author
contact details; page 8 specifies funding sources and grant identifiers; page 5
requests sponsor-role information. Page 6 describes single-blind review. These
are historical journal requirements, not a certification of the 2026 policy.
They support retaining the supplied names in the existing identified draft and
the separate Funding section rather than deleting either.

Current publisher submission guidance was also opened:
https://www.elsevier.support/publishing/answer/author-guide-to-editorial-managers-new-submission-experience
(page updated 28 August 2026). It includes author and funder-entry steps, but
explicitly limits applicability to journals using the new workflow. No claim is
made that Vehicular Communications has adopted that particular interface.

The user directly supplied the four authors, shared affiliation, corresponding
author/email and funding wording on 2026-09-22. The manuscript matches those
fields, with the corresponding author's name now also explicit in the footnote.
The funding text and grant identifiers are unchanged. Sponsor involvement was
not supplied and no non-involvement statement has been invented. All-author
scientific/submission approval and unrelated declarations remain pending.

## Publisher AI artwork policy recheck — 2026-09-22/23

The current official policy was opened successfully:
https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals .
It permits AI-assisted explanatory diagrams subject to human oversight and
disclosure in each caption and the general AI statement. Data visualizations
must derive faithfully from underlying data through reproducible methods, with
tool/developer/version disclosure in Methods. General-purpose AI image tools
are not permitted for graphical abstracts. The manuscript's three conceptual
figures are explanatory figures, not graphical abstracts. Methods now describe
the data-derived plotting workflow. Unavailable model versions are identified
as unavailable, not invented. Human final approval remains outstanding; this
publisher-level check does not certify journal-specific submission compliance.

2026-09-23 authoring update: at the user's request, figure-caption disclosures
and the general AI statement were moved out of the reading draft into
`submission_disclosure_notes.md`. The user intends to complete them at submission.
The draft therefore does not yet satisfy those disclosure requirements; the
exported package reminder preserves this pending step. Methods still identify
AI-assisted analysis/plotting code. No claim of AI-free production is made.
