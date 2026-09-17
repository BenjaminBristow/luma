import numpy as np
import pytest
from PIL import Image

from luma.operations.blur import apply_blur
from luma.operations.colour_grading import apply_colour_grading
from luma.operations.contrast import apply_contrast
from luma.operations.exposure import apply_exposure
from luma.operations.fade import apply_fade
from luma.operations.grain import apply_grain
from luma.operations.highlights import apply_highlights
from luma.operations.hue_shift import apply_hue_shift
from luma.operations.saturation import apply_saturation
from luma.operations.sepia import apply_sepia
from luma.operations.shadows import apply_shadows
from luma.operations.sharpen import apply_sharpen
from luma.operations.vignette import apply_vignette
from luma.operations.warmth import apply_warmth


@pytest.fixture
def test_image():
    """
    Create a small test image in memory.

    Using an in-memory image keeps the operation tests fast and
    means they do not depend on files stored on the user's computer.
    """

    pixels = np.array(
        [
            [
                [255, 0, 0],
                [0, 255, 0],
                [0, 0, 255],
            ],
            [
                [255, 255, 0],
                [255, 128, 0],
                [128, 0, 255],
            ],
            [
                [50, 50, 50],
                [128, 128, 128],
                [220, 220, 220],
            ],
        ],
        dtype=np.uint8,
    )

    return Image.fromarray(pixels, "RGB")


def assert_valid_image(image):
    """Check that an operation returned a valid RGB Pillow image."""

    assert isinstance(image, Image.Image)
    assert image.mode == "RGB"
    assert image.size == (3, 3)


def test_contrast_changes_image(test_image):
    result = apply_contrast(test_image, 50)

    assert_valid_image(result)
    assert not np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


def test_saturation_changes_image(test_image):
    result = apply_saturation(test_image, 50)

    assert_valid_image(result)
    assert not np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


def test_highlights_changes_image(test_image):
    result = apply_highlights(test_image, 30)

    assert_valid_image(result)
    assert not np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


def test_shadows_changes_image(test_image):
    result = apply_shadows(test_image, 30)

    assert_valid_image(result)
    assert not np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


def test_warmth_changes_image(test_image):
    result = apply_warmth(test_image, 20)

    assert_valid_image(result)
    assert not np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


def test_vignette_changes_image(test_image):
    result = apply_vignette(test_image, 30)

    assert_valid_image(result)
    assert not np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


def test_colour_grading_changes_image(test_image):
    result = apply_colour_grading(
        test_image,
        {
            "red": 30,
            "blue": 20,
        },
    )

    assert_valid_image(result)
    assert not np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


def test_fade_changes_image(test_image):
    result = apply_fade(test_image, 30)

    assert_valid_image(result)
    assert not np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


def test_exposure_changes_image(test_image):
    result = apply_exposure(test_image, 30)

    assert_valid_image(result)
    assert not np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


def test_hue_shift_changes_image(test_image):
    result = apply_hue_shift(test_image, 30)

    assert_valid_image(result)
    assert not np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


def test_grain_changes_image(test_image):
    result = apply_grain(test_image, 30)

    assert_valid_image(result)
    assert not np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


def test_sepia_changes_image(test_image):
    result = apply_sepia(test_image, 80)

    assert_valid_image(result)
    assert not np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


def test_blur_changes_image(test_image):
    result = apply_blur(test_image, 20)

    assert_valid_image(result)
    assert not np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


def test_sharpen_changes_image(test_image):
    result = apply_sharpen(test_image, 50)

    assert_valid_image(result)
    assert not np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


def test_zero_amount_returns_original_image(test_image):
    """
    Every operation should leave the image unchanged when its
    adjustment amount is zero.
    """

    operations = [
        lambda image: apply_contrast(image, 0),
        lambda image: apply_saturation(image, 0),
        lambda image: apply_highlights(image, 0),
        lambda image: apply_shadows(image, 0),
        lambda image: apply_warmth(image, 0),
        lambda image: apply_vignette(image, 0),
        lambda image: apply_fade(image, 0),
        lambda image: apply_exposure(image, 0),
        lambda image: apply_hue_shift(image, 0),
        lambda image: apply_grain(image, 0),
        lambda image: apply_sepia(image, 0),
        lambda image: apply_blur(image, 0),
        lambda image: apply_sharpen(image, 0),
    ]

    original = np.asarray(test_image)

    for operation in operations:
        result = operation(test_image)

        assert np.array_equal(
            original,
            np.asarray(result),
        )


def test_colour_grading_with_no_adjustments_returns_original(test_image):
    result = apply_colour_grading(
        test_image,
        {},
    )

    assert np.array_equal(
        np.asarray(test_image),
        np.asarray(result),
    )


@pytest.mark.parametrize(
    "amount",
    [-100, -50, 0, 50, 100],
)
def test_contrast_handles_valid_amounts(test_image, amount):
    result = apply_contrast(test_image, amount)

    assert_valid_image(result)


@pytest.mark.parametrize(
    "amount",
    [-100, -50, 0, 50, 100],
)
def test_saturation_handles_valid_amounts(test_image, amount):
    result = apply_saturation(test_image, amount)

    assert_valid_image(result)