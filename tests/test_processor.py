from pathlib import Path

import numpy as np

from PIL import Image, ImageOps

from luma.processor import process_directory, process_image


def create_test_image(path: Path) -> None:
    """Create a small RGB image for testing."""

    image = Image.new("RGB", (4, 4), (100, 150, 200))
    image.save(path)


def assert_valid_image(path: Path) -> None:
    """Check that a processed file is a valid RGB image."""

    with Image.open(path) as image:
        assert image.mode == "RGB"
        assert image.size == (4, 4)


def test_process_image_creates_output(tmp_path):
    """A single image should be processed and saved."""

    input_path = tmp_path / "input.jpg"
    output_path = tmp_path / "output.jpg"

    create_test_image(input_path)

    settings = {
        "contrast": 20,
        "saturation": 10,
    }

    process_image(input_path, output_path, settings)

    assert output_path.exists()


def test_process_image_creates_valid_image(tmp_path):
    """The processed image should remain a valid RGB image."""

    input_path = tmp_path / "input.jpg"
    output_path = tmp_path / "output.jpg"

    create_test_image(input_path)

    settings = {
        "contrast": 20,
    }

    process_image(input_path, output_path, settings)

    assert_valid_image(output_path)


def test_process_image_preserves_dimensions(tmp_path):
    """Processing should not change the image dimensions."""

    input_path = tmp_path / "input.jpg"
    output_path = tmp_path / "output.jpg"

    create_test_image(input_path)

    settings = {
        "saturation": 20,
        "warmth": 10,
    }

    process_image(input_path, output_path, settings)

    with Image.open(output_path) as image:
        assert image.size == (4, 4)


def test_process_image_changes_image(tmp_path):
    """A non-zero adjustment should change the image."""

    input_path = tmp_path / "input.png"
    output_path = tmp_path / "output.png"

    create_test_image(input_path)

    settings = {
        "contrast": 50,
    }

    process_image(input_path, output_path, settings)

    with Image.open(input_path) as original:
        original_array = np.array(original)

    with Image.open(output_path) as processed:
        processed_array = np.array(processed)

    assert not np.array_equal(
        original_array,
        processed_array,
    )


def test_process_image_applies_exif_orientation(tmp_path):
    """EXIF orientation should be applied to portrait images."""

    input_path = tmp_path / "portrait.jpg"
    output_path = tmp_path / "output.jpg"

    # Create a rectangular image so rotation changes its dimensions.
    image = Image.new("RGB", (4, 6), (100, 150, 200))

    # EXIF orientation 6 means the image should be rotated 90 degrees.
    exif = image.getexif()
    exif[274] = 6
    image.save(input_path, exif=exif)

    process_image(
        input_path,
        output_path,
        {},
    )

    with Image.open(output_path) as processed:
        assert processed.size == (6, 4)


def test_process_directory_processes_multiple_images(tmp_path):
    """Every supported image in a directory should be processed."""

    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    create_test_image(input_directory / "image1.png")
    create_test_image(input_directory / "image2.png")
    create_test_image(input_directory / "image3.png")

    settings = {
        "contrast": 20,
    }

    process_directory(
        input_directory,
        output_directory,
        settings,
    )

    assert (output_directory / "image1.png").exists()
    assert (output_directory / "image2.png").exists()
    assert (output_directory / "image3.png").exists()


def test_process_directory_ignores_unsupported_files(tmp_path):
    """Unsupported files should not be processed."""

    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    create_test_image(input_directory / "image.png")

    (input_directory / "notes.txt").write_text(
        "This should not be processed."
    )

    process_directory(
        input_directory,
        output_directory,
        {},
    )

    assert (output_directory / "image.png").exists()
    assert not (output_directory / "notes.txt").exists()


def test_process_directory_handles_empty_directory(tmp_path, capsys):
    """An empty input directory should be handled cleanly."""

    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    process_directory(
        input_directory,
        output_directory,
        {},
    )

    captured = capsys.readouterr()

    assert "No supported images found" in captured.out


def test_process_directory_creates_output_directory(tmp_path):
    """The output directory should be created automatically."""

    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    create_test_image(input_directory / "image.png")

    process_directory(
        input_directory,
        output_directory,
        {},
    )

    assert output_directory.exists()
    assert output_directory.is_dir()


