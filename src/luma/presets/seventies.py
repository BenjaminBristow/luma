from .base import BasePreset


class SeventiesPreset(BasePreset):
    """
    A warm, earthy 1970s-inspired photographic look.

    The preset emphasises warm colours, faded contrast and
    noticeable analogue-style grain.
    """

    name = "70s"

    category = "Vintage"

    description = (
        "A warm earthy 1970s-inspired analogue photography look."
    )

    settings = {
        "contrast": -8,
        "saturation": 5,
        "warmth": 18,
        "fade": 18,
        "grain": 28,
        "sepia": 12,
        "vignette": 5,

        "colour_grading": {
            "red": 10,
            "orange": 15,
            "yellow": 10,
            "green": -5,
        },
    }