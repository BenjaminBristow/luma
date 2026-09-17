from PIL import Image, ImageEnhance


def apply_saturation(image: Image.Image, amount: int) -> Image.Image:
    """
    Apply a percentage-based saturation adjustment to an image.

    Positive values increase colour intensity.
    Negative values reduce colour intensity.

    Examples:
        20  -> 20% more saturation
        0   -> no change
        -20 -> 20% less saturation
    """

    # Skip the operation entirely when the preset
    # does not request a saturation adjustment.
    if amount == 0:
        return image

    # Pillow uses 1.0 as the original saturation level.
    # Convert our percentage into the multiplier Pillow expects.
    #
    # +20% becomes 1.20
    # -20% becomes 0.80
    factor = 1 + (amount / 100)

    # Create Pillow's colour enhancer.
    enhancer = ImageEnhance.Color(image)

    # Return the adjusted image for the next operation.
    return enhancer.enhance(factor)