# Remask, Don't Regret: Self-Correcting Masked Diffusion Language Models

## Abstract
Masked diffusion language models (MDLMs) generate text by iteratively unmasking tokens, but once a token is
unmasked it is frozen: early mistakes can never be revised and they compound as later tokens condition on them.
We introduce ReMask, a training-free sampler that lets an MDLM undo its own decisions. At each step ReMask scores
every already-unmasked token with the model's own posterior, re-masks the lowest-confidence ones, and re-predicts
them with the richer context now available. A simple budget schedule keeps the number of network evaluations
unchanged. On OpenWebText, ReMask lowers generative perplexity from 42.1 to 27.8 at 64 steps without reducing
entropy, and on code infilling it raises pass@1 from 31% to 44%. We show that most of the gain comes from
correcting tokens committed in the first 20% of steps.

## Method (notes)
- Standard MDLM sampling: mask -> unmask by confidence -> token frozen forever.
- ReMask: after each unmask step, compute per-token posterior confidence, re-mask bottom-k, continue.
- Budget schedule: k_t decays linearly to 0; total NFE equal to baseline.
