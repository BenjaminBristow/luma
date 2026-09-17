from .base import BasePreset


class ForestPreset(BasePreset):
    """
    A rich natural look designed for forests, woodland and
    green outdoor environments.

    Greens are strengthened while highlights are controlled
    to preserve detail beneath trees.
    """

    name = "forest"

    category = "Nature"

    description = (
        "A rich natural look that enhances greens and woodland tones."
    )

    settings = {
        "contrast": 12,
        "saturation": 10,
        "highlights": -12,
        "shadows": 15,
        "warmth": 3,
        "vignette": 5,
        "sharpen": 8,

        "colour_grading": {
            "green": 25,
            "yellow": 8,
            "cyan": 5,
        },
    }