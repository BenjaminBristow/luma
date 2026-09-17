from .base import BasePreset


class AuroraPreset(BasePreset):
    """
    A vibrant and atmospheric preset designed to make
    colourful scenes look richer and more visually striking.

    It particularly suits sunsets, landscapes and outdoor
    photography.
    """

    name = "aurora"

    category = "Weather & Atmosphere"

    description = (
        "A vibrant atmospheric look designed for colourful "
        "scenes and sunsets."
    )

    settings = {
        "contrast": 15,
        "saturation": 15,
        "highlights": -10,
        "shadows": 12,
        "warmth": 8,
        "vignette": 5,

        # A small exposure boost helps colourful outdoor scenes
        # feel brighter and more vibrant.
        "exposure": 5,

        # Keep fine details crisp in landscapes and photographs.
        "sharpen": 8,

        # Enhance specific colours rather than simply increasing
        # saturation across the entire photograph.
        "colour_grading": {
            "red": 15,
            "orange": 25,
            "yellow": 5,
            "blue": 8,
            "purple": 15,
        },
    }