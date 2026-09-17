from .base import BasePreset


class HorrorPreset(BasePreset):
    """
    A dark unsettling look designed for horror photography.

    Deep shadows, cold colour and a slight green/cyan influence
    create an eerie and unnatural atmosphere.
    """

    name = "horror"

    category = "Dark & Cinematic"

    description = (
        "A cold unsettling look with deep shadows and eerie colour."
    )

    settings = {
        "contrast": 35,
        "saturation": -25,
        "highlights": -30,
        "shadows": -20,
        "warmth": -20,
        "exposure": -12,
        "vignette": 22,
        "grain": 15,
        "sharpen": 10,

        "colour_grading": {
            "green": 8,
            "cyan": 18,
            "blue": 15,
            "red": -10,
            "orange": -15,
        },
    }