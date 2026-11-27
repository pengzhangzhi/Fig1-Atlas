---
license: other
license_name: per-image-cc
license_link: LICENSE.md
pretty_name: Fig1 Atlas
configs:
- config_name: default
  data_files:
  - split: train
    path: images/**
tags:
- figures
- scientific-figures
- machine-learning
size_categories:
- 1K<n<10K
---

# Fig1 Atlas — Figure 1 images

Figure 1 crops from accepted ICLR / ICML / NeurIPS 2026 papers, for papers whose arXiv version is released under
an open Creative Commons license (CC-BY, CC-BY-SA, CC0, CC-BY-NC, CC-BY-NC-SA). Each image keeps the license of its
paper, given in the `license` column of `images/metadata.jsonl` together with title, authors and arXiv link.
NC-licensed images are for non-commercial use only.

Search, annotations (role / claim / layout / description) and the agent skill live in the GitHub repo:
https://github.com/pengzhangzhi/Fig1-Atlas

```python
from datasets import load_dataset
ds = load_dataset("fredzzp/fig1-atlas", split="train")
```

* `images/<id>.png` — 1600 px wide crop rendered from the paper PDF
* `thumbs/<id>.webp` — 480 px thumbnail

**Takedown / opt-in:** authors can ask for removal (or opt a paper in) by opening an issue at
https://github.com/pengzhangzhi/Fig1-Atlas/issues.
