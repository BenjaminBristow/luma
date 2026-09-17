from .base import BasePreset


class AntiquePreset(BasePreset):
    """
    An aged and slightly faded look inspired by antique photographs.

    It combines sepia tones with reduced contrast, warmth and grain.
    """

    name = "antique"

    category = "Vintage"

    description = (
        "An aged antique photograph with warm faded tones."
    )

    settings = {
        "contrast": -15,
        "saturation": -20,
        "warmth": 15,
        "fade": 28,
        "sepia": 45,
        "grain": 28,
        "vignette": 10,
    }