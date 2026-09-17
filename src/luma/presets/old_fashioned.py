from .base import BasePreset


class OldFashionedPreset(BasePreset):
    """
    A heavily aged photographic look inspired by old printed
    photographs and family albums.
    """

    name = "old-fashioned"

    category = "Vintage"

    description = (
        "A warm aged-photograph look with faded tones and grain."
    )

    settings = {
        "contrast": -10,
        "saturation": -15,
        "warmth": 12,
        "fade": 25,
        "grain": 30,
        "sepia": 20,
        "vignette": 8,
    }