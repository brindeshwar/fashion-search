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
            build_tryon_tab(catalog)
    return demo


def build_tryon_tab(catalog: Catalog) -> None:
    from . import tryon

    if not tryon.is_available():
        gr.Markdown("### Virtual try-on is not set up\n```\n" + tryon.INSTALL_HINT + "\n```")
        return

    from .core import embed_texts

    def find_garments(query):
        if not query.strip():
            return [], []
        hits = catalog.top_k(embed_texts([query])[0], 10)
        return [(catalog.path(i), catalog.table.category.iloc[i]) for i, _ in hits], [
            i for i, _ in hits
        ]

    def pick(hit_ids, evt: gr.SelectData):
        i = hit_ids[evt.index]
        return catalog.path(i), tryon.fashn_category(catalog.table.category.iloc[i])

    def run(person, garment, category, photo_type, steps, seed):
        if person is None or garment is None:
            raise gr.Error("Add a person photo and pick or upload a garment first.")
        return tryon.try_on(person, garment, category, photo_type, steps, seed)

    gr.Markdown(
        "Put a catalogue item on a photo of a person with **FASHN VTON v1.5**. "
        "The first run loads the model (~30 s)."
    )
    hit_ids = gr.State([])
    with gr.Row():
        with gr.Column():
            person = gr.Image(type="pil", label="1. Person photo (front-facing works best)")
        with gr.Column():
            q = gr.Textbox(
                label="2. Find a garment in the catalogue (or upload one below)",
                placeholder="e.g. red plaid flannel",
            )
            hits = gr.Gallery(columns=5, height=200, object_fit="contain", show_label=False)
            garment = gr.Image(type="pil", label="Selected garment", height=240)
        with gr.Column():
            output = gr.Image(label="Result", interactive=False)
    with gr.Row():
        category = gr.Dropdown(["tops", "bottoms", "one-pieces"], value="tops", label="Category")
        photo_type = gr.Radio(
            ["flat-lay", "model"],
            value="flat-lay",
            label="Garment photo",
            info="flat-lay = product shot, model = worn by a person",
        )
        steps = gr.Slider(10, 50, 30, step=5, label="Steps (quality vs speed)")
        seed = gr.Number(42, precision=0, label="Seed")
    q.submit(find_garments, q, [hits, hit_ids])
    hits.select(pick, hit_ids, [garment, category])
    gr.Button("3. Try it on", variant="primary").click(
        run, [person, garment, category, photo_type, steps, seed], output
    )


def launch(catalog: Catalog, port: int = 7860) -> None:
    build_app(catalog).launch(server_port=port, allowed_paths=[str(catalog.image_dir)])
