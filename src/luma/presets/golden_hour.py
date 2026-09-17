from .base import BasePreset


class GoldenHourPreset(BasePreset):
    """
    A warm golden-hour look designed to recreate the soft,
    rich colours associated with late-afternoon sunlight.
    """

    name = "golden-hour"

    category = "Nature"

    description = (
        "A warm golden-hour look with rich sunlight and golden highlights."
    )

    settings = {
        "contrast": 10,
        "saturation": 12,
        "highlights": -8,
        "shadows": 12,
        "warmth": 25,
        "exposure": 5,
        "vignette": 4,

        "colour_grading": {
            "red": 15,
            "orange": 35,
            "yellow": 30,
        },
    }