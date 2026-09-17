from .base import BasePreset


class NinetiesPreset(BasePreset):
    """
    A slightly muted 1990s-inspired look with soft contrast,
    natural colours and analogue photographic grain.
    """

    name = "90s"

    category = "Vintage"

    description = (
        "A muted 1990s-inspired analogue photography look."
    )

    settings = {
        "contrast": -5,
        "saturation": -5,
        "highlights": -10,
        "shadows": 10,
        "warmth": 3,
        "fade": 12,
        "grain": 20,
        "vignette": 4,
    }