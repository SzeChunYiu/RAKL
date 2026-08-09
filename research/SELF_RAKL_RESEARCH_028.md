# SELF-RAKL Research 028 — Hosted Runner OS-Family Identity

Date: 2026-08-09  
Frozen benchmark: `research/SELF_RAKL_RESEARCH_028_FROZEN_BENCHMARK.json`

## Selected closure residual

Round 027B bound the *repository revision actually executed by CI*, but its logs exposed another independent evaluator coordinate: both protected workflows requested `ubuntu-latest`, while GitHub resolved that alias to a particular Ubuntu 24.04 image build. The source-level workflow therefore did not bind even the OS family over time.

This round separates:

```text
workflow runner label
!= OS family
!= hosted image build
!= runner service/version
!= action runtime selected by the platform
!= Python/package environment
```

The narrow change is to replace `ubuntu-latest` with `ubuntu-24.04` in the two protected workflows. This reduces one mutable coordinate but does not pretend to freeze the exact hosted image build.

## Six-role panel

1. **CI/reproducibility engineer** — scoped the smallest source-level change and preserved all subject-binding/test commands.
2. **Software supply-chain security reviewer** — treated the runner as part of the evaluator trust root rather than as invisible infrastructure.
3. **Formal-methods/state expert** — separated requested label, observed OS family, observed image build, and runtime/platform influence.
4. **SRE/platform specialist** — reviewed GitHub-hosted runner lifecycle and the difference between an OS-version label and an immutable VM image.
5. **Benchmark/research-method lead** — froze known-answer worlds and meta-QoIs before the protected workflow edits.
6. **Adversarial reviewer** — prohibited the overclaim that `ubuntu-24.04` pins `Image Version 20260720.247.2`; also retained the Node runtime override observed in current logs as an open influence.

The panel agreed that pinning the OS family is a real but partial closure. A fully immutable hosted-runner build is not obtained from the ordinary `runs-on` label.

## External framework projection

Current GitHub documentation lists both `ubuntu-latest` and `ubuntu-24.04` as standard hosted-runner labels. The official `actions/runner-images` project states that `-latest` follows the newest stable OS image and can migrate across OS versions, and recommends specifying a concrete OS version to avoid that migration. The same project also documents ongoing image updates, so a concrete OS label must not be treated as a build digest.

The observed Round-027/027B job logs reported:

```text
Image: ubuntu-24.04
Image Version: 20260720.247.2
OS: Ubuntu 24.04.4 LTS
runner: 2.336.0
```

They also warned that pinned actions targeting Node 20 were being forced to run on Node 24. That is direct evidence that source/action pinning does not close platform runtime influence.

## Capability-shaping attribution

- **Model strength amplified:** detecting hidden dependency coordinates from execution traces.
- **Weakness constrained:** treating a successful CI result as environment-independent evidence.
- **Smallest compensator:** explicit OS-family label plus per-run observation of the actual image/build in logs.
- **Verification oracle:** exact-subject GitHub Actions job logs and unchanged parent-evaluator firewall.
- **External-resource gain:** GitHub supplies the hosted image and its run metadata; this is not intrinsic model capability.

## Expected disposition

If exact candidate testing succeeds on `ubuntu-24.04` and the only protected edits are the two frozen runner-label substitutions, classify `META_N090_EVALUATOR_RUNNER_IMAGE_IDENTITY` as **PARTIALLY_IDENTIFIED**:

- OS family: bound to Ubuntu 24.04;
- actual hosted image build: observed for each execution, not source-pinned;
- platform-selected action runtime: open;
- Python/package/toolchain environment: open under N084/N020A.

This is not semantic saturation. It reduces a real evaluator-trust coordinate while leaving the exact external boundary explicit.
