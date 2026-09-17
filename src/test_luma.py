from pathlib import Path

from luma.presets.cinematic import CinematicPreset
from luma.processor import process_directory


# Define the input and output directories.
input_directory = Path("input")
output_directory = Path("output")


# Load the Cinematic preset so we can pass its settings
# into the image processor.
preset = CinematicPreset()


# Process every supported image in the input directory.
process_directory(
    input_directory,
    output_directory,
    preset.settings,
)