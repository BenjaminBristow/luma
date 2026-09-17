# Photo-Editor
A place to automatically edit all your photos for you 

# Luma

Luma is a command-line batch image editor built with Python.

It applies reusable image-processing operations through a collection of themed presets, allowing multiple photographs to be edited consistently from the terminal.

## Features

* Batch process multiple images
* 30+ built-in image presets
* Themed preset categories
* Custom input and output directories
* JPEG, PNG and WebP support
* NumPy-powered image processing for improved performance
* Individual reusable image-processing operations
* Progress reporting during batch processing
* Processing time measurement
* Per-image error handling so one failed image does not stop the batch
* Installable command-line interface

## Preset Categories

### Dark & Cinematic

* `cinematic`
* `noir`
* `thriller`
* `horror`
* `dramatic`

### Artistic

* `dreamy`
* `ethereal`
* `crimson`
* `pastel`
* `monochrome`
* `bleach`

### Vintage

* `retro`
* `old-fashioned`
* `sepia`
* `antique`
* `faded`
* `polaroid`
* `film`
* `70s`
* `80s`
* `90s`

### Nature

* `forest`
* `overgrown`
* `autumn`
* `golden-hour`
* `moss`
* `earthy`
* `ocean`
* `tropical`

### Weather & Atmosphere

* `aurora`
* `storm`
* `mist`
* `fog`
* `overcast`
* `moonlight`
* `twilight`

### Urban

* `industrial`
* `abandoned`
* `grunge`
* `concrete`
* `urban`

## How It Works

Luma separates the application into several layers.

```text
CLI
 ↓
Preset
 ↓
Processor
 ↓
Operations
 ↓
Output Image
```

### CLI

The command-line interface handles user input and determines which preset should be used.

### Presets

Presets define **what** changes should be made to an image.

For example, the `aurora` preset combines adjustments to:

* Contrast
* Saturation
* Highlights
* Shadows
* Warmth
* Exposure
* Vignette
* Sharpness
* Individual colour ranges

### Processor

The processor controls the order in which image operations are applied and handles batch processing.

### Operations

Individual operations handle **how** an adjustment is performed.

Examples include:

* Contrast
* Saturation
* Highlights
* Shadows
* Warmth
* Exposure
* Hue shifting
* Colour grading
* Fade
* Sepia
* Grain
* Blur
* Sharpen
* Vignette

This separation makes it possible to create new presets without rewriting the underlying image-processing logic.

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd luma
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install Luma in editable mode:

```bash
pip install -e .
```

## Usage

Place images inside the `input/` directory.

Then run a preset:

```bash
luma --cinematic
```

Processed images will be placed in:

```text
output/
```

### Using a Different Preset

```bash
luma --aurora
```

```bash
luma --forest
```

```bash
luma --noir
```

```bash
luma --dreamy
```

### Custom Input and Output Directories

Luma uses `input/` and `output/` by default, but both directories can be changed.

```bash
luma --cinematic --input photos --output edited
```

### List Available Presets

```bash
luma --presets
```

This displays the available presets grouped by category.

## Supported Images

Luma currently supports:

* `.jpg`
* `.jpeg`
* `.png`
* `.webp`

## Project Structure

```text
luma/
├── input/
├── output/
├── src/
│   ├── test_luma.py
│   └── luma/
│       ├── __init__.py
│       ├── cli.py
│       ├── processor.py
│       │
│       ├── operations/
│       │   ├── contrast.py
│       │   ├── saturation.py
│       │   ├── highlights.py
│       │   ├── shadows.py
│       │   ├── warmth.py
│       │   ├── vignette.py
│       │   ├── colour_grading.py
│       │   ├── fade.py
│       │   ├── exposure.py
│       │   ├── hue_shift.py
│       │   ├── grain.py
│       │   ├── sepia.py
│       │   ├── blur.py
│       │   └── sharpen.py
│       │
│       └── presets/
│           ├── base.py
│           ├── cinematic.py
│           ├── aurora.py
│           ├── ...
│           └── urban.py
│
├── .gitignore
├── pyproject.toml
└── README.md
```

## Performance

Image processing uses NumPy for operations that require per-pixel calculations.

This allows large image arrays to be processed using vectorised operations rather than slow Python-level pixel-by-pixel loops.

Batch processing also measures the total processing time and reports successful and failed images.

Example:

```text
Processing: IMG_7965.jpeg [14%]
Processing: IMG_7914.jpeg [28%]
Processing: IMG_7900.jpeg [42%]

Processing complete.
  Successful: 7
  Failed:     0
  Time:       12.29 seconds
```

## Error Handling

Each image is processed independently.

If an individual image cannot be processed, Luma reports the error and continues processing the remaining images rather than terminating the entire batch.

## Technologies

* Python
* Pillow
* NumPy
* argparse
* pathlib
* setuptools

## Development

Luma is being developed as a portfolio project with an emphasis on:

* Clean project structure
* Reusable components
* Separation of concerns
* Performance
* Error handling
* Command-line application design
* Maintainable Python code

## Future Development

Planned improvements include:

* Comprehensive pytest test suite
* More robust filesystem traversal
* Improved handling of filesystem errors
* More detailed preset information
* Improved CLI output
* Additional image operations
* Further preset tuning
* Packaging and distribution improvements

## Licence

This project is currently for educational and portfolio purposes.
