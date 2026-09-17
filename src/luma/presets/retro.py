from .base import BasePreset


class RetroPreset(BasePreset):
    """
    A colourful retro look inspired by older consumer photography.

    The preset combines faded contrast, warmth, grain and slightly
    muted colours to create an aged but still colourful appearance.
    """

    name = "retro"

    category = "Vintage"

    description = (
        "A warm, faded and colourful vintage photography look."
    )

    settings = {
        "contrast": -5,
        "saturation": 5,
        "warmth": 10,
        "fade": 18,
        "grain": 22,
        "vignette": 5,
    }