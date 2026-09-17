from .base import BasePreset


class ThrillerPreset(BasePreset):
    """
    A tense cinematic look inspired by thriller photography.

    The combination of cool tones, controlled highlights and
    strong contrast gives scenes a darker and more suspenseful
    atmosphere.
    """

    name = "thriller"

    category = "Dark & Cinematic"

    description = (
        "A tense cool-toned cinematic look with strong contrast."
    )

    settings = {
        "contrast": 28,
        "saturation": -18,
        "highlights": -22,
        "shadows": -5,
        "warmth": -12,
        "exposure": -5,
        "vignette": 15,
        "sharpen": 12,

        "colour_grading": {
            "blue": 18,
            "cyan": 12,
            "orange": -8,
            "yellow": -10,
        },
    }