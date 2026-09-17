from .base import BasePreset


class OvercastPreset(BasePreset):
    """
    A muted natural look designed to recreate the soft,
    cool lighting of an overcast day.
    """

    name = "overcast"

    category = "Weather & Atmosphere"

    description = (
        "A cool muted look inspired by cloudy overcast conditions."
    )

    settings = {
        "contrast": -8,
        "saturation": -12,
        "highlights": -20,
        "shadows": 12,
        "warmth": -8,
        "exposure": -2,
        "fade": 5,

        "colour_grading": {
            "blue": 8,
            "cyan": 10,
            "yellow": -5,
        },
    }