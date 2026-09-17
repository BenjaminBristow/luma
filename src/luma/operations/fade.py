import numpy as np
from PIL import Image


def apply_fade(
    image: Image.Image,
    amount: int,
) -> Image.Image:
    """
    Apply a faded, washed-out appearance to an image.

    Positive values reduce contrast and lift darker areas,
    creating a faded photographic appearance.

    This is particularly useful for retro, vintage and
    old-fashioned presets.
    """

    if amount <= 0:
        return image

    image = image.convert("RGB")

    # Convert RGB values from 0-255 into floating-point values
    # between 0 and 1 for easier mathematical processing.
    pixels = np.asarray(
        image,
        dtype=np.float32,
    ) / 255.0

    fade_strength = np.clip(
        amount / 100,
        0,
        1,
    )

    # Move pixels towards middle grey.
    # Dark areas are lifted while bright areas are brought down,
    # reducing the overall contrast of the photograph.
    pixels = pixels + (
        0.5 - pixels
    ) * fade_strength

    pixels = np.clip(
        pixels,
        0,
        1,
    )

    return Image.fromarray(
        (pixels * 255).astype(np.uint8),
        "RGB",
    )