# Luma

Luma is a Python batch photo editor with a modern graphical interface and command-line interface.

It allows multiple photographs to be edited consistently using a collection of themed presets and reusable image-processing operations.

The GUI is designed to make Luma accessible to normal users without requiring knowledge of the command line.

## Features

* Modern graphical interface
* Drag-and-drop photo importing
* Before and after image previews
* 41 built-in presets
* Presets organised into themed categories
* Batch processing of multiple photographs
* Recursive folder processing
* JPEG, PNG and WebP support
* Custom input and output directories
* Automatic export folders
* Progress reporting during batch processing
* Processing time measurement
* Per-image error handling
* Reusable image-processing operations
* NumPy-powered image processing
* Command-line interface for advanced users

## Installation

Luma can be installed from PyPI using pip:

```bash
pip install luma
```

After installation, launch the graphical interface with:

```bash
luma
```

To update an existing installation:

```bash
pip install --upgrade luma
```

## Graphical Interface

The Luma GUI provides a simple workflow for editing photographs.

```text
Add photos
    ↓
Choose a theme
    ↓
Choose a preset
    ↓
Preview the result
    ↓
Edit photos
    ↓
Export edited photos
```

Photos can be added using the file picker or by dragging them directly into Luma.

The first added photograph is used as the example image for the before and after preview.

Changing the selected preset generates a new preview without processing the entire batch.

## Command-Line Interface

Luma also provides a command-line interface for users who prefer working from the terminal.

The CLI can be launched using:

```bash
luma-cli
```

### Apply a preset

```bash
luma-cli --cinematic
```

```bash
luma-cli --aurora
```

```bash
luma-cli --forest
```

```bash
luma-cli --noir
```

```bash
luma-cli --dreamy
```

### Custom input and output directories

Luma uses `input/` and `output/` by default, but both directories can be changed.

```bash
luma-cli --cinematic --input photos --output edited
```

### List available presets

```bash
luma-cli --presets
```

This displays the available presets grouped by category.

## Presets

Luma currently includes 41 built-in presets organised into themed categories.

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

## How Luma Works

Luma separates image processing into several layers.

```text
GUI / CLI
    ↓
Preset
    ↓
Processor
    ↓
Operations
    ↓
Output Image
```

### Presets

Presets define **what** changes should be made to an image.

For example, the `aurora` preset combines multiple adjustments including:

* Contrast
* Saturation
* Highlights
* Shadows
* Warmth
* Exposure
* Vignette
* Sharpening
* Colour grading

### Processor

The processor controls the order in which image operations are applied and handles batch processing.

Each image is processed independently so that a failure with one image does not stop the rest of the batch.

### Operations

Individual operation modules define **how** an adjustment is performed.

Luma currently includes operations for:

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

This separation makes it possible to create and modify presets without rewriting the underlying image-processing logic.

## Supported Images

Luma currently supports:

* `.jpg`
* `.jpeg`
* `.png`
* `.webp`

## Exporting

The GUI automatically creates a separate export folder for each batch.

Folders use the following format:

```text
<number>_<preset>_images_<HH-MM>_<DD-MM-YY>
```

For example:

```text
12_cinematic_images_01-23_21-09-26
```

Existing exports are never overwritten. If the same folder name already exists, Luma automatically creates a numbered version.

## Error Handling

Luma is designed to continue processing when individual files cannot be accessed or processed.

Filesystem errors such as inaccessible files, missing files and permission errors are handled without terminating the entire batch.

When an individual image fails, Luma reports the error and continues processing the remaining images.

## Performance

Image processing uses NumPy for operations that require per-pixel calculations.

This allows image arrays to be processed using vectorised operations rather than slow Python-level pixel processing.

Batch processing also measures the total processing time.

Example:

```text
Processing complete.
  Successful: 7
  Failed:     0
  Time:       12.29 seconds
```

## Technologies

* Python
* Pillow
* NumPy
* CustomTkinter
* tkinterdnd2
* tqdm
* setuptools
* pytest

## Development

Luma is developed as a portfolio project with an emphasis on:

* Clean project structure
* Separation of concerns
* Reusable components
* Maintainable Python code
* Performance
* Error handling
* Automated testing
* User-friendly application design

### Clone the repository

```bash
git clone https://github.com/BenjaminBristow/luma.git
cd luma
```

### Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

### Install in editable mode

```bash
pip install -e .
```

### Run the GUI

```bash
luma
```

### Run the CLI

```bash
luma-cli --cinematic
```

### Run the tests

```bash
pytest
```

## Project Structure

```text
luma/
├── input/
├── output/
├── src/
│   └── luma/
│       ├── __init__.py
│       ├── cli.py
│       ├── gui.py
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
│           ├── retro.py
│           ├── forest.py
│           ├── ocean.py
│           ├── noir.py
│           └── ...
│
├── tests/
├── .gitignore
├── pyproject.toml
└── README.md
```

## Licence

This project is currently developed as an educational and portfolio project.
