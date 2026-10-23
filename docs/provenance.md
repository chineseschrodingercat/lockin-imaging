# Provenance and acknowledgments

**Author and project direction:** Minhao Liu.

**Public companion:** version 0.2.0, prepared 23 October 2026. The implementation
refactors standard exposure-aware harmonic regression ideas used in the broader
research workflow into a smaller standalone example. Packaging, CLI, tests,
synthetic scene and gallery were prepared specifically for this public edition.
It is not a byte-identical export of the experimental pipeline. Detailed local
source-to-release notes are retained outside the public repository.

**Data:** all displayed pixels, traces and metrics originate from
`src/lockin_imaging/synthetic.py` with the stated seed. In version 0.2.0, the
workflow's trace, fit, I/Q vector and amplitude map all use that same recording;
the former separately drawn schematic has been replaced. All figures are
rendered programmatically. No experimental image or unpublished numerical
result was supplied to an image-generation service or embedded in the gallery.

**AI assistance:** AI assisted code refactoring, test and documentation drafting,
figure scripting and release checks under author direction. The project author
retains responsibility for interpretation, review and publication decisions.
Automated verification is reported within its tested scope.

The 0.2.0 review moved explanatory notes into full figure legends, checked
figure/model correspondence and added derivations and source references. The
numerical estimator and default synthetic metrics are unchanged. See
[review notes](review-notes.md) for the corrections and their checks.

**Software:** NumPy provides array operations and SVD; Matplotlib renders the
figures; pytest and Ruff provide test/lint tooling. Dependencies are recorded in
the validation environment file and run receipts. Their licenses remain those
of their respective authors.

Figure preparation used the `scientific-visualization` procedural skill from:

Kassis, T., Agarwal, V., He, Y., Patel, D., and Brueckner, A. M. (2026).
*Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents.*
[arXiv:2609.00065](https://doi.org/10.48550/arXiv.2609.00065).
This acknowledgment describes tooling; it is not independent review of this work.
