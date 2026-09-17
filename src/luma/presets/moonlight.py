from .base import BasePreset


class MoonlightPreset(BasePreset):
    """
    A cold nocturnal look inspired by scenes illuminated
    primarily by moonlight.
    """

    name = "moonlight"

    category = "Weather & Atmosphere"

    description = (
        "A cold blue nocturnal look inspired by moonlit scenes."
    )

    settings = {
        "contrast": 18,
        "saturation": -5,
        "highlights": -15,
        "shadows": -8,
        "warmth": -30,
        "exposure": -10,
        "vignette": 12,
        "sharpen": 5,

        "colour_grading": {
            "blue": 30,
            "cyan": 15,
            "orange": -10,
            "yellow": -15,
        },
    }