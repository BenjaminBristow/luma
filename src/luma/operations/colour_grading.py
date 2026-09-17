import numpy as np
from PIL import Image


# Each colour is represented by the centre of its hue range.
# Hue is measured from 0 to 360 degrees.
HUE_CENTRES = {
    "red": 0,
    "orange": 30,
    "yellow": 60,
    "green": 120,
    "cyan": 180,
    "blue": 240,
    "purple": 280,
    "magenta": 320,
}


def apply_colour_grading(
    image: Image.Image,
    adjustments: dict[str, int],
) -> Image.Image:
    """
    Selectively increase or decrease colour intensity based on hue.

    The adjustments dictionary specifies how strongly each colour
    should be affected.

    Positive values increase saturation in that colour range.
    Negative values decrease saturation.

    The adjustment fades smoothly between colour ranges rather than
    creating harsh boundaries between affected and unaffected pixels.
    """

    if not adjustments:
        return image

    image = image.convert("RGB")

    # Convert RGB values from 0-255 to 0-1.
    # Floating-point values make the colour calculations easier.
    pixels = np.asarray(image, dtype=np.float32) / 255.0

    maximum = pixels.max(axis=2)
    minimum = pixels.min(axis=2)

    difference = maximum - minimum

    # Calculate saturation.
    # Completely grey pixels have no saturation.
    saturation = np.zeros_like(maximum)

    non_zero = difference != 0

    saturation[non_zero] = (
        difference[non_zero] / maximum[non_zero]
    )

    red = pixels[..., 0]
    green = pixels[..., 1]
    blue = pixels[..., 2]

    # Calculate the hue of every pixel.
    hue = np.zeros_like(maximum)

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

    # Apply each requested colour adjustment.
    for colour, amount in adjustments.items():

        if amount == 0:
            continue

        if colour not in HUE_CENTRES:
            continue

        centre = HUE_CENTRES[colour]

        # Find the shortest distance between each pixel's hue
        # and the target colour.
        distance = np.abs(hue - centre)
        distance = np.minimum(distance, 360 - distance)

        # Create a smooth mask.
        # Pixels close to the target colour are affected more strongly.
        mask = np.clip(1 - (distance / 45), 0, 1)

        # Avoid strongly affecting pixels that contain very little colour.
        mask *= saturation

        # Convert the percentage adjustment into a multiplier.
        factor = 1 + (amount / 100)

        saturation *= 1 + ((factor - 1) * mask)

    # Saturation must remain between 0 and 1.
    saturation = np.clip(saturation, 0, 1)

    # Preserve the original brightness/value of each pixel.
    value = maximum

    # Convert the adjusted HSV-style representation back into RGB.
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

    # Convert back from 0-1 to 0-255 and create a Pillow image.
    pixels = np.clip(pixels * 255, 0, 255)

    return Image.fromarray(
        pixels.astype(np.uint8),
        "RGB",
    )