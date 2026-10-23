# Foundations: what a lock-in image measures

A time-averaged fluorescence image answers **where light is bright**. A lock-in
amplitude image answers **where intensity contains a component at a chosen
frequency**. A bright static source can therefore be weak in the second image.
Conversely, a source can show a periodic component without that component proving
a particular physical cause: drift, motion or pickup at the same frequency can
also enter the estimate.

## Why two references?

A response may lag the supplied reference. A cosine alone can miss a response
that lies mostly in the sine direction. Fitting both references gives signed
coefficients I and Q. Their vector length is amplitude; their angle specifies
phase. There is no per-pixel search for a favorable phase: the two coefficients
are fitted together. [The quadrature diagram](figure-legends.md#figure-1-from-a-recorded-trace-to-a-pixelwise-amplitude-map)
uses the actual fitted coefficients of the example pixel.

Classical lock-in instruments multiply a signal by reference waveforms and
low-pass filter the products. The same phase-sensitive idea motivates this
package, but its implementation fits one complete finite record using linear
regression. Instrument time constants and filter orders are not parameters of
this API. See the [SRS and Zurich primers](references.md) for the hardware view.

## Why fit the baseline at the same time?

Slow fluorescence drift can correlate with sine and cosine over a finite
record. Removing a polynomial from the observations first can remove part of
the target signal. A joint fit estimates the polynomial and harmonic together;
the appendix derives both the correct projection identity and the error of
one-sided detrending. A correct fit still cannot separate nearly indistinguishable
columns reliably. The package reports conditioning and rejects severe numerical
instability.

## What does camera exposure change?

A camera frame averages light over a finite interval. Fast oscillations partly
cancel within that interval. For a fixed rectangular exposure, the harmonic is
attenuated by `sinc(f × exposure)`. The fit incorporates this known response,
so the returned amplitude describes the sinusoid before exposure averaging.
This correction requires correct frame-center timing and does not recover
unknown motion, photon statistics or aliased components.

## Which quantity should be compared?

| Quantity | Definition | Interpretation |
|---|---|---|
| Mean fitted baseline | Mean of the fitted polynomial | Includes any background left in the input |
| Peak harmonic amplitude | `A = hypot(I, Q)` | Pre-exposure sinusoidal peak, in input units |
| Sinusoidal AC RMS | `A / sqrt(2)` | Excludes the DC baseline; many instruments use RMS |
| Sinusoidal peak-to-peak | `2A` | Extrema difference of that harmonic alone |
| Normalized harmonic amplitude | `100A/B` | Percentage relative to the total fitted baseline |
| ON/OFF contrast | `(OFF − ON) / OFF` | Requires defined stimulus states and their levels |

The last two rows cannot be exchanged by renaming an axis. The
[mathematical appendix](appendix-mathematics.md) derives the different
conversions for an ideal sine wave and an ideal rectangular waveform.

## Why is the control map not identically zero?

The fitted I and Q coefficients fluctuate around zero under a zero-modulation
noise model. Their nonnegative vector length does not average to zero. This
positive noise floor is expected and should remain visible in a numerical
summary. An amplitude image alone is not a significance map. The repository
does not choose a detection cutoff or estimate classification performance.

The public control is a second simulation with the same baseline and independent
noise. It demonstrates estimator behavior under its model. It does not replace
physical negative controls, independent acquisitions or biological replicates.

## Reading this repository

Read [the figure legends](figure-legends.md) for every displayed condition and
normalization, [the method](method.md) for the API contract, and
[the appendix](appendix-mathematics.md) for the derivations. The
[reference guide](references.md) separates background sources from the code's
own finite tests. The [release boundary](release-boundary.md) explains what the
public companion includes. The full experimental workflow and unpublished
results remain outside this repository.
