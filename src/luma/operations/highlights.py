import numpy as np
from PIL import Image


def apply_highlights(image: Image.Image, amount: int) -> Image.Image:
    """
    Adjust the brightness of the brightest areas of an image.

    The amount is expressed as a percentage.

    Positive values brighten highlights.
    Negative values darken highlights.

    Unlike a normal brightness adjustment, darker areas are
    affected much less than brighter areas.
    """

    # There is nothing to change when the preset requests
    # no highlight adjustment.
    if amount == 0:
        return image

    # Convert the image into RGB so that we know exactly
    # which three colour channels we are working with.
    image = image.convert("RGB")

    # Convert the Pillow image into a NumPy array.
    #
    # Instead of processing one pixel at a time in Python,
    # NumPy allows us to perform calculations across the
    # entire image much more efficiently.
    pixels = np.asarray(image, dtype=np.float32)

    # Calculate the perceived brightness of every pixel.
    #
    # The final dimensions are:
    # height × width × 3
    #
    # Using [..., 0], [..., 1] and [..., 2] lets us access
    # every red, green and blue channel at once.
    brightness = (
        0.299 * pixels[..., 0]
        + 0.587 * pixels[..., 1]
        + 0.114 * pixels[..., 2]
    )

    # Normalise brightness to a 0.0 - 1.0 range.
    brightness_factor = brightness / 255

    # Bright pixels receive a stronger adjustment.
    highlight_strength = brightness_factor ** 2

    # Convert the percentage into a pixel adjustment.
    adjustment = amount * highlight_strength

    # Apply the same adjustment to all three colour channels.
    pixels += adjustment[..., np.newaxis]

    # Keep every colour value inside the valid RGB range.
    pixels = np.clip(pixels, 0, 255)

    # Convert the NumPy array back into an image.
    return Image.fromarray(pixels.astype(np.uint8), "RGB")