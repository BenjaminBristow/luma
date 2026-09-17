from .base import BasePreset


class EightiesPreset(BasePreset):
    """
    A colourful 1980s-inspired look with stronger saturation,
    contrast and vivid warm and cool colours.
    """

    name = "80s"

    category = "Vintage"

    description = (
        "A vibrant colourful 1980s-inspired photography look."
    )

    settings = {
        "contrast": 12,
        "saturation": 18,
        "warmth": 5,
        "fade": 5,
        "grain": 15,
        "vignette": 3,

        "colour_grading": {
            "red": 15,
            "orange": 10,
            "blue": 15,
            "purple": 20,
            "magenta": 15,
        },
    }