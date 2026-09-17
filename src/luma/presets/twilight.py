from .base import BasePreset


class TwilightPreset(BasePreset):
    """
    A colourful dusk-inspired look combining cool blue shadows
    with subtle purple, red and warm horizon tones.
    """

    name = "twilight"

    category = "Weather & Atmosphere"

    description = (
        "A colourful dusk look combining blue, purple and warm tones."
    )

    settings = {
        "contrast": 15,
        "saturation": 12,
        "highlights": -12,
        "shadows": 15,
        "warmth": -5,
        "exposure": -3,
        "vignette": 6,

        "colour_grading": {
            "red": 12,
            "orange": 8,
            "blue": 25,
            "purple": 30,
            "magenta": 15,
        },
    }