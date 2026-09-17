from .base import BasePreset


class MistPreset(BasePreset):
    """
    A soft atmospheric look designed to recreate the appearance
    of light mist or haze.
    """

    name = "mist"

    category = "Weather & Atmosphere"

    description = (
        "A soft hazy look inspired by light atmospheric mist."
    )

    settings = {
        "contrast": -18,
        "saturation": -8,
        "highlights": 5,
        "shadows": 18,
        "exposure": 5,
        "fade": 18,
        "blur": 8,
        "warmth": -2,
    }