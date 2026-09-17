from .base import BasePreset


class EtherealPreset(BasePreset):
    """
    A light atmospheric look designed to make photographs
    feel otherworldly and delicate.

    Cool highlights, lifted shadows and reduced contrast create
    a soft almost magical appearance.
    """

    name = "ethereal"

    category = "Artistic"

    description = (
        "A soft atmospheric look with an otherworldly appearance."
    )

    settings = {
        "contrast": -25,
        "saturation": 5,
        "highlights": 8,
        "shadows": 25,
        "exposure": 10,
        "warmth": -8,
        "fade": 20,
        "blur": 6,
        "vignette": -8,

        "colour_grading": {
            "cyan": 12,
            "blue": 15,
            "purple": 18,
            "magenta": 10,
        },
    }