import argparse
from pathlib import Path
from importlib.metadata import version

from luma.presets import PRESETS
from luma.processor import process_directory


def main():
    """
    Entry point for the Luma command-line interface.

    The CLI is responsible for understanding what the user
    wants to do, while the processor handles the actual
    image processing.
    """

    # Create the command-line argument parser.
    parser = argparse.ArgumentParser(
        description="Luma - command-line image editor"
    )

    # Allow the user to see the version.
    parser.add_argument(
        "--version",
        action="version",
        version=f"Luma {version('luma-image-editor')}",
    )

    # Allow the user to list all available presets.
    parser.add_argument(
        "--presets",
        action="store_true",
        help="List available image presets",
    )

    # Allow the user to override the default input directory.
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("input"),
        help="Input image directory (default: input)",
    )

    # Allow the user to override the default output directory.
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="Output image directory (default: output)",
    )

    # Create a command-line flag for every registered preset.
    #
    # For example:
    #     --cinematic
    #     --vintage
    #     --dramatic
    #
    # The preset registry means we don't have to manually add
    # another argument every time a new preset is created.
    for preset_name in PRESETS:
        parser.add_argument(
            f"--{preset_name}",
            action="store_true",
            help=f"Apply the {preset_name} preset",
        )

    # Read the arguments supplied by the user.
    args = parser.parse_args()

    if args.presets:
        print("Available presets:")
        print()

        # Group presets by their category so the list remains easy
        # to navigate as more presets are added.
        grouped_presets = {}

        for preset_class in PRESETS.values():
            category = preset_class.category

            grouped_presets.setdefault(
                category,
                [],
            ).append(preset_class)

        # Display each category and the presets belonging to it.
        for category, presets in grouped_presets.items():

            print(category)

            for preset in presets:
                print(f"  --{preset.name}")

            print()

        return

    for preset_name, preset_class in PRESETS.items():

        # argparse converts hyphens in option names into underscores
        # when creating Namespace attributes.
        argument_name = preset_name.replace("-", "_")

        if getattr(args, argument_name):

            preset = preset_class()

            print(f"Luma - {preset.name.capitalize()} Preset")
            print()

            # Make sure the input directory exists before attempting
            # to process anything.
            if not args.input.exists():
                print(f"Input directory not found: {args.input}")
                return

            # Process every supported image in the input directory.
            process_directory(
                args.input,
                args.output,
                preset.settings,
            )

            return

    # If the user did not provide a preset, show the normal help.
    parser.print_help()


if __name__ == "__main__":
    main()