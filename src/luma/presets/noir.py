from .base import BasePreset


class NoirPreset(BasePreset):
    """
    A classic noir-inspired look built around strong contrast,
    deep shadows and heavily reduced colour.

    It is designed to create a dramatic black-and-white-like
    appearance while retaining a small amount of colour.
    """

    name = "noir"

    category = "Dark & Cinematic"

    description = (
        "A high-contrast noir look with deep shadows and muted colour."
    )

    settings = {
        "contrast": 35,
        "saturation": -70,
        "highlights": -15,
        "shadows": -15,
        "exposure": -5,
        "vignette": 18,
        "grain": 18,
        "sharpen": 12,
    }