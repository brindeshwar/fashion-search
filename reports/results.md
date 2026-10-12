# Old vs new

| Metric | Old MLP (trained) | FashionSigLIP (zero-shot) |
|---|---|---|
| Fashion-MNIST test accuracy (10k images) | 87.9% | 77.5% |
| Same test set, inverted (dark item on light background) | 10.0% | 83.3% |
| ...share of inverted images predicted 'Shirt' (true rate 10%) | 100.0% | 3.9% |
| Held-out shirt photos classified as 'Shirt' | 100.0% | 97.0% |
| Held-out shirt photos classified as any top | 100.0% | 100.0% |

Shirt test set: 100 photos from ../Dataset held out from baseline training (seed 0). The baseline was trained on Fashion-MNIST + the other 400 photos. FashionSigLIP saw no training data from either set.

**Reading this:** the MLP wins on raw Fashion-MNIST, the data it was fitted to. But on the inverted copy it labels almost everything 'Shirt': it learned that 'light background = shirt photo' instead of what a shirt looks like, which is also why it scores 100% on the held-out shirt photos. FashionSigLIP keeps its accuracy across both looks, and also handles open-vocabulary tagging and search, which the MLP cannot do at all.
