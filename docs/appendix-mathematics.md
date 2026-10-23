# Mathematical appendix

This appendix derives the **public, fixed-frequency estimator** in
[core.py](../src/lockin_imaging/core.py). It documents standard signal-processing
and regression mathematics in the package's own sign, scale and timing
conventions. It does not describe unreleased experiment-specific methods.

For a short introduction, start with [Foundations](foundations.md). The
[reference guide](references.md) identifies primary sources and exactly which
background claims they support. The derivations below follow directly from the
stated model; none is presented as a new theorem or an experimental result.

| Symbol | Meaning |
|---|---|
| $N,\Delta t,\tau$ | Frame count, frame-center interval and rectangular exposure duration |
| $t_k=t_0+k\Delta t$ | Timestamp of frame center, $k=0,\ldots,N-1$ |
| $f,\omega=2\pi f$ | Supplied reference frequency and angular frequency |
| $d,p=d+3$ | Baseline polynomial degree and total number of fitted coefficients |
| $D,H,X=[D\ H]$ | Baseline, harmonic and complete design matrices |
| $\gamma=(I,Q)^T$ | Signed, exposure-corrected harmonic coefficients |
| $A,\phi,B$ | Sinusoidal peak amplitude, phase and mean fitted baseline |

## A. From phase-sensitive detection to a finite-record fit

In the simplest case, a baseline-subtracted signal is
$y_k-B=I\cos\theta_k+Q\sin\theta_k$, where
$\theta_k=\omega(t_k-t_0)$. If the sampled sine and cosine are orthogonal, have
zero means and squared norms $N/2$, multiplying by each reference and averaging
gives

$$
I=\frac{2}{N}\sum_k(y_k-B)\cos\theta_k,\qquad
Q=\frac{2}{N}\sum_k(y_k-B)\sin\theta_k.
$$

These conditions hold for an appropriate integer number of cycles on a uniform
sample grid away from DC and Nyquist. They need not hold for an arbitrary
frequency, incomplete cycles or a polynomial baseline. The package replaces
these simple correlations with a joint least-squares fit. A classical lock-in
uses mixing and low-pass filtering; the corresponding principles and instrument
RMS conventions are described by [SRS](references.md#srs) and
[Zurich Instruments](references.md#zurich). This offline regression does not
implement an instrument's RC time constant or settling dynamics.

With exposure transfer $h$, a complex correlation in the ideal orthogonal case
obeys

$$
Z=\frac{2}{Nh}\sum_k(y_k-B)e^{-i\theta_k}=I-iQ=Ae^{-i\phi}.
$$

Consequently, this package's phase is **minus** the argument of that
negative-exponential correlation. One must not import a complex-demodulator
phase convention without checking its sign and normalization.

## B. Rectangular camera integration

Let the instantaneous harmonic be
$s(t)=A\cos[\omega(t-t_0)-\phi]$. For an exposure centered at $t_k$,

$$
\begin{aligned}
\overline s_k
&=\frac{1}{\tau}\int_{t_k-\tau/2}^{t_k+\tau/2}
 A\cos[\omega(t-t_0)-\phi]\,dt\\
&=A\frac{2\sin(\omega\tau/2)}{\omega\tau}
 \cos[\omega(t_k-t_0)-\phi]\\
&=h(f,\tau)[I\cos\theta_k+Q\sin\theta_k],
\end{aligned}
$$

where $I=A\cos\phi$, $Q=A\sin\phi$ and

$$
h(f,\tau)=\mathrm{sinc}(f\tau)
=\frac{\sin(\pi f\tau)}{\pi f\tau},\qquad h(f,0)=1.
$$

This is the normalized sinc used by
[NumPy](https://numpy.org/doc/2.4/reference/generated/numpy.sinc.html), not
$\sin x/x$ with the same numerical argument. Incorporating $h$ into both design
columns makes the estimated I/Q values pre-exposure amplitudes. Dividing an
already corrected amplitude by $h$ a second time would be an error.

The observed slow baseline is modeled as a polynomial after exposure averaging.
Averaging an instantaneous polynomial over a fixed centered interval keeps it
within the same polynomial degree, although its coefficients can change. The
code therefore does not invert a physical baseline-integration model.

If acquisition timestamps mark exposure **starts**, add $\tau/2$ before calling
the solver. Using the wrong timestamp convention shifts phase relative to an
external clock. A common shift of every supplied timestamp leaves the package's
first-center-relative phase unchanged. Rolling shutters, variable exposure,
unknown frame jitter and nonrectangular integration are outside this model.

The API requires $0<f<1/(2\Delta t)$ and $0\leq\tau\leq\Delta t$ (up to its
numerical exposure comparison tolerance). Thus, in the intended domain,
$0\leq f\tau<1/2$ and $2/\pi<h\leq1$. The default transfer guard 0.1 is
conservative and normally inactive here; a stricter caller-supplied guard can
reject a fit. These constraints do not rule out aliasing of *other* frequencies
in a real input.

## C. Joint polynomial and harmonic regression

Define

$$
u_k=2\frac{t_k-t_0}{t_{N-1}-t_0}-1,\qquad
D_{kj}=P_j(u_k),\quad j=0,\ldots,d,
$$

$$
H_{k,:}=h[\cos\theta_k,\ \sin\theta_k],\qquad
y=D\beta+H\gamma+\epsilon=X\alpha+\epsilon.
$$

Legendre columns span the same polynomial space as ordinary powers, with better
scaling on this bounded interval. Their continuous orthogonality does **not**
make the finite sampled columns mutually orthogonal or make them orthogonal to
$H$. [NumPy's basis documentation](references.md#numpy) defines the matrix used.

For $N>p$ and full column rank, minimize $\|y-X\alpha\|_2^2$. With thin SVD
$X=U\Sigma V^T$,

$$
\widehat\alpha=V\Sigma^{-1}U^Ty=X^+y.
$$

The implementation uses this factorization once for all pixels. It does not
form or invert $X^TX$, whose 2-norm condition number would be
$\kappa_2(X)^2$. It rejects a smallest singular value below
$\epsilon_{\rm mach}\max(N,p)s_{\max}$ or $\kappa_2(X)>10^8$.
These are numerical guards, not a guarantee of scientific identifiability or
small uncertainty. The objectives and factorization are documented by
[NIST and NumPy](references.md#least-squares).

For numerical stability, the solver subtracts the first intensity in each trace
before projection. Since $D$ contains the constant column, subtracting any
constant $c$ changes only the fitted intercept. Adding $c$ back to the fitted
baseline exactly restores the original model in exact arithmetic. I/Q and
residuals are unchanged.

## D. Why detrending only the observations can bias the harmonic

Let $P_D=D(D^TD)^{-1}D^T$ and $M_D=I_N-P_D$. These expressions are for analysis;
a stable implementation can apply the projection using QR without forming an
$N\times N$ matrix. For fixed $\gamma$, minimizing over $\beta$ leaves

$$
\min_\gamma\|M_Dy-M_DH\gamma\|_2^2.
$$

Since $M_D=M_D^T=M_D^2$, the joint estimator is

$$
\widehat\gamma=(H^TM_DH)^{-1}H^TM_Dy.
$$

This is the partial-regression identity: remove the baseline subspace from
**both** the observations and harmonic columns. By contrast, detrending $y$
and then fitting the *original* $H$ gives

$$
\widetilde\gamma=(H^TH)^{-1}H^TM_Dy.
$$

For noiseless $y=D\beta+H\gamma$,

$$
\widetilde\gamma-\gamma
=-(H^TH)^{-1}H^TP_DH\gamma.
$$

The error vanishes when $D^TH=0$, but generally not otherwise. Individual
coefficients and phase can change; it is not universally a scalar amplitude
attenuation. Near DC, sinusoidal columns can also be approximated by low-degree
polynomials, causing genuinely poor separation even for a correct joint solve.
[The regression test](../tests/test_mathematics.py) checks the identity and
demonstrates the failure of one-sided detrending on a finite synthetic record.

## E. Output scale, phase and normalization

The model identity

$$
I\cos\theta+Q\sin\theta=A\cos(\theta-\phi)
$$

gives $A=\sqrt{I^2+Q^2}$ and $\phi=\mathrm{atan2}(Q,I)$.
For a pure sinusoid, AC RMS amplitude is $A/\sqrt2$ and peak-to-peak amplitude
is $2A$. The AC RMS excludes the DC baseline. At zero amplitude, phase is
mathematically undefined; a returned floating-point angle is not evidence of
a meaningful phase.

The baseline output and normalized amplitude are

$$
\widehat B=\frac1N\mathbf1^TD\widehat\beta,\qquad
M=100\,\frac{\widehat A}{\widehat B}\quad(\widehat B>0).
$$

$\widehat B$ need not equal the raw sample mean: the fitted harmonic can have a
nonzero sample mean over incomplete cycles. If intensity contains unremoved
background $B_{\rm bg}$ plus responsive fluorescence $B_{\rm resp}$, normalization
uses the total fitted baseline. For a component with intrinsic modulation
fraction $m_{\rm resp}$, the idealized measured fraction is
$m_{\rm resp}B_{\rm resp}/(B_{\rm resp}+B_{\rm bg})$ when those are the only
baseline terms. Static fluorescent objects can dilute it further. No intrinsic
particle contrast can be inferred without the missing background information.

The plotted trace in Figure 2e is instead
$100[1+(y_k-\widehat b_k)/\widehat B]$. Its fitted oscillation has relative peak
$100h\widehat A/\widehat B$. This display deliberately retains the exposure
response of the observed trace.

## F. Conditional covariance and the positive noise floor

Assume the linear mean model is correct, the design is fixed, and temporal errors
have zero mean and covariance $\sigma^2I_N$. Then

$$
\mathrm{Cov}(\widehat\alpha)
=\sigma^2X^+(X^+)^T,\qquad
\widehat\sigma^2=\frac{\|y-X\widehat\alpha\|_2^2}{N-p}.
$$

The returned $2\times2$ I/Q covariance is the last block with
$\sigma^2$ replaced by $\widehat\sigma^2$. Equivalently it is
$\widehat\sigma^2(H^TM_DH)^{-1}$. Gaussian errors are not required for this
second-moment calculation, but distributional claims below do require them.
For general temporal covariance $\Omega$, the correct expression would be
$X^+\Omega(X^+)^T$. Estimation of $\Omega$, generalized least squares, and
correlated-noise uncertainty are **not implemented** here.

Writing $C=\mathrm{Cov}(\widehat\gamma)$ and the true
$\gamma=(I,Q)^T$, the exact second-moment identity is

$$
\mathbb E[\widehat A^2]=A^2+\mathrm{tr}(C).
$$

In the special isotropic Gaussian case $C=s^2I_2$, the joint density of two
quadratures can be changed to polar coordinates, with Jacobian $r$. Integrating
over angle yields the Rice density

$$
p(r\mid A)=\frac{r}{s^2}
 \exp\!\left[-\frac{r^2+A^2}{2s^2}\right]
 I_0\!\left(\frac{rA}{s^2}\right),\qquad r\geq0,
$$

where $I_0(z)=(2\pi)^{-1}\int_0^{2\pi}e^{z\cos\vartheta}\,d\vartheta$.
At $A=0$, this becomes Rayleigh:

$$
p(r)=\frac{r}{s^2}e^{-r^2/(2s^2)},\quad
\mathbb E[r]=s\sqrt{\pi/2},\quad
r_{\rm median}=s\sqrt{2\log2}.
$$

This familiar magnitude bias is also discussed for MRI quadratures by
[Gudbjartsson and Patz](references.md#rician). The shared mathematical form does
not validate this package for MRI or make actual camera noise Gaussian.
Unequal/correlated I/Q errors do not obey this simple Rice law. The gallery's
polynomial projection makes its covariance generally non-isotropic, so the
formula is explanatory, not an exact fitted null distribution for its map.

Away from zero amplitude, first-order propagation gives

$$
g_A=\frac{1}{A}(I,Q)^T,\qquad
g_\phi=\frac{1}{A^2}(-Q,I)^T,
$$

$$
\mathrm{Var}(\widehat A)\approx g_A^TCg_A,\qquad
\mathrm{Var}(\widehat\phi)\approx g_\phi^TCg_\phi.
$$

These approximations fail near the origin. An uncertainty calculation for
$M=100A/B$ additionally needs the covariance of $(I,Q,B)$ and gradient
$(100I/(AB),100Q/(AB),-100A/B^2)$. The API does not export that full covariance or
a normalized-amplitude confidence interval. It also does not subtract the
magnitude bias, select a detection threshold, or correct a spatial/frequency
multiple-comparison problem.

## G. A harmonic amplitude is not an ON/OFF contrast

Consider an ideal rectangular waveform with high level $F_H$, low level
$F_L=F_H-\Delta$, and low-state duty fraction $D\in(0,1)$. Its mean is
$B=F_H-D\Delta$. Choose the low state on $0\leq t<DT$ in a period $T$. The first
complex Fourier coefficient is

$$
c_1=-\frac{\Delta}{T}\int_0^{DT}e^{-i2\pi t/T}\,dt
=-\frac{\Delta}{\pi}e^{-i\pi D}\sin(\pi D).
$$

Its sinusoidal peak amplitude is therefore
$A_1=2|c_1|=2\Delta\sin(\pi D)/\pi$.
Defining plateau contrast $c=\Delta/F_H$ and the *fraction*
$m=A_1/B=M/100$ gives

$$
m=\frac{2c\sin(\pi D)}{\pi(1-Dc)},\qquad
c=\frac{\pi m}{2\sin(\pi D)+\pi Dm}.
$$

For $D=1/2$, $A_1=2\Delta/\pi$ and $c=2\pi m/(4+\pi m)$.
For an ideal **sinusoid** with high/low extrema $B\pm A$, the different relation
is $c=2m/(1+m)$. Thus even these two noiseless waveforms have different
amplitude-to-contrast conversions.

These identities require known waveform, duty fraction, state levels,
background convention and an uncontaminated fundamental. Other harmonics can
alias or leak into a finite-record fit. A single recovered I/Q pair cannot
establish those conditions. The repository deliberately reports normalized
harmonic amplitude, not an inferred experimental ON/OFF contrast.

<a id="frequency-response"></a>
## H. Finite records, frequency mismatch and diagnostic scans

For uniform samples, the exact complex finite-window response is the geometric sum

$$
W_N(\delta f)=\frac1N\sum_{k=0}^{N-1}e^{i2\pi\delta f k\Delta t}
=e^{i\pi\delta f(N-1)\Delta t}
 \frac{\sin(\pi N\delta f\Delta t)}
 {N\sin(\pi\delta f\Delta t)},
$$

with removable singularities evaluated by their limits. The nearest nonzero
zeros of its isolated central lobe are at $\delta f=\pm1/(N\Delta t)$.
For the synthetic record this scale is 0.0625 Hz. It is a finite-window
correlation scale, not a universal lower bound on parametric frequency
estimation accuracy.

For a real sinusoid at $f_0$, a simple complex correlation against $f$ contains
both positive- and negative-frequency contributions:

$$
Z(f)=\frac{Ah(f_0,\tau)}{h(f,\tau)}
 \left[e^{-i\phi}W_N(f_0-f)+e^{i\phi}W_N(-f_0-f)\right].
$$

This expression assumes the true baseline has already been removed. It is not
the exact Figure 2f estimator: that estimator also refits polynomial terms and
accounts for nonorthogonal harmonic columns at each frequency. If $H_f$ denotes
the harmonic design at $f$, its exact mean response under the stated linear
model is

$$
\mathbb E[\widehat\gamma(f)]
=(H_f^TM_DH_f)^{-1}H_f^TM_DH_{f_0}\gamma_0.
$$

The scan's fine grid samples this response more densely; it does not create
additional observation time. Choosing the largest scanned amplitude would
introduce frequency selection and change uncertainty interpretation. The image
maps use the caller's fixed frequency, and no such selection is made.

## I. Work, storage and excluded pixels

For $P$ pixels, $p=d+3$ design columns and a chunk of $C$ pixels, the thin SVD
costs $O(Np^2)$ and projecting/reconstructing all traces costs $O(NpP)$.
Working storage is $O(Np+NC+P)$ at fixed small $p$, excluding the original input
and constant-factor chunk temporaries. All output maps remain in memory; the
implementation is not a fully streaming acquisition system.

The memory guarantee applies to an existing C-contiguous NumPy array or memory
map. Passing a nested Python sequence can allocate an input array during
conversion. Missing/nonfinite or explicitly saturated samples exclude the
whole pixel trace, rather than changing the design separately per frame.
Nonpositive fitted baselines retain I/Q but invalidate normalization. Flags
describe these numerical/data contracts, not object identity or significance.

## J. Executable checks and scope

| Derivation or failure mode | Executable check |
|---|---|
| Signed I/Q, phase, polynomial baseline, exposure | Parameterized analytic recovery in [test_core.py](../tests/test_core.py) |
| Exposure sinc from an integral | Independent dense numerical integration in test_core.py |
| Joint regression and partial regression | QR residualization of both response and references in [test_mathematics.py](../tests/test_mathematics.py) |
| One-sided detrending failure | Noiseless nonorthogonal counterexample in test_mathematics.py |
| Magnitude second moment and Rayleigh special case | Seeded independent white-noise realizations in test_mathematics.py |
| Rectangular-wave conversion | Numerical integration of the low-state interval at several duty fractions |
| Frequency response | Geometric-sum and exact off-frequency regression checks |
| Figure/model correspondence | Example-pixel coefficients, trace normalization, map scales and scan reference in [test_figures.py](../tests/test_figures.py) |

Tests check the stated identities and finite cases. They do not establish
universal robustness, instrument sensitivity, biological replication, or the
validity of an unpublished research conclusion.
