from .base import BasePreset


class PolaroidPreset(BasePreset):
    """
    A bright, slightly faded and warm look inspired by
    instant-film photography.
    """

    name = "polaroid"

    category = "Vintage"

    description = (
        "A bright warm instant-film inspired look."
    )

    settings = {
        "contrast": -5,
        "saturation": 8,
        "exposure": 5,
        "warmth": 10,
        "fade": 15,
        "grain": 12,
        "highlights": -8,
        "shadows": 8,
    }