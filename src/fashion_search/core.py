"""Model loading, embeddings and zero-shot scoring (the only module that touches torch)."""

from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from .config import MODEL_ID
from .taxonomy import ATTRIBUTES

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=1)
def load_model():
    """Load FashionSigLIP once per process. Returns (model, preprocess, tokenizer)."""
    import open_clip

    model, _, preprocess = open_clip.create_model_and_transforms(MODEL_ID)
    tokenizer = open_clip.get_tokenizer(MODEL_ID)
    return model.to(DEVICE).eval(), preprocess, tokenizer


def _autocast():
    return torch.autocast(DEVICE, enabled=DEVICE == "cuda")


@torch.no_grad()
def embed_images(images, batch_size: int = 64) -> np.ndarray:
    """Embed PIL images or file paths. Returns L2-normalised (N, D) float32."""
    model, preprocess, _ = load_model()
    out = []
    for i in range(0, len(images), batch_size):
        batch = [
            (Image.open(x) if isinstance(x, (str, Path)) else x).convert("RGB")
            for x in images[i : i + batch_size]
        ]
        pixels = torch.stack([preprocess(im) for im in batch]).to(DEVICE)
        with _autocast():
            feats = model.encode_image(pixels, normalize=True)
        out.append(feats.float().cpu().numpy())
    return np.concatenate(out)


@torch.no_grad()
def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed text prompts. Returns L2-normalised (N, D) float32."""
    model, _, tokenizer = load_model()
    with _autocast():
        feats = model.encode_text(tokenizer(texts).to(DEVICE), normalize=True)
    return feats.float().cpu().numpy()


def softmax_scores(image_emb: np.ndarray, text_emb: np.ndarray, scale: float) -> np.ndarray:
    """Softmax over labels of scaled cosine similarity. Returns (N_images, N_labels)."""
    logits = scale * image_emb @ text_emb.T
    logits -= logits.max(axis=1, keepdims=True)
    probs = np.exp(logits)
    return probs / probs.sum(axis=1, keepdims=True)


def zero_shot(image_emb: np.ndarray, labels: list[str], template: str = "{}") -> np.ndarray:
    """Zero-shot classify embedded images against text labels."""
    model, _, _ = load_model()
    text_emb = embed_texts([template.format(label) for label in labels])
    return softmax_scores(image_emb, text_emb, model.logit_scale.exp().item())


def tag_images(image_emb: np.ndarray) -> dict[str, tuple[list[str], np.ndarray]]:
    """Tag every image on every attribute in the taxonomy. Returns {attr: (labels, probs)}."""
    return {
        attr: (labels, zero_shot(image_emb, labels, template))
        for attr, (template, labels) in ATTRIBUTES.items()
    }
