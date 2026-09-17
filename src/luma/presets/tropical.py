from .base import BasePreset


class TropicalPreset(BasePreset):
    """
    A vibrant tropical look designed for beaches, plants,
    bright skies and colourful outdoor environments.
    """

    name = "tropical"

    category = "Nature"

    description = (
        "A bright vibrant look for tropical landscapes and beaches."
    )

    settings = {
        "contrast": 8,
        "saturation": 22,
        "highlights": -10,
        "shadows": 12,
        "warmth": 12,
        "exposure": 5,
        "sharpen": 8,

        "colour_grading": {
            "orange": 20,
            "yellow": 15,
            "green": 20,
            "cyan": 20,
            "blue": 15,
        },
    }