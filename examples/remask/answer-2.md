The Figure 1 draft is rendered and saved next to `draft.md` as a PDF, a PNG and the matplotlib script that makes them. I checked the final render by eye and found no overlaps or clipped text.

What the figure shows:
- **Panel (a), standard MDLM:** "flew" is committed at step 1, marked wrong, and carried unchanged to the final row with a red connector labelled "frozen".
- **Panel (b), ReMask:** the same token gets the lowest posterior-confidence bar at step 2, is re-masked, and comes back as "cooked" at step 3.
- **Bottom strip:** the linearly decaying re-mask budget, "same network evaluations as baseline", and the two abstract numbers (Gen. PPL 42.1 → 27.8 at 64 steps, pass@1 31% → 44%).

Three things in it are placeholders, not your data:
- **The sentence** ("The chef flew/cooked the pasta in a pot") is one I made up. Swap in a real sample where ReMask fixes an early token.
- **The confidence bars** have illustrative heights. Replace the `CONF` list with the model's actual posteriors for that sample.
- **The budget bars** are a schematic of linear decay, not your actual schedule values.

One change from the sketch: I dropped the arrow from the re-masked token to its re-prediction because it collided with the confidence bars. The column alignment and the note under the panel carry that link instead.

To tweak it, edit the `EDIT` block at the top of the script (token rows, titles, notes, stats, colours, geometry in inches) and rerun `python3 fig1_remask.py`. The figure is 7.2 in wide, so check the token text size at your venue's column width.

The layout is adapted from Figure 1 of "Soft-Masked Diffusion Language Models" (ICLR 2026, arXiv 2510.17206), with the confidence bars borrowed from "Early Decisions Matter" (ICML 2026, arXiv 2604.10567). The script's docstring credits the first; only the layout is borrowed, not the artwork.

Files, next to `draft.md`:
- fig1_remask.pdf
- fig1_remask.png
- fig1_remask.py