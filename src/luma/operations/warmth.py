import numpy as np
from PIL import Image


def apply_warmth(image: Image.Image, amount: int) -> Image.Image:
    """
    Adjust the overall colour temperature of an image.

    Positive values make the image warmer.
    Negative values make the image cooler.
    """

    # There is nothing to change when the preset requests
    # no warmth adjustment.
    if amount == 0:
        return image

    # Convert to RGB so we have predictable colour channels.
    image = image.convert("RGB")

    # Convert the image into a NumPy array.
    pixels = np.asarray(image, dtype=np.float32).copy()

    # Convert the percentage into a colour adjustment.
    adjustment = amount * 2

    # Increase red to make the image warmer.
    pixels[..., 0] += adjustment

    # Decrease blue by the same amount.
    pixels[..., 2] -= adjustment

    # Keep all colour values within the valid RGB range.
    pixels = np.clip(pixels, 0, 255)

    # Convert the result back into a Pillow image.
    return Image.fromarray(pixels.astype(np.uint8), "RGB")