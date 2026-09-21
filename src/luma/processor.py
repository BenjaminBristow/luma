import time
from pathlib import Path

from PIL import Image, ImageOps

from tqdm import tqdm

from luma.operations.contrast import apply_contrast
from luma.operations.saturation import apply_saturation
from luma.operations.colour_grading import apply_colour_grading
from luma.operations.highlights import apply_highlights
from luma.operations.shadows import apply_shadows
from luma.operations.warmth import apply_warmth
from luma.operations.vignette import apply_vignette
from luma.operations.fade import apply_fade
from luma.operations.exposure import apply_exposure
from luma.operations.hue_shift import apply_hue_shift
from luma.operations.grain import apply_grain
from luma.operations.sepia import apply_sepia
from luma.operations.blur import apply_blur
from luma.operations.sharpen import apply_sharpen


def process_image(
    input_path: Path,
    output_path: Path,
    settings: dict,
) -> None:
    """
    Process a single image using the settings supplied by a preset.

    The processor controls the order in which image operations are
    applied, while each operation module handles one specific type
    of image adjustment.

    Operations with no setting are skipped automatically by using
    a default value of zero.
    """

    # Open the source image. The context manager automatically closes
    # the image file once processing has finished.
    with Image.open(input_path) as image:
    # Apply the camera's EXIF orientation so portrait photos
    # are physically rotated correctly before editing.
        edited_image = ImageOps.exif_transpose(image)

        # Basic tonal and colour adjustments.
        edited_image = apply_contrast(
            edited_image,
            settings.get("contrast", 0),
        )

        edited_image = apply_saturation(
            edited_image,
            settings.get("saturation", 0),
        )

        # Selectively adjust individual colour ranges such as
        # reds, oranges, blues and purples.
        edited_image = apply_colour_grading(
            edited_image,
            settings.get("colour_grading", {}),
        )

        # Adjust brighter and darker parts of the image separately.
        edited_image = apply_highlights(
            edited_image,
            settings.get("highlights", 0),
        )

        edited_image = apply_shadows(
            edited_image,
            settings.get("shadows", 0),
        )

        # Adjust overall colour temperature.
        edited_image = apply_warmth(
            edited_image,
            settings.get("warmth", 0),
        )

        # Change the overall exposure.
        edited_image = apply_exposure(
            edited_image,
            settings.get("exposure", 0),
        )

        # Shift the hue of the image when requested.
        edited_image = apply_hue_shift(
            edited_image,
            settings.get("hue_shift", 0),
        )

        # Apply faded and aged effects.
        edited_image = apply_fade(
            edited_image,
            settings.get("fade", 0),
        )

        edited_image = apply_sepia(
            edited_image,
            settings.get("sepia", 0),
        )

        # Apply detail and texture effects.
        edited_image = apply_blur(
            edited_image,
            settings.get("blur", 0),
        )

        edited_image = apply_sharpen(
            edited_image,
            settings.get("sharpen", 0),
        )

        edited_image = apply_grain(
            edited_image,
            settings.get("grain", 0),
        )

        # Vignette is deliberately near the end so that it affects
        # the finished image rather than an intermediate stage.
        edited_image = apply_vignette(
            edited_image,
            settings.get("vignette", 0),
        )

        # Save the final processed image.
        edited_image.save(output_path)


def process_directory(
    input_directory: Path,
    output_directory: Path,
    settings: dict,
) -> None:
    """
    Recursively process supported images in an input directory.

    The relative folder structure inside the input directory is
    preserved inside the output directory.

    For example:

        input/holiday/beach.jpg
        -> output/holiday/beach.jpg

    Each image is processed independently. If one image fails,
    the remaining images continue processing.
    """

    # Create the output directory if it does not already exist.
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    # These are the image formats currently supported by Luma.
    supported_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    image_files = []

    try:
        # rglob("*") recursively searches through the entire directory
        # tree instead of only looking at files immediately inside it.
        for path in input_directory.rglob("*"):
            try:
                if (
                    path.is_file()
                    and path.suffix.lower() in supported_extensions
                ):
                    image_files.append(path)

            except (PermissionError, FileNotFoundError, OSError) as error:
                print(f"Skipping '{path}': {error}")

    except (PermissionError, FileNotFoundError, OSError) as error:
        print(f"Unable to access input directory: {error}")
        return

    if not image_files:
        print("No supported images found in the input directory.")
        return

    start_time = time.perf_counter()

    successful = 0
    failed = 0

    with tqdm(
        image_files,
        desc="Processing images",
        unit="image",
    ) as progress_bar:

        for input_path in progress_bar:
            relative_path = input_path.relative_to(input_directory)

            output_path = output_directory / relative_path

            # Nested folders need to be created before the image
            # can be saved into the matching output location.
            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            progress_bar.set_postfix(
                file=str(relative_path),
            )

            try:
                process_image(
                    input_path,
                    output_path,
                    settings,
                )

                successful += 1

            except Exception as error:
                failed += 1
                tqdm.write(
                    f"Failed: {relative_path}: {error}"
                )

    elapsed_time = time.perf_counter() - start_time

    print()
    print("Processing complete.")
    print(f"  Successful: {successful}")
    print(f"  Failed:     {failed}")
    print(f"  Time:       {elapsed_time:.2f} seconds")