# References and source guide

The sources below explain established methods and numerical conventions. They
are not evidence for this project's experimental performance or a claim that
its public estimator reproduces a commercial instrument. Links and relevant
content were checked on 23 October 2026. No third-party figure is reproduced.

<a id="srs"></a>
## 1. Phase-sensitive detection and RMS conventions

**Stanford Research Systems.** *About Lock-In Amplifiers*, Application Note #3.
[Official PDF](https://www.thinksrs.com/downloads/pdfs/applicationnotes/AboutLIAs.pdf).

The sections on phase-sensitive detection, dual-phase detection and “RMS or
Peak?” explain reference mixing, quadrature outputs and the instrument's RMS
convention. The PDF's first three pages were used for those points. This
repository returns sinusoidal **peak** amplitude, so its numerical amplitude
should not be compared directly to an RMS display without conversion.

<a id="zurich"></a>
## 2. Digital lock-in signal processing

**Zurich Instruments.** *UHF User Manual: Signal Processing Basics*, section
“Principles of Lock-in Detection.”
[Official manual](https://docs.zhinst.com/uhf_user_manual/signal_processing_basics.html#principles-of-lock-in-detection).

The equations describe complex reference multiplication, sum/difference
frequencies, low-pass filtering, I/Q outputs and RMS magnitude. This supports
the conceptual introduction. The offline polynomial regression here has a
different finite-record response from an instrument's recursive filters.

<a id="least-squares"></a>
## 3. Least-squares estimation

**NIST/SEMATECH.** *e-Handbook of Statistical Methods*, §4.4.3.1, “Least Squares.”
[NIST handbook](https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd431.htm).

This source defines the residual sum-of-squares objective and discusses
dependence among fitted parameters and residual error. The appendix derives
the particular block-projection, covariance and normalization formulas used
here from the stated linear model. It does not attribute those package-specific
derivations to an instrument manual.

<a id="numpy"></a>
## 4. Numerical primitives and exact conventions

**NumPy developers.** *NumPy 2.4 reference manual.*

- [Singular value decomposition](https://numpy.org/doc/2.4/reference/generated/numpy.linalg.svd.html): factorization, returned matrix orientation and singular values.
- [Normalized sinc](https://numpy.org/doc/2.4/reference/generated/numpy.sinc.html): `sin(πx)/(πx)`, with its continuous value at zero.
- [Legendre pseudo-Vandermonde matrix](https://numpy.org/doc/2.4/reference/generated/numpy.polynomial.legendre.legvander.html): columns for polynomial degrees 0 through d.

These versioned pages match the major/minor version used in the pinned validation
environment. The repository's SVD, exposure and polynomial conventions are
explicit so that a different implementation can reproduce them.

<a id="rician"></a>
## 5. Magnitude bias from Gaussian quadratures

**Gudbjartsson, H., and Patz, S. (1995).** The Rician distribution of noisy MRI
data. *Magnetic Resonance in Medicine*, **34**(6), 910–914.
[DOI](https://doi.org/10.1002/mrm.1910340618) ·
[PubMed record and abstract](https://pubmed.ncbi.nlm.nih.gov/8598820/) ·
[PMC full-text link](https://pmc.ncbi.nlm.nih.gov/articles/PMC2254141/).

The bibliographic record and abstract were verified; direct full-text retrieval
was intermittently blocked. This article is cited only for the established
connection between Gaussian quadratures and biased magnitude images. The
appendix independently derives the isotropic Rice/Rayleigh formulas and states
why they are not exact for arbitrary correlated or unequal-variance I/Q errors.
The MRI application is not evidence about fluorescence-camera noise.

## Where the derivations are checked

The appendix's projection identities, square-wave conversion and finite-window
frequency formulas are derived explicitly and checked using independent
numerical constructions in [test_mathematics.py](../tests/test_mathematics.py).
They are standard consequences of the stated model. Their tests and citations
do not establish a novel physical mechanism or an unpublished empirical result.

Software/AI assistance and the figure-preparation skill are acknowledged
separately in [provenance.md](provenance.md); that tooling acknowledgment is not
a scientific-method reference or an external review.
