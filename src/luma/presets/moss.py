from .base import BasePreset


class MossPreset(BasePreset):
    """
    A dark earthy green look inspired by moss, damp woodland
    and shaded natural environments.
    """

    name = "moss"

    category = "Nature"

    description = (
        "A dark earthy green look inspired by moss and shaded woodland."
    )

    settings = {
        "contrast": 15,
        "saturation": 5,
        "highlights": -15,
        "shadows": 8,
        "warmth": -3,
        "vignette": 10,

        "colour_grading": {
            "green": 30,
            "yellow": -5,
            "cyan": 5,
        },
    }