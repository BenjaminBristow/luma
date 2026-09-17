import numpy as np
from PIL import Image


def apply_exposure(
    image: Image.Image,
    amount: int,
) -> Image.Image:
    """
    Adjust the exposure of an image.

    Positive values increase exposure.
    Negative values decrease exposure.

    The adjustment affects the entire tonal range while preserving
    the relative relationship between different brightness levels.
    """

    if amount == 0:
        return image

    image = image.convert("RGB")

    pixels = np.asarray(
        image,
        dtype=np.float32,
    ) / 255.0

    # Convert the percentage into an exposure multiplier.
    # A positive value increases the amount of light, while a
    # negative value reduces it.
    factor = 2 ** (amount / 100)

    pixels *= factor

    pixels = np.clip(
        pixels,
        0,
        1,
    )

    return Image.fromarray(
        (pixels * 255).astype(np.uint8),
        "RGB",
    )