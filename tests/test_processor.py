from pathlib import Path

import numpy as np
from PIL import Image

from luma.presets.cinematic import CinematicPreset
from luma.processor import process_directory, process_image


def create_test_image(path: Path):
    """
    Create a small JPEG image for processor tests.

    The image is deliberately generated during the test so that
    the test suite does not depend on personal photographs.
    """

    pixels = np.array(
        [
            [
                [255, 0, 0],
                [0, 255, 0],
                [0, 0, 255],
                [255, 255, 0],
            ],
            [
                [255, 128, 0],
                [128, 0, 255],
                [50, 50, 50],
                [220, 220, 220],
            ],
            [
                [20, 40, 80],
                [80, 120, 160],
                [180, 120, 60],
                [100, 50, 30],
            ],
            [
                [255, 255, 255],
                [0, 0, 0],
                [120, 120, 120],
                [200, 200, 200],
            ],
        ],
        dtype=np.uint8,
    )

    image = Image.fromarray(pixels, "RGB")

    image.save(path)


def test_process_image_creates_output(tmp_path):
    input_path = tmp_path / "input.jpg"
    output_path = tmp_path / "output.jpg"

    create_test_image(input_path)

    preset = CinematicPreset()

    process_image(
        input_path,
        output_path,
        preset.settings,
    )

    assert output_path.exists()


def test_process_image_creates_valid_image(tmp_path):
    input_path = tmp_path / "input.jpg"
    output_path = tmp_path / "output.jpg"

    create_test_image(input_path)

    preset = CinematicPreset()

    process_image(
        input_path,
        output_path,
        preset.settings,
    )

    with Image.open(output_path) as image:
        assert image.mode == "RGB"
        assert image.size == (4, 4)


def test_process_image_changes_image(tmp_path):
    input_path = tmp_path / "input.jpg"
    output_path = tmp_path / "output.jpg"

    create_test_image(input_path)

    original = np.asarray(
        Image.open(input_path).convert("RGB")
    )

    preset = CinematicPreset()

    process_image(
        input_path,
        output_path,
        preset.settings,
    )

    edited = np.asarray(
        Image.open(output_path).convert("RGB")
    )

    assert not np.array_equal(
        original,
        edited,
    )


def test_process_directory_processes_multiple_images(tmp_path):
    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    create_test_image(
        input_directory / "first.jpg"
    )

    create_test_image(
        input_directory / "second.jpg"
    )

    preset = CinematicPreset()

    process_directory(
        input_directory,
        output_directory,
        preset.settings,
    )

    assert output_directory.exists()
    assert (output_directory / "first.jpg").exists()
    assert (output_directory / "second.jpg").exists()


def test_process_directory_ignores_unsupported_files(tmp_path):
    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    create_test_image(
        input_directory / "photo.jpg"
    )

    (input_directory / "notes.txt").write_text(
        "This is not an image."
    )

    preset = CinematicPreset()

    process_directory(
        input_directory,
        output_directory,
        preset.settings,
    )

    assert (output_directory / "photo.jpg").exists()
    assert not (output_directory / "notes.txt").exists()


def test_process_directory_handles_empty_directory(tmp_path, capsys):
    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    preset = CinematicPreset()

    process_directory(
        input_directory,
        output_directory,
        preset.settings,
    )

    captured = capsys.readouterr()

    assert "No supported images found" in captured.out


def test_process_directory_creates_output_directory(tmp_path):
    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    create_test_image(
        input_directory / "photo.jpg"
    )

    preset = CinematicPreset()

    process_directory(
        input_directory,
        output_directory,
        preset.settings,
    )

    assert output_directory.exists()


def test_process_directory_continues_after_failed_image(
    tmp_path,
):
    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    # Create one valid image.
    create_test_image(
        input_directory / "valid.jpg"
    )

    # Create a file with an image extension but invalid contents.
    (input_directory / "broken.jpg").write_text(
        "This is not a valid JPEG image."
    )

    preset = CinematicPreset()

    process_directory(
        input_directory,
        output_directory,
        preset.settings,
    )

    # The valid image should still have been processed even though
    # the other image failed.
    assert (output_directory / "valid.jpg").exists()