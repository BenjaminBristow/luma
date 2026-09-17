from PIL import Image, ImageEnhance


def apply_sharpen(
    image: Image.Image,
    amount: int,
) -> Image.Image:
    """
    Increase image sharpness.

    Positive values make edges and fine details more pronounced.
    """

    if amount <= 0:
        return image

    image = image.convert("RGB")

    # Convert the percentage into Pillow's sharpness multiplier.
    factor = 1 + (amount / 100)

    enhancer = ImageEnhance.Sharpness(image)

    return enhancer.enhance(factor)