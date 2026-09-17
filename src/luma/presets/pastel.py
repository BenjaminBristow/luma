from .base import BasePreset


class PastelPreset(BasePreset):
    """
    A soft colourful look inspired by pastel photography.

    Contrast is reduced and darker areas are lifted to create
    gentle colours and a lighter overall appearance.
    """

    name = "pastel"

    category = "Artistic"

    description = (
        "A soft colourful look with gentle pastel tones."
    )

    settings = {
        "contrast": -25,
        "saturation": 8,
        "highlights": 5,
        "shadows": 25,
        "exposure": 8,
        "fade": 15,
        "warmth": 3,
        "vignette": -5,

        "colour_grading": {
            "red": 8,
            "orange": 8,
            "yellow": 8,
            "green": 8,
            "cyan": 8,
            "blue": 8,
            "purple": 8,
            "magenta": 8,
        },
    }