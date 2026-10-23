# Mathematical model and interpretation

This page specifies the implemented contract. The [foundations](foundations.md)
give a conceptual introduction; the [mathematical appendix](appendix-mathematics.md)
derives the formulas, and the [source guide](references.md) identifies supporting
references. Plot-specific transformations are defined in the
[figure legends](figure-legends.md).

## Timing and signal

For one pixel, the supplied timestamps are uniformly spaced frame **centers** in
seconds. The reference frequency `f` is fixed by the caller. Set `t0` to the first
frame center and scale the full time span to `u ∈ [-1, 1]`.

$$
y_k = \sum_{j=0}^{d}\beta_j P_j(u_k)
    + h(f,\tau)\,[I\cos(2\pi f(t_k-t_0))+Q\sin(2\pi f(t_k-t_0))]
    + \epsilon_k,
$$

where `P_j` is a Legendre polynomial, `d` is the supplied drift degree, `τ` is
exposure duration, and

$$h(f,\tau)=\frac{\sin(\pi f\tau)}{\pi f\tau}=\operatorname{sinc}(f\tau).$$

The transfer follows by integrating a sinusoid over a rectangular exposure
centered on `t_k`. Its value is one at zero exposure. Polynomial coefficients
describe the *observed*, exposure-averaged slow baseline; they are not a separate
instantaneous photophysical model.

All columns are fitted jointly with a rank-checked SVD. Fitting and subtracting a
polynomial first can remove some signal when drift and harmonic columns are not
orthogonal. One decomposition is shared across pixels, but pixel coefficients
are independent. No pooled fluorescence waveform supplies the phase.

## Output definitions

$$A=\sqrt{I^2+Q^2},\qquad \phi=\operatorname{atan2}(Q,I),\qquad
B=\frac1N\sum_k\sum_{j=0}^d\beta_jP_j(u_k).$$

$$M\ (\%)=100\,A/B\quad\text{for }B>0.$$

- `A` is the **pre-exposure sinusoidal peak amplitude**, in input intensity units.
- `φ` follows `A cos(2πf(t−t0)−φ)` and refers to the first supplied timestamp.
  Phase has little meaning when amplitude is near zero.
- `B` is the temporal mean of the fitted slow baseline, including any camera or
  spatial background present in the input. No dark-current correction is inferred.
- `M` is normalized harmonic amplitude. It is not peak-to-peak amplitude or
  `(OFF−ON)/OFF` contrast. A square-wave fundamental also differs from its plateau
  contrast. Inferring physical stimulus states would require additional evidence.

The residual standard deviation uses `N − rank(X)` degrees of freedom. The
reported I/Q covariance is the residual variance multiplied by the corresponding
block of `X⁺(X⁺)ᵀ`. This covariance is conditional on a correct linear mean model,
fixed timing/frequency and independent equal-variance temporal errors. Correlated
camera noise, drift misspecification and adaptive frequency selection can violate
that interpretation. It is not a detection threshold, p-value or false-discovery
guarantee. Even pure noise has a positive estimated magnitude `A`.

## Quality contracts

| Condition | Behavior |
|---|---|
| Irregular, repeated, missing or decreasing timestamps | Reject the run; no interpolation |
| Frequency at or above the sampling Nyquist limit | Reject the run |
| Exposure longer than the frame interval | Reject overlapping-exposure acquisition |
| Small exposure transfer, deficient rank or condition number above the numerical guard | Reject unstable fit |
| Nonfinite sample in a pixel | Flag the pixel; exclude its whole trace |
| Any sample at or above an explicitly supplied saturation level | Flag the pixel; exclude its whole trace |
| Nonpositive fitted mean baseline | Keep fitted coefficients; set normalized amplitude to NaN and flag invalid |
| Object, complex, boolean, noncontiguous or color array | Reject; require an explicit conversion upstream |

Flags are bitwise: `1=nonfinite`, `2=saturated`, `4=nonpositive baseline`.
Counts can overlap. All input pixel positions remain in the output maps.

## Limits of the public estimator

One polynomial and one I/Q pair describe the whole recording. Time-varying phase,
moving objects, nonlinear drift, multi-frequency cross-talk and long gaps require
additional modeling. This version does not perform registration, segmentation,
particle classification, frequency calibration, or biological inference. Dense
frequency plotting does not increase independent frequency resolution.

The numerical verification uses analytic injected signals, an independent
numerical exposure integral, repeated white-noise draws, and chunked/read-only
array comparisons. These checks establish behavior on their stated inputs; they
do not validate an instrument or unpublished experimental finding.
