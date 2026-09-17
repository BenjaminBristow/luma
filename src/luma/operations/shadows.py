import numpy as np
from PIL import Image


def apply_shadows(image: Image.Image, amount: int) -> Image.Image:
    """
    Adjust the brightness of the darker areas of an image.

    The amount is expressed as a percentage.

    Positive values brighten shadows.
    Negative values darken shadows.

    Unlike a normal brightness adjustment, brighter areas are
    affected much less than darker areas.
    """

    # There is nothing to change when the preset requests
    # no shadow adjustment.
    if amount == 0:
        return image

    # Convert the image into RGB so that we know exactly
    # which colour channels we are working with.
    image = image.convert("RGB")

    # Convert the image into a NumPy array so calculations
    # can be performed on the whole image efficiently.
    pixels = np.asarray(image, dtype=np.float32)

    # Calculate the perceived brightness of every pixel.
    brightness = (
        0.299 * pixels[..., 0]
        + 0.587 * pixels[..., 1]
        + 0.114 * pixels[..., 2]
    )

    # Normalise brightness to a 0.0 - 1.0 range.
    brightness_factor = brightness / 255

    # Dark pixels receive the strongest adjustment.
    # Bright pixels receive very little adjustment.
    shadow_strength = (1 - brightness_factor) ** 2

    # Convert the percentage into a pixel adjustment.
    adjustment = amount * shadow_strength

    # Apply the adjustment to all colour channels.
    pixels += adjustment[..., np.newaxis]

    # Prevent values from going below 0 or above 255.
    pixels = np.clip(pixels, 0, 255)

    # Convert the NumPy array back into a Pillow image.
    return Image.fromarray(pixels.astype(np.uint8), "RGB")