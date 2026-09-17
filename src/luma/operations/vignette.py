import numpy as np
from PIL import Image


def apply_vignette(image: Image.Image, amount: int) -> Image.Image:
    """
    Darken the edges of an image to create a vignette effect.

    Positive values darken the edges.
    Negative values brighten the edges.
    """

    # There is nothing to change when the preset requests
    # no vignette adjustment.
    if amount == 0:
        return image

    # Convert the image into RGB.
    image = image.convert("RGB")

    # Convert the image into a NumPy array.
    pixels = np.asarray(image, dtype=np.float32)

    # Get the image dimensions.
    height, width = pixels.shape[:2]

    # Find the centre of the image.
    centre_x = width / 2
    centre_y = height / 2

    # Create arrays containing the x and y coordinates
    # of every pixel in the image.
    y, x = np.ogrid[:height, :width]

    # Calculate the distance of every pixel from the centre.
    distance = np.sqrt(
        (x - centre_x) ** 2
        + (y - centre_y) ** 2
    )

    # Calculate the maximum possible distance from the centre.
    max_distance = np.sqrt(
        centre_x ** 2
        + centre_y ** 2
    )

    # Normalise the distances to a 0.0 - 1.0 range.
    distance_factor = distance / max_distance

    # Make the vignette stronger towards the edges.
    vignette_strength = distance_factor ** 2

    # Convert the percentage into a brightness multiplier.
    adjustment = amount * vignette_strength
    multiplier = 1 - (adjustment / 100)

    # Apply the multiplier to every colour channel.
    pixels *= multiplier[..., np.newaxis]

    # Keep values inside the valid RGB range.
    pixels = np.clip(pixels, 0, 255)

    # Convert the result back into a Pillow image.
    return Image.fromarray(pixels.astype(np.uint8), "RGB")