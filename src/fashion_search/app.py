"""Gradio UI: text search, image search and tag browsing over the catalogue."""

import gradio as gr

from .catalog import Catalog
from .taxonomy import ATTRIBUTES

TAG_COLS = list(ATTRIBUTES)


def build_app(catalog: Catalog) -> gr.Blocks:
    # Imported here so the UI can be built (and tested) without loading the model.
    from .core import embed_images, embed_texts

    def caption(i, score=None):
        row = catalog.table.iloc[i]
        tags = " · ".join(str(row[c]) for c in ["color", "pattern", "sleeve"])
        return f"{score:.2f} | {tags}" if score is not None else tags

    def results(query_emb, k):
        return [(catalog.path(i), caption(i, s)) for i, s in catalog.top_k(query_emb, int(k))]

    def search_text(query, k):
        return results(embed_texts([query])[0], k) if query.strip() else []

    def search_image(image, k):
        return results(embed_images([image])[0], k) if image is not None else []

    def browse(*values):
        idx = catalog.filter(**dict(zip(TAG_COLS, values, strict=True)))
        return [(catalog.path(i), caption(i)) for i in idx[:200]], f"{len(idx)} items"

    def gallery():
        return gr.Gallery(columns=5, height=620, object_fit="contain", show_label=False)

    with gr.Blocks(title="Fashion Visual Search") as demo:
        gr.Markdown(
            "# Fashion Visual Search\n"
            f"{len(catalog)} items indexed with **Marqo-FashionSigLIP**. "
            "Tags are zero-shot; nothing was trained on this data."
        )
        with gr.Tab("Search by text"):
            with gr.Row():
                q = gr.Textbox(
                    placeholder="e.g. blue checked flannel with long sleeves",
                    label="Describe what you want",
                    scale=4,
                )
                k1 = gr.Slider(5, 50, 15, step=5, label="Results", scale=1)
            gr.Examples(
                [
                    "red and black plaid flannel",
                    "white formal office shirt",
                    "tropical hawaiian print short sleeve",
                    "denim shirt",
                    "vintage floral blouse",
                ],
                q,
            )
            out1 = gallery()
            q.submit(search_text, [q, k1], out1)
            gr.Button("Search", variant="primary").click(search_text, [q, k1], out1)

        with gr.Tab("Search by image"):
            with gr.Row():
                img = gr.Image(type="pil", label="Upload a clothing photo", height=320)
                k2 = gr.Slider(5, 50, 15, step=5, label="Results")
            out2 = gallery()
            img.change(search_image, [img, k2], out2)

        with gr.Tab("Browse by tags"):
            with gr.Row():
                dropdowns = [
                    gr.Dropdown(["any"] + sorted(catalog.table[c].unique()), value="any", label=c)
                    for c in TAG_COLS
                ]
            count = gr.Markdown()
            out3 = gallery()
            for d in dropdowns:
                d.change(browse, dropdowns, [out3, count])
            demo.load(browse, dropdowns, [out3, count])

        with gr.Tab("Virtual try-on"):
            gr.Markdown(
                "Coming next: put any of these shirts on a photo of a person "
                "(FASHN VTON v1.5). See docs/PROGRESS.md."
            )
    return demo


def launch(catalog: Catalog, port: int = 7860) -> None:
    build_app(catalog).launch(server_port=port, allowed_paths=[str(catalog.image_dir)])
