from .base import BasePreset


class StormPreset(BasePreset):
    """
    A dark and dramatic look designed to emphasise the atmosphere
    of stormy skies and harsh weather.
    """

    name = "storm"

    category = "Weather & Atmosphere"

    description = (
        "A dark dramatic look for stormy skies and harsh weather."
    )

    settings = {
        "contrast": 25,
        "saturation": -12,
        "highlights": -25,
        "shadows": -5,
        "warmth": -15,
        "exposure": -8,
        "vignette": 12,
        "sharpen": 10,

        "colour_grading": {
            "blue": 15,
            "cyan": 12,
            "yellow": -10,
            "orange": -5,
        },
    }