import numpy as np
from PIL import Image


def apply_grain(
    image: Image.Image,
    amount: int,
) -> Image.Image:
    """
    Add photographic grain to an image.

    Positive values increase the amount of grain.

    Grain is generated as random luminance noise and applied
    equally across the RGB channels so that the image retains
    its original colour balance.
    """

    if amount <= 0:
        return image

    image = image.convert("RGB")

    pixels = np.asarray(
        image,
        dtype=np.float32,
    )

    # Generate random noise centred around zero.
    # A larger amount produces stronger visible grain.
    noise = np.random.normal(
        0,
        amount * 0.35,
        pixels.shape[:2],
    )

    pixels += noise[..., np.newaxis]

    pixels = np.clip(
        pixels,
        0,
        255,
    )

    return Image.fromarray(
        pixels.astype(np.uint8),
        "RGB",
    )