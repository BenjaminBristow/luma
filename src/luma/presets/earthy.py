from .base import BasePreset


class EarthyPreset(BasePreset):
    """
    A muted natural look built around warm brown, orange and
    subdued green tones.
    """

    name = "earthy"

    category = "Nature"

    description = (
        "A muted natural look with warm earthy colours."
    )

    settings = {
        "contrast": 5,
        "saturation": -5,
        "highlights": -10,
        "shadows": 12,
        "warmth": 12,
        "fade": 8,
        "grain": 8,

        "colour_grading": {
            "red": 10,
            "orange": 20,
            "yellow": 10,
            "green": -10,
        },
    }