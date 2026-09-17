from pathlib import Path

import numpy as np
from PIL import Image

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

    assert not np.array_equal(original_array, processed_array)


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

    settings = {
        "contrast": 20,
    }

    process_directory(
        input_directory,
        output_directory,
        settings,
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


def test_process_directory_handles_permission_error(tmp_path, monkeypatch, capsys):
    """
    A PermissionError while scanning the input directory should not
    crash the application.
    """
    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    def raise_permission_error(self):
        raise PermissionError("Permission denied")

    monkeypatch.setattr(
        Path,
        "iterdir",
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
    A FileNotFoundError while scanning the input directory should be
    handled without crashing.
    """
    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    def raise_file_not_found_error(self):
        raise FileNotFoundError("Directory disappeared")

    monkeypatch.setattr(
        Path,
        "iterdir",
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
    A general filesystem OSError while scanning should be handled
    without crashing.
    """
    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"

    input_directory.mkdir()

    def raise_os_error(self):
        raise OSError("Filesystem error")

    monkeypatch.setattr(
        Path,
        "iterdir",
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
    A filesystem error affecting one entry should not prevent other
    entries from being discovered.
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

    original_iterdir = Path.iterdir

    def custom_iterdir(self):
        if self == input_directory:
            return iter([
                valid_image,
                ProblematicPath(),
            ])

        return original_iterdir(self)

    monkeypatch.setattr(
        Path,
        "iterdir",
        custom_iterdir,
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

