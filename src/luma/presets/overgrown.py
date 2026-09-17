from .base import BasePreset


class OvergrownPreset(BasePreset):
    """
    A lush, atmospheric look designed for dense vegetation,
    abandoned places covered in plants and heavily overgrown areas.
    """

    name = "overgrown"

    category = "Nature"

    description = (
        "A lush atmospheric look for dense vegetation and overgrown places."
    )

    settings = {
        "contrast": 8,
        "saturation": 15,
        "highlights": -18,
        "shadows": 18,
        "warmth": -2,
        "fade": 5,
        "vignette": 8,

        "colour_grading": {
            "green": 35,
            "yellow": 10,
            "cyan": 8,
        },
    }