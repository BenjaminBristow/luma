from .base import BasePreset


class BleachPreset(BasePreset):
    """
    A bleach-bypass inspired look with high contrast,
    reduced saturation and a slightly cold appearance.

    The result is gritty and photographic rather than colourful.
    """

    name = "bleach"

    category = "Artistic"

    description = (
        "A gritty bleach-bypass inspired look with muted colours."
    )

    settings = {
        "contrast": 35,
        "saturation": -45,
        "highlights": -20,
        "shadows": 15,
        "warmth": -8,
        "exposure": -2,
        "fade": 5,
        "grain": 18,
        "vignette": 8,
        "sharpen": 15,

        "colour_grading": {
            "blue": 10,
            "cyan": 8,
            "orange": -8,
            "yellow": -8,
        },
    }