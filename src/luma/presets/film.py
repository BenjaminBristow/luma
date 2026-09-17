from .base import BasePreset


class FilmPreset(BasePreset):
    """
    A general photographic film look with subtle grain,
    controlled contrast and slightly warm colours.
    """

    name = "film"

    category = "Vintage"

    description = (
        "A subtle photographic film look with natural grain and warmth."
    )

    settings = {
        "contrast": 10,
        "saturation": -5,
        "highlights": -10,
        "shadows": 8,
        "warmth": 5,
        "fade": 8,
        "grain": 18,
        "sharpen": 5,
        "vignette": 4,
    }