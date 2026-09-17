from .base import BasePreset


class OceanPreset(BasePreset):
    """
    A cool, clean look designed for oceans, beaches and
    underwater environments.
    """

    name = "ocean"

    category = "Nature"

    description = (
        "A cool clean look that enhances blue and cyan tones."
    )

    settings = {
        "contrast": 12,
        "saturation": 15,
        "highlights": -12,
        "shadows": 10,
        "warmth": -15,
        "vignette": 4,
        "sharpen": 8,

        "colour_grading": {
            "cyan": 25,
            "blue": 30,
            "purple": 5,
        },
    }