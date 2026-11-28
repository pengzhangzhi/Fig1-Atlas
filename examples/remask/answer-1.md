I ran the Fig1 Atlas workflow on your draft. Below are five templates and my pick; I stop here until you choose.

**What your Figure 1 must argue:** standard MDLM sampling freezes every unmasked token, so early mistakes survive and compound; ReMask lets the same model re-mask and fix them at the same NFE. That is a `prior-vs-ours` figure with a `problem-setup` flavour.

Fetched images are in `fig1_refs/` (next to `draft.md`).

## Templates

**1. Soft-Masked Diffusion Language Models** (ICLR 2026, [arXiv 2510.17206](https://arxiv.org/abs/2510.17206), `fig1_refs/iclr26-1449.png`)
- **Layout:** two token grids side by side, rows are decoding iterations, with a vertical "decoding iterations" arrow. The baseline's final row has one red wrong token; the "this work" grid ends all green.
- **Why it fits:** it makes your argument (the baseline commits an error and keeps it; ours does not) with a different mechanism, so you can borrow the layout without resembling a competitor.
- **Mapping:** (a) "Standard MDLM: unmask → frozen", where a wrong token committed in row 1 is carried unchanged to the last row. (b) "ReMask: unmask → score → re-mask → re-predict", where the same token is flagged, returned to `[M]`, and refilled correctly.

**2. Early Decisions Matter** (ICML 2026, [arXiv 2604.10567](https://arxiv.org/abs/2604.10567), `fig1_refs/icml26-5222.png`)
- **Layout:** two panels with rows t=0..4, pink tokens against green, and small confidence bar charts above the slots.
- **Why it fits:** its claim is that early choices decide the trajectory, which matches your finding that most of the gain comes from the first 20% of steps.
- **Mapping:** the same grids as template 1, with posterior-confidence bars above already-unmasked tokens. The lowest bar is the one that gets re-masked, and a bracket marks "first 20% of steps".

**3. On the Error Correcting Effects of Stochasticity in Discrete Diffusion** (NeurIPS 2026, [arXiv 2605.26582](https://arxiv.org/abs/2605.26582), `fig1_refs/neurips26-1599.png`)
- **Layout:** mechanism cartoon on top, step timelines where the proposed sampler has arcs jumping backward, and quality-vs-NFE plots at the bottom.
- **Why it fits:** it is the only one that shows "correction at no extra network evaluations" together with the headline number.
- **Mapping:** timeline (a) is MDLM with forward-only arcs. Timeline (b) is ReMask with small backward arcs whose size k_t shrinks linearly to 0. Below, generative perplexity vs steps with 42.1 → 27.8 marked at 64, plus a flat entropy inset.

**4. Rex: Reversible Exponential Runge-Kutta Solvers** (ICML 2026 oral, [arXiv 2502.08834](https://arxiv.org/abs/2502.08834), `fig1_refs/icml26-0825.png`)
- **Layout:** two minimal schematic plots on matching axes, with a red "ε" gap badge against a green "ε=0" badge.
- **Why it fits:** it is the cleanest "error accumulates vs. doesn't" picture.
- **Mapping:** x = sampling step, y = number of wrong committed tokens. The frozen curve only rises; the ReMask curve bends back down. It would need a measured error-vs-step curve to be honest, and it hides the mechanism.

**5. Closest prior work, weak templates to copy**
- **PRISM**, "Fine-Tuning Masked Diffusion for Provable Self-Correction" (ICML 2026, [arXiv 2510.01384](https://arxiv.org/abs/2510.01384), `fig1_refs/icml26-0239.png`): vanilla vs. remasking inference stacks with per-token scores.
- **RemeDi**, "Don't Settle Too Early" (ICLR 2026, [arXiv 2509.23653](https://arxiv.org/abs/2509.23653), `fig1_refs/iclr26-1039.png`): one sentence over four denoising steps, a token struck through and replaced, plus a radar chart.
- These draw almost exactly your idea. Reviewers will have them in mind, so your figure should look different and make "training-free, same frozen model, same NFE" visible.

## Recommendation: template 1, with two borrowings

Use the Soft-Masked two-grid layout as the body. Add the confidence bars from template 2 and a thin budget/NFE strip from template 3 along the bottom. The grid shows both the failure and the fix in one glance, and the strip carries the claim that separates you from PRISM and RemeDi.

```
 (a) Standard MDLM: unmask → frozen          (b) ReMask (ours): unmask → score → re-mask
 step                                         step
  0 │ [M]  [M]   [M]   [M]  [M]   [M] [M]      0 │ [M]  [M]   [M]     [M]  [M]   [M] [M]
  1 │ The  chef  flew✗ [M]  [M]   [M] [M]      1 │ The  chef  flew    [M]  [M]   [M] [M]
    │            🔒 frozen                        │           ▁ low posterior conf.
  2 │ The  chef  flew✗ the  pasta [M] [M]      2 │ The  chef  [M]↺    the  pasta [M] [M]
  3 │ The  chef  flew✗ the  pasta in  [M]      3 │ The  chef  cooked  the  pasta in  [M]
  T ▼ The  chef  flew✗ the  pasta in  a pot    T ▼ The  chef  cooked✓ the  pasta in  a pot
      └ early error persists, later tokens         └ re-predicted with richer context
        condition on it
 ───────────────────────────────────────────────────────────────────────────────────────
 re-mask budget k_t: ▇▆▅▄▃▂▁ → 0   |  NFE: 64 = 64  |  Gen. PPL 42.1 → 27.8  |  pass@1 31% → 44%
```

The sentence is a placeholder I made up. A real sample from your OpenWebText or code-infilling runs where ReMask fixes an early token would be stronger.

## Things to settle in the paper

- **Negative result:** "Re-evaluating Confidence Remasking in Masked Diffusion Language Models" (NeurIPS 2026, [arXiv 2606.12232](https://arxiv.org/abs/2606.12232)) reports that confidence remasking gives little benefit at matched NFE. Your equal-NFE claim will be read against it.
- **Training-free competitors:** CORE (ICML 2026, [arXiv 2602.04096](https://arxiv.org/abs/2602.04096)) is also a training-free remasking sampler. From memory, not from the atlas, so please verify: ReMDM (Wang et al., 2025) is another.

## Your call

Which template do you want (or "1 as recommended"), and in what format: TikZ, matplotlib, or SVG? I'd default to TikZ so it drops into the LaTeX source and stays editable.