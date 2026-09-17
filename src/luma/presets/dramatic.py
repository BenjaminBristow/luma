from .base import BasePreset


class DramaticPreset(BasePreset):
    """
    A powerful cinematic look designed to emphasise lighting,
    contrast and atmosphere.

    Unlike Horror or Thriller, this preset is intended to remain
    relatively natural while making the photograph feel more
    visually striking.
    """

    name = "dramatic"

    category = "Dark & Cinematic"

    description = (
        "A powerful cinematic look with strong contrast and atmosphere."
    )

    settings = {
        "contrast": 32,
        "saturation": 8,
        "highlights": -25,
        "shadows": 18,
        "warmth": 5,
        "exposure": -2,
        "vignette": 12,
        "sharpen": 15,

        "colour_grading": {
            "red": 12,
            "orange": 15,
            "blue": 12,
            "purple": 8,
        },
    }