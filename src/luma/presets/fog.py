from .base import BasePreset


class FogPreset(BasePreset):
    """
    A heavier atmospheric effect designed to make an image
    feel surrounded by dense fog.
    """

    name = "fog"

    category = "Weather & Atmosphere"

    description = (
        "A soft low-contrast look designed to simulate dense fog."
    )

    settings = {
        "contrast": -30,
        "saturation": -15,
        "highlights": 8,
        "shadows": 25,
        "exposure": 8,
        "fade": 28,
        "blur": 14,
        "warmth": -5,
    }