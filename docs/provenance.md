# Provenance and acknowledgments

**Author and project direction:** Minhao Liu.

**Public companion:** version 0.1.0, prepared 23 October 2026. The implementation
refactors standard exposure-aware harmonic regression ideas used in the broader
research workflow into a smaller standalone example. Packaging, CLI, tests,
synthetic scene and gallery were prepared specifically for this public edition.
It is not a byte-identical export of the experimental pipeline. Detailed local
source-to-release notes are retained outside the public repository.

**Data:** all displayed pixels, traces and metrics originate from
`src/lockin_imaging/synthetic.py` with the stated seed. The workflow is a
programmatically drawn schematic. No experimental image or unpublished numerical
result was supplied to an image-generation service or embedded in the gallery.

**AI assistance:** AI assisted code refactoring, test and documentation drafting,
figure scripting and release checks under author direction. The project author
retains responsibility for interpretation, review and publication decisions.
Automated verification is reported within its tested scope.

**Software:** NumPy provides array operations and SVD; Matplotlib renders the
figures; pytest and Ruff provide test/lint tooling. Dependencies are recorded in
the validation environment file and run receipts. Their licenses remain those
of their respective authors.

Figure preparation used the `scientific-visualization` procedural skill from:

Kassis, T., Agarwal, V., He, Y., Patel, D., and Brueckner, A. M. (2026).
*Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents.*
[arXiv:2609.00065](https://doi.org/10.48550/arXiv.2609.00065).
This acknowledgment describes tooling; it is not independent review of this work.
