from PIL import Image, ImageEnhance


def apply_contrast(image: Image.Image, amount: int) -> Image.Image:
    """
    Apply a percentage-based contrast adjustment to an image.

    The amount is expressed as a percentage rather than Pillow's
    multiplier format. This makes preset definitions easier to read.

    Examples:
        20  -> 20% more contrast
        0   -> no change
        -20 -> 20% less contrast
    """

    # There is nothing to do if the preset does not request
    # a contrast adjustment.
    if amount == 0:
        return image

    # Pillow uses 1.0 as the original contrast level.
    # Convert our percentage into Pillow's multiplier format.
    #
    # +20% becomes 1.20
    # -20% becomes 0.80
    factor = 1 + (amount / 100)

    # Create Pillow's contrast enhancer using the current image.
    enhancer = ImageEnhance.Contrast(image)

    # Return the adjusted image so another operation can
    # continue processing it.
    return enhancer.enhance(factor)