import numpy as np
from PIL import Image


def apply_sepia(
    image: Image.Image,
    amount: int,
) -> Image.Image:
    """
    Apply a sepia tone to an image.

    Positive values move the image towards warm brown and cream
    tones associated with old-fashioned photographs.

    The original brightness of the image is preserved as much
    as possible while the colour balance is shifted towards
    warm sepia tones.
    """

    if amount <= 0:
        return image

    image = image.convert("RGB")

    pixels = np.asarray(
        image,
        dtype=np.float32,
    )

    # Convert the image to luminance while preserving its
    # overall brightness information.
    grey = (
        0.299 * pixels[..., 0]
        + 0.587 * pixels[..., 1]
        + 0.114 * pixels[..., 2]
    )

    # Build a warm sepia version from the original luminance.
    #
    # The red channel remains strongest, green is slightly lower,
    # and blue is reduced to create the characteristic brown tone.
    sepia_pixels = np.empty_like(pixels)

    sepia_pixels[..., 0] = grey * 1.08
    sepia_pixels[..., 1] = grey * 0.95
    sepia_pixels[..., 2] = grey * 0.75

    sepia_pixels = np.clip(
        sepia_pixels,
        0,
        255,
    )

    strength = np.clip(
        amount / 100,
        0,
        1,
    )

    # Blend the original image with the sepia version.
    # This means lower values retain more of the original colour.
    pixels = (
        pixels * (1 - strength)
        + sepia_pixels * strength
    )

    pixels = np.clip(
        pixels,
        0,
        255,
    )

    return Image.fromarray(
        pixels.astype(np.uint8),
        "RGB",
    )