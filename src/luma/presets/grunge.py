from .base import BasePreset


class GrungePreset(BasePreset):
    """
    A gritty high-contrast look inspired by grunge photography,
    underground music scenes and distressed urban environments.
    """

    name = "grunge"

    category = "Urban"

    description = (
        "A gritty high-contrast look with grain and muted colours."
    )

    settings = {
        "contrast": 35,
        "saturation": -18,
        "highlights": -12,
        "shadows": -5,
        "warmth": -5,
        "exposure": -3,
        "fade": 5,
        "grain": 38,
        "vignette": 15,
        "sharpen": 20,
    }