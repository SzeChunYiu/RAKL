# NS-R001b strain/vorticity geometry atlas — A2/A3

Authority: `EXACT_ALGEBRAIC_CALIBRATION / ROUTE_FAMILY_FALSIFIER / NO_THEOREM_CANDIDATE / ROOT_AUTHORITY_NONE`.

This atlas executes the frozen NS-R001b next action. It deliberately uses **two different calibrations** so that a rejected route cannot hide which assumption it actually needed.

The goal is not to refute established geometric regularity criteria. The goal is narrower: determine whether local strain/vorticity alignment by itself can be the missing bridge from Leray energy control to a global critical bound.

## Common linear core

Let

\[
S_0=\begin{pmatrix}
-\tfrac12&0&0\\
0&-\tfrac12&0\\
0&0&1
\end{pmatrix},
\qquad
J=\begin{pmatrix}
0&-1&0\\
1&0&0\\
0&0&0
\end{pmatrix},
\qquad
A(b)=S_0+bJ .
\]

For the linear velocity field \(u(x)=A(b)x\),

\[
\nabla\cdot u=\operatorname{tr}A(b)=0,
\qquad
S=\tfrac12(A+A^T)=S_0,
\qquad
\omega=\nabla\times u=2b\,e_3.
\]

Hence

\[
S\omega=\omega,\qquad
\omega\cdot S\omega=4b^2>0\quad(b\neq0).
\]

Thus the vorticity is exactly aligned with the unique positive eigendirection of the strain. The normalized squared alignment efficiency is

\[
\frac{(\omega\cdot S\omega)^2}
{\lVert S\rVert_F^2\,\lVert\omega\rVert^4}
=\frac{2}{3},
\]

and the angle between \(\omega\) and \(S\omega\) is zero.

This is **positive stretching**, not geometric depletion.

---

## A2 — finite-energy smooth divergence-free field with a positively aligned core

Set \(b=1\), \(u_0(x)=A(1)x\). Because \(u_0\) is homogeneous of degree one and divergence free,

\[
B_0(x)=-\frac13\,x\times u_0(x)
\]

satisfies \(\nabla\times B_0=u_0\). Explicitly, writing \(x=(x,y,z)\),

\[
B_0=
\left(
\frac13xz-\frac12yz,\;
\frac12xz+\frac13yz,\;
-\frac13(x^2+y^2)
\right).
\]

Choose a standard \(\chi\in C_c^\infty(\mathbb R^3)\) with
\(\chi=1\) on \(B_1\) and support in \(B_2\), and define

\[
\phi=\nabla\times(\chi B_0).
\]

Then:

- \(\phi\in C_c^\infty(\mathbb R^3;\mathbb R^3)\);
- \(\nabla\cdot\phi=0\) identically;
- \(\phi=u_0\) on \(B_1\);
- on \(B_1\), \(S_\phi=S_0\), \(\omega_\phi=2e_3\), and
  \(\omega_\phi\cdot S_\phi\omega_\phi=4\).

Therefore a smooth compactly supported finite-energy divergence-free field can have a whole open core with exactly constant vorticity direction, perfect positive-eigenframe alignment, and strictly positive vortex stretching.

### Concentration version

Let \(\psi\in C_c^\infty(\mathbb R)\) equal one on a nonempty time interval and define the parent-A1 concentration family

\[
U_\lambda(x,t)=\lambda^{3/2}\phi(\lambda x)\psi(\lambda^2t).
\]

The Leray pair
\(L_t^\infty L_x^2\cap L_t^2\dot H_x^1\)
remains fixed. On the natural core where \(\chi=1\) and \(\psi=1\),

\[
S_{U_\lambda},\,\omega_{U_\lambda}\sim\lambda^{5/2},
\qquad
\omega_{U_\lambda}\cdot S_{U_\lambda}\omega_{U_\lambda}
\sim\lambda^{15/2},
\]

while the normalized alignment efficiency remains exactly \(2/3\).

**A2 result.** Adding local positive-eigenframe strain/vorticity geometry does not repair the A1 criticality gap on arbitrary smooth finite-energy divergence-free histories.

**Boundary.** \(U_\lambda\) is not asserted to solve Navier–Stokes. A theorem using exact trajectory structure may evade A2.

---

## A3 — exact smooth Navier–Stokes linear flow with the same alignment, but infinite energy

Now let \(b(t)=b_0e^t\) and

\[
u(x,t)=A(b(t))x .
\]

Because \(b'=b\),

\[
A'(t)+A(t)^2
=
\operatorname{diag}
\left(\tfrac14-b(t)^2,\,
      \tfrac14-b(t)^2,\,
      1\right),
\]

which is symmetric. Define

\[
p(x,t)=
-\frac12\,x^\mathsf T\big(A'(t)+A(t)^2\big)x .
\]

Since \(\Delta u=0\),

\[
\partial_t u+(u\cdot\nabla)u+\nabla p-\nu\Delta u=0,
\qquad
\nabla\cdot u=0
\]

for every viscosity \(\nu>0\). Thus A3 is an exact smooth Navier–Stokes solution on \(\mathbb R^3\).

Its vorticity is

\[
\omega(x,t)=2b_0e^t e_3,
\]

so

\[
S_0\omega=\omega,\qquad
\omega\cdot S_0\omega=4b_0^2e^{2t},
\qquad
\partial_t\omega=S_0\omega.
\]

The perfect positive-eigenframe alignment is therefore dynamically compatible with the exact equation and produces exponential vorticity growth without a finite-time singularity.

However \(u(x,t)\) grows linearly in \(|x|\), so
\(\int_{\mathbb R^3}|u|^2dx=\infty\). A3 is outside the Clay finite-energy / decaying data class.

**A3 result.** Exact Navier–Stokes dynamics plus local positive alignment are still not enough to isolate the Millennium mechanism unless global finite-energy/spatial localization is used.

**Boundary.** A3 is not a counterexample to any finite-energy regularity statement.

---

## Two-calibration conclusion

The calibrations remove two different shortcuts:

| route basis | A2 | A3 | status |
|---|---:|---:|---|
| energy + incompressibility + local alignment | finite energy, yes; exact trajectory, no | — | rejected |
| exact Navier–Stokes + local alignment, without global localization | — | exact trajectory, yes; finite energy, no | rejected |
| exact Navier–Stokes **and** finite-energy/global localization | not tested | not tested | live |

So the surviving NS-R001b obstruction is sharper:

> Find a scale-critical spacetime quantity or inequality that uses the **joint intersection** of exact Navier–Stokes evolution and global finite-energy/localization to prevent persistent concentration/stretching. Static local alignment alone is not the missing coordinate.

The 2024 strain-vorticity interaction analysis makes an **advection-mediated depletion coordinate** a high-information next context to inspect: it explicitly separates advection from quadratic strain/vorticity interactions and supplies exact identities/conditional criteria. This is a next-context recommendation only, not a theorem candidate.

## What this does not claim

- It does not prove global regularity or finite-time blowup.
- It does not refute Constantin–Fefferman or any other established geometric regularity criterion.
- It does not show that vorticity-direction coherence is useless; A2 tests a local core, not the full nonlocal criterion.
- It does not promote the linear A3 flow into the Clay class.
- It does not establish novelty.

Root state remains `OPEN_NO_SOLUTION_CERTIFICATE`.
