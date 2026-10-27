# Model-assisted vector figures (2026-10-27)

Figures 1–3 were redrawn with the built-in OpenAI image-generation tool using
respectively the supplied `system_architecture.png`, `decision_counterexample.png`
and `protocol_sequence.png` as edit references. The outputs are preserved here
as `*_model.png`; the original supplied PNGs remain unchanged one directory up.

The image model produces raster images, not native vector files. The delivered
SVGs contain traced vector paths plus precisely typeset SVG text and corrected
geometric primitives; the PDFs are exports of those SVGs. Neither format embeds
a raster image. Traced icons retain the generated artwork's shape imperfections;
vectorization cannot recover detail absent from the generated input. Text and
mathematical labels were reset to native Times New Roman text. Figure 2's plots
were reconstructed on one exact common coordinate scale to correct model drift.
The protocol labels reflect the gateway implementation: a verified decision consumes
the nonce, while the report is accepted only when that decision is Valid.

## Prompt set

All three prompts requested scientific-educational manuscript diagrams, one
finished landscape 16:9 diagram at maximum resolution, vector-friendly flat line
art on white, exact scientific content, legible serif typography, simple icons,
solid navy/blue/teal/pale-blue fills and no gradients, textures, shadows or blur.

1. Architecture: redraw the reference while preserving all content and arrows.
   Public task context includes policy P, threshold k=n-f-r, roster, report,
   challenge nonce and expiry. Preserve Evidence issuers, Vehicle / prover and
   Verification gateway; signed U_i, EdDSA/MiMC, private witness, construction of
   F_k, four-valued decision, Groth16 proof, public outputs, gateway checks,
   Valid acceptance and the privacy footer.
2. Counterexample: preserve Ω=[-4,8]∩Z, P=[0,8]∩Z, (n,f,r,k)=(3,1,0,2),
   U1=[-4,4] Honest, U2=[-2,6] Honest, U3=[2,4] Byzantine, and z*=-1.
   Use three numbered panels for signed evidence, threshold support and
   all-source overlap, shared ticks -4,-2,0,2,4,6,8 and shaded P=[0,8].
   F2=[-2,4] has at least two supporting issuers and is Ambiguous; the all-source
   intersection [2,4] falsely accepts if used alone. Preserve all observations.
3. Protocol: preserve four columns (Administrator, Verification gateway,
   Vehicle / prover, Evidence issuers) and the seven numbered steps and arrows:
   configure task; issue nonce/expiry; request evidence; return signed boxes;
   compute decision/proof; submit report; verify and process. Include
   c=H(ver,task,ν,e,H(R)) mod q. Check nonce existence/expiry, reconstruct inputs,
   verify proof and decision, accept only verified Valid, atomically consume the
   accepted nonce. Include failure cases and retry semantics. No text collisions.

## Rebuild

Requires Python with `vtracer==0.6.12` and `rsvg-convert` (tested: librsvg 2.62.1).
From the manuscript directory:

```sh
python vectorize_model_figures.py
latexmk -pdf -interaction=nonstopmode -halt-on-error manuscript.tex
```

`vectorize_model_figures.py` traces the three saved model outputs, applies
`vector_labels.py` to restore exact labels and coordinates, then exports SVG and
PDF. The image-model step is not deterministic; the saved PNGs make the vector
processing reproducible without another model invocation.

Verification: inspect each PDF with `pdfimages -list`; no image entries are
expected. SVGs must have no `<image>` elements or data URIs. Render the exported
PDFs and inspect all formulas, arrow directions, labels and interval endpoints.