def test_process_directory_continues_after_invalid_image(tmp_path):
    """A broken image should not prevent valid images from being processed."""

    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    create_test_image(input_directory / "valid.png")

    # Give the file an image extension but deliberately make it invalid.
    (input_directory / "broken.png").write_text(
        "This is not a real image."
    )

    process_directory(
        input_directory,
        output_directory,
        {},
    )

    assert (output_directory / "valid.png").exists()
    assert not (output_directory / "broken.png").exists()


def test_process_directory_processes_nested_images(tmp_path):
    """Images inside nested folders should also be processed."""

    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    holiday_directory = input_directory / "holiday"
    family_directory = input_directory / "family"

    holiday_directory.mkdir(parents=True)
    family_directory.mkdir(parents=True)

    create_test_image(holiday_directory / "beach.png")
    create_test_image(family_directory / "dinner.png")
    create_test_image(input_directory / "random.png")

    process_directory(
        input_directory,
        output_directory,
        {},
    )

    assert (output_directory / "random.png").exists()
    assert (output_directory / "holiday" / "beach.png").exists()
    assert (output_directory / "family" / "dinner.png").exists()


def test_process_directory_preserves_nested_structure(tmp_path):
    """Nested input folders should be recreated in the output directory."""

    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    nested_directory = (
        input_directory
        / "holiday"
        / "2026"
        / "st_lucia"
    )

    nested_directory.mkdir(parents=True)

    create_test_image(
        nested_directory / "sunset.png"
    )

    process_directory(
        input_directory,
        output_directory,
        {},
    )

    expected_output = (
        output_directory
        / "holiday"
        / "2026"
        / "st_lucia"
        / "sunset.png"
    )

    assert expected_output.exists()


def test_process_directory_handles_permission_error(
    tmp_path,
    monkeypatch,
    capsys,
):
    """
    A PermissionError while recursively scanning the input directory
    should not crash the application.
    """

    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    def raise_permission_error(self, pattern):
        raise PermissionError("Permission denied")

    monkeypatch.setattr(
        Path,
        "rglob",
        raise_permission_error,
    )

    process_directory(
        input_directory,
        output_directory,
        {},
    )

    captured = capsys.readouterr()

    assert "Unable to access input directory" in captured.out
    assert "Permission denied" in captured.out


def test_process_directory_handles_file_not_found_error(
    tmp_path,
    monkeypatch,
    capsys,
):
    """
    A FileNotFoundError while recursively scanning the input directory
    should be handled without crashing.
    """

    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    def raise_file_not_found_error(self, pattern):
        raise FileNotFoundError("Directory disappeared")

    monkeypatch.setattr(
        Path,
        "rglob",
        raise_file_not_found_error,
    )

    process_directory(
        input_directory,
        output_directory,
        {},
    )

    captured = capsys.readouterr()

    assert "Unable to access input directory" in captured.out
    assert "Directory disappeared" in captured.out


def test_process_directory_handles_os_error(
    tmp_path,
    monkeypatch,
    capsys,
):
    """
    A general filesystem OSError while recursively scanning should
    be handled without crashing.
    """

    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    def raise_os_error(self, pattern):
        raise OSError("Filesystem error")

    monkeypatch.setattr(
        Path,
        "rglob",
        raise_os_error,
    )

    process_directory(
        input_directory,
        output_directory,
        {},
    )

    captured = capsys.readouterr()

    assert "Unable to access input directory" in captured.out
    assert "Filesystem error" in captured.out


def test_process_directory_skips_problematic_entry(
    tmp_path,
    monkeypatch,
    capsys,
):
    """
    A filesystem error affecting one discovered entry should not
    prevent other entries from being processed.
    """

    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    valid_image = input_directory / "valid.png"

    create_test_image(valid_image)

    problematic_entry = input_directory / "problematic.png"

    class ProblematicPath:
        suffix = ".png"

        def is_file(self):
            raise PermissionError("Access denied")

        def __str__(self):
            return str(problematic_entry)

    def custom_rglob(self, pattern):
        if self == input_directory:
            return iter([
                valid_image,
                ProblematicPath(),
            ])

        return iter(())

    monkeypatch.setattr(
        Path,
        "rglob",
        custom_rglob,
    )

    process_directory(
        input_directory,
        output_directory,
        {},
    )

    captured = capsys.readouterr()

    assert (output_directory / "valid.png").exists()
    assert "Skipping" in captured.out
    assert "Access denied" in captured.out