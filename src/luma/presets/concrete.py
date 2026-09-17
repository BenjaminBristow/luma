from .base import BasePreset


class ConcretePreset(BasePreset):
    """
    A cool desaturated look inspired by concrete architecture,
    brutalist buildings and modern urban structures.
    """

    name = "concrete"

    category = "Urban"

    description = (
        "A cool desaturated look inspired by concrete architecture."
    )

    settings = {
        "contrast": 25,
        "saturation": -35,
        "highlights": -15,
        "shadows": 8,
        "warmth": -15,
        "exposure": -2,
        "vignette": 6,
        "sharpen": 15,

        "colour_grading": {
            "blue": 8,
            "cyan": 8,
            "orange": -10,
            "yellow": -10,
        },
    }