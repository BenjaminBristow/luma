from .base import BasePreset


class AutumnPreset(BasePreset):
    """
    A warm autumnal look designed to enhance reds, oranges
    and yellows while maintaining natural contrast.
    """

    name = "autumn"

    category = "Nature"

    description = (
        "A warm autumn look that enhances red, orange and yellow foliage."
    )

    settings = {
        "contrast": 12,
        "saturation": 12,
        "highlights": -10,
        "shadows": 10,
        "warmth": 15,
        "vignette": 5,

        "colour_grading": {
            "red": 20,
            "orange": 30,
            "yellow": 25,
            "green": -10,
        },
    }