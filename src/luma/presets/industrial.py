from .base import BasePreset


class IndustrialPreset(BasePreset):
    """
    A cold, high-contrast look designed for factories,
    machinery, warehouses and industrial environments.
    """

    name = "industrial"

    category = "Urban"

    description = (
        "A cold high-contrast look for industrial environments."
    )

    settings = {
        "contrast": 28,
        "saturation": -15,
        "highlights": -15,
        "shadows": -5,
        "warmth": -12,
        "exposure": -3,
        "vignette": 8,
        "sharpen": 18,

        "colour_grading": {
            "blue": 12,
            "cyan": 10,
            "yellow": -8,
            "orange": -5,
        },
    }