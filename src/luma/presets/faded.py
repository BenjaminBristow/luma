from .base import BasePreset


class FadedPreset(BasePreset):
    """
    A washed-out photographic look with lifted shadows and
    reduced contrast.

    Unlike Sepia or Antique, this preset keeps much of the
    original colour of the photograph.
    """

    name = "faded"

    category = "Vintage"

    description = (
        "A soft washed-out look with reduced contrast and faded colours."
    )

    settings = {
        "contrast": -15,
        "saturation": -10,
        "fade": 35,
        "highlights": -5,
        "shadows": 15,
        "grain": 12,
    }