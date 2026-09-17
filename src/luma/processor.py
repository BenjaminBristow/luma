import time
from pathlib import Path

from PIL import Image

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

        # Start with the original image.
        edited_image = image

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
    Process every supported image in an input directory.

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

    # Find supported image files directly inside the input directory.
    image_files = []

    try:
        for path in input_directory.iterdir():
            try:
                # Check each entry independently so one inaccessible or broken
                # filesystem entry does not prevent the rest from being processed.
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

    # Tell the user when there is nothing to process.
    if not image_files:
        print("No supported images found in the input directory.")
        return

    # Start timing the batch once we know there are images to process.
    start_time = time.perf_counter()

    successful = 0
    failed = 0

    # Process each image independently.
    for index, input_path in enumerate(image_files, start=1):

        # Calculate the percentage of the batch that has been completed.
        progress = int((index / len(image_files)) * 100)

        output_path = output_directory / input_path.name

        print(
            f"Processing: {input_path.name} "
            f"[{progress}%]"
        )

        try:
            process_image(
                input_path,
                output_path,
                settings,
            )

            successful += 1

        except Exception as error:
            # A single problematic image should not stop the
            # rest of the batch from processing.
            failed += 1

            print(f"  Failed: {error}")

    # Calculate the total processing time.
    elapsed_time = time.perf_counter() - start_time

    print()
    print("Processing complete.")
    print(f"  Successful: {successful}")
    print(f"  Failed:     {failed}")
    print(f"  Time:       {elapsed_time:.2f} seconds")