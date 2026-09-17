from .base import BasePreset


class AbandonedPreset(BasePreset):
    """
    A dark aged look designed for abandoned buildings,
    ruins and neglected environments.
    """

    name = "abandoned"

    category = "Urban"

    description = (
        "A dark aged look for abandoned and neglected places."
    )

    settings = {
        "contrast": 22,
        "saturation": -20,
        "highlights": -20,
        "shadows": 5,
        "warmth": -5,
        "exposure": -5,
        "fade": 12,
        "grain": 20,
        "vignette": 14,
        "sharpen": 12,

        "colour_grading": {
            "green": -10,
            "yellow": -8,
            "blue": 12,
            "cyan": 8,
        },
    }