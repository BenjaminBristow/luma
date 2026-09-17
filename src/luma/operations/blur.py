from PIL import Image, ImageFilter


def apply_blur(
    image: Image.Image,
    amount: int,
) -> Image.Image:
    """
    Apply a soft Gaussian blur.

    Positive values increase the amount of blur.

    This can be useful for dreamy, misty and soft photographic styles.
    """

    if amount <= 0:
        return image

    image = image.convert("RGB")

    # Pillow's GaussianBlur uses a radius rather than a percentage,
    # so convert the user-friendly amount into a sensible radius.
    radius = amount / 10

    return image.filter(
        ImageFilter.GaussianBlur(radius=radius)
    )