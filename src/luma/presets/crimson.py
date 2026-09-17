from .base import BasePreset


class CrimsonPreset(BasePreset):
    """
    A bold artistic look built around deep red and crimson tones.

    Red and orange colours are strengthened while cooler colours
    are reduced to make warm tones dominate the photograph.
    """

    name = "crimson"

    category = "Artistic"

    description = (
        "A bold artistic look dominated by rich crimson and red tones."
    )

    settings = {
        "contrast": 20,
        "saturation": 20,
        "highlights": -12,
        "shadows": 5,
        "warmth": 15,
        "exposure": -2,
        "vignette": 10,
        "sharpen": 8,

        "colour_grading": {
            "red": 45,
            "orange": 25,
            "magenta": 30,
            "yellow": 5,
            "green": -20,
            "cyan": -15,
            "blue": -10,
        },
    }