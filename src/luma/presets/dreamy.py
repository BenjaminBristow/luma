from .base import BasePreset


class DreamyPreset(BasePreset):
    """
    A soft bright look designed to create a dreamy,
    romantic and slightly surreal atmosphere.

    Reduced contrast, lifted shadows and subtle blur soften
    the image while maintaining enough colour to keep it lively.
    """

    name = "dreamy"

    category = "Artistic"

    description = (
        "A soft bright look with gentle colours and a dreamy atmosphere."
    )

    settings = {
        "contrast": -15,
        "saturation": 12,
        "highlights": 5,
        "shadows": 20,
        "exposure": 8,
        "warmth": 8,
        "fade": 12,
        "blur": 4,
        "vignette": -5,
    }