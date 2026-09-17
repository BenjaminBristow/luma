from .base import BasePreset


class MonochromePreset(BasePreset):
    """
    A strong black-and-white inspired look.

    Colour is heavily reduced while contrast and sharpening
    are increased to emphasise shapes, textures and lighting.
    """

    name = "monochrome"

    category = "Artistic"

    description = (
        "A strong black-and-white inspired look with bold contrast."
    )

    settings = {
        "contrast": 30,
        "saturation": -100,
        "highlights": -10,
        "shadows": -5,
        "exposure": 2,
        "vignette": 10,
        "grain": 12,
        "sharpen": 15,
    }