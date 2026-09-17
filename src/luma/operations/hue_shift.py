import numpy as np
from PIL import Image


def apply_hue_shift(
    image: Image.Image,
    amount: int,
) -> Image.Image:
    """
    Shift the hue of every colour in an image.

    The amount is measured in degrees.

    Positive values rotate colours forwards around the colour wheel.
    Negative values rotate them backwards.

    For example:
        30  -> shift all colours 30 degrees
        -30 -> shift all colours 30 degrees in the opposite direction
    """

    if amount == 0:
        return image

    image = image.convert("RGB")

    pixels = np.asarray(
        image,
        dtype=np.float32,
    ) / 255.0

    maximum = pixels.max(axis=2)
    minimum = pixels.min(axis=2)
    difference = maximum - minimum

    hue = np.zeros_like(maximum)

    non_zero = difference != 0

    red = pixels[..., 0]
    green = pixels[..., 1]
    blue = pixels[..., 2]

    red_dominant = (
        (maximum == red)
        & non_zero
    )

    green_dominant = (
        (maximum == green)
        & non_zero
    )

    blue_dominant = (
        (maximum == blue)
        & non_zero
    )

    hue[red_dominant] = (
        (green[red_dominant] - blue[red_dominant])
        / difference[red_dominant]
    ) % 6

    hue[green_dominant] = (
        (blue[green_dominant] - red[green_dominant])
        / difference[green_dominant]
    ) + 2

    hue[blue_dominant] = (
        (red[blue_dominant] - green[blue_dominant])
        / difference[blue_dominant]
    ) + 4

    hue *= 60

    # Rotate every hue around the colour wheel.
    hue = (hue + amount) % 360

    saturation = np.zeros_like(maximum)

    saturation[non_zero] = (
        difference[non_zero] / maximum[non_zero]
    )

    value = maximum

    chroma = value * saturation

    hue_section = hue / 60

    x = chroma * (
        1 - np.abs((hue_section % 2) - 1)
    )

    rgb_prime = np.zeros_like(pixels)

    section = (hue_section >= 0) & (hue_section < 1)
    rgb_prime[section] = np.stack(
        [
            chroma[section],
            x[section],
            np.zeros_like(chroma[section]),
        ],
        axis=-1,
    )

    section = (hue_section >= 1) & (hue_section < 2)
    rgb_prime[section] = np.stack(
        [
            x[section],
            chroma[section],
            np.zeros_like(chroma[section]),
        ],
        axis=-1,
    )

    section = (hue_section >= 2) & (hue_section < 3)
    rgb_prime[section] = np.stack(
        [
            np.zeros_like(chroma[section]),
            chroma[section],
            x[section],
        ],
        axis=-1,
    )

    section = (hue_section >= 3) & (hue_section < 4)
    rgb_prime[section] = np.stack(
        [
            np.zeros_like(chroma[section]),
            x[section],
            chroma[section],
        ],
        axis=-1,
    )

    section = (hue_section >= 4) & (hue_section < 5)
    rgb_prime[section] = np.stack(
        [
            x[section],
            np.zeros_like(chroma[section]),
            chroma[section],
        ],
        axis=-1,
    )

    section = (hue_section >= 5) & (hue_section < 6)
    rgb_prime[section] = np.stack(
        [
            chroma[section],
            np.zeros_like(chroma[section]),
            x[section],
        ],
        axis=-1,
    )

    minimum_value = value - chroma

    pixels = rgb_prime + minimum_value[..., np.newaxis]

    pixels = np.clip(
        pixels * 255,
        0,
        255,
    )

    return Image.fromarray(
        pixels.astype(np.uint8),
        "RGB",
    )