from .base import BasePreset


class UrbanPreset(BasePreset):
    """
    A modern city photography look balancing strong contrast,
    controlled colour and crisp detail.
    """

    name = "urban"

    category = "Urban"

    description = (
        "A modern city look with strong contrast and crisp detail."
    )

    settings = {
        "contrast": 22,
        "saturation": -5,
        "highlights": -15,
        "shadows": 10,
        "warmth": -5,
        "exposure": 2,
        "vignette": 6,
        "sharpen": 15,

        "colour_grading": {
            "blue": 12,
            "cyan": 8,
            "orange": 8,
            "red": 5,
        },
    }