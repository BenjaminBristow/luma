from .base import BasePreset


class SepiaPreset(BasePreset):
    """
    A strong sepia preset designed to recreate the appearance
    of traditional brown-toned photographs.
    """

    name = "sepia"

    category = "Vintage"

    description = (
        "A classic warm brown sepia photographic effect."
    )

    settings = {
        "contrast": 5,
        "saturation": -25,
        "sepia": 90,
        "fade": 5,
        "grain": 10,
        "vignette": 5,
    }