"""Tag vocabulary for zero-shot tagging.

Each attribute maps to (prompt template, candidate values). The template must contain
exactly one ``{}``, which is filled with each value to build the text prompt.
Changing this file changes the tags: rerun ``fashion-search index`` afterwards.
"""

ATTRIBUTES: dict[str, tuple[str, list[str]]] = {
    "category": (
        "a photo of a {}",
        [
            "button-up shirt",
            "t-shirt",
            "polo shirt",
            "blouse",
            "sweater",
            "hoodie",
            "jacket",
            "dress",
            "tank top",
        ],
    ),
    "color": (
        "a {} piece of clothing",
        [
            "white",
            "black",
            "grey",
            "navy",
            "blue",
            "light blue",
            "red",
            "pink",
            "green",
            "olive",
            "yellow",
            "orange",
            "brown",
            "beige",
            "purple",
            "multicolored",
        ],
    ),
    "pattern": (
        "a {} shirt",
        [
            "plain solid-color",
            "striped",
            "checked plaid",
            "floral",
            "graphic print",
            "polka dot",
            "denim",
            "tropical hawaiian",
        ],
    ),
    "sleeve": ("a shirt with {}", ["long sleeves", "short sleeves", "no sleeves"]),
    "style": ("a {} outfit", ["formal office", "casual", "vintage", "streetwear", "sporty"]),
}
