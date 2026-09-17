from .base import BasePreset


class CinematicPreset(BasePreset):
    """
    A cinematic preset with controlled contrast, muted colours
    and subtle film-like texture.
    """

    name = "cinematic"

    category = "Dark & Cinematic"
    
    description = (
        "A cinematic look with controlled contrast, muted colours "
        "and subtle film texture."
    )

    settings = {
        "contrast": 20,
        "saturation": -10,
        "highlights": -15,
        "shadows": 10,
        "warmth": 5,
        "vignette": 8,

        # A small amount of fade reduces the harsh digital appearance.
        "fade": 5,

        # Subtle grain gives the image a more photographic character.
        "grain": 12,

        # A little sharpening keeps details defined after the tonal
        # adjustments have been applied.
        "sharpen": 10,
    }