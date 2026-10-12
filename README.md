# Luma

**A batch photo editor with creative presets, a desktop interface, and a command-line workflow.**

Luma is an open-source Python photo editor designed to make editing multiple photographs consistent and straightforward. Choose from a collection of themed presets, preview the results, and process entire batches of images without having to edit every photograph individually.

The desktop application combines a modern HTML, CSS, and JavaScript interface with a Python image-processing engine. Luma also provides a command-line interface for users who prefer working in the terminal.

**[Download Luma](https://github.com/BenjaminBristow/luma/releases/latest)** · **[View source code](https://github.com/BenjaminBristow/luma)** · **[Report a bug](https://github.com/BenjaminBristow/luma/issues)**

---

## Download and install

Pre-built desktop releases are available for macOS and Windows on the [GitHub Releases page](https://github.com/BenjaminBristow/luma/releases).

### Windows

1. Open the [latest release](https://github.com/BenjaminBristow/luma/releases/latest).
2. Download `Luma-Windows.zip`.
3. Extract the entire ZIP file.
4. Open the extracted `Luma` folder.
5. Double-click `Luma.exe` to launch the application.

**Important:** Keep `Luma.exe` and its accompanying files together. The executable relies on supporting files included in the extracted folder, so don't move the `.exe` out on its own.

### macOS

1. Open the [latest release](https://github.com/BenjaminBristow/luma/releases/latest).
2. Download `Luma.dmg`.
3. Open the disk image and follow the installation instructions provided with the release.

The release also includes `Luma-macOS.zip` as an alternative archive.

### Python installation

If you prefer to install Luma through Python rather than use a pre-built desktop release, you can install the package with pip:

```bash
pip install luma
```

Launch the graphical interface with:

```bash
luma
```

To update an existing pip installation:

```bash
pip install --upgrade luma
```

---

## Features

* **41 built-in presets** across cinematic, artistic, vintage, nature, atmospheric, and urban styles.
* **Desktop graphical interface** with a modern HTML, CSS, and JavaScript frontend.
* **Drag-and-drop importing** alongside file-picker support.
* **Before-and-after previews** to compare the original photograph with the selected effect.
* **Batch processing** to apply a consistent look across multiple images.
* **Recursive folder processing** for working with larger photo collections.
* **JPEG, PNG, and WebP support.**
* **Custom input and output directories** for organising your workflow.
* **Automatic export folders** to keep edited images organised.
* **Progress reporting and processing-time measurements** during batch operations.
* **Per-image error handling** so an individual failed image doesn't stop the rest of a batch.
* **Command-line interface** for repeatable workflows and terminal-based editing.
* **Reusable image-processing operations** built around Pillow and NumPy.

## How it works

Luma separates the user interface, presets, image-processing logic, and individual editing operations.

```text
        Desktop GUI / CLI
                |
                v
         Selected preset
                |
                v
          Image processor
                |
                v
       Reusable operations
                |
                v
         Exported images
```

A preset combines individual adjustments into a complete visual style. For example, a cinematic look might combine contrast, exposure, colour grading, highlights, shadows, and vignette effects.

The processor applies the selected operations to each image and handles the batch workflow, while individual operation modules contain the image-adjustment logic.

This separation makes it easier to maintain existing presets, add new styles, and reuse operations without duplicating image-processing code.

## Using the desktop interface

The typical workflow is:

1. Import photographs using drag-and-drop or the file picker.
2. Browse the available preset categories.
3. Select a preset to preview its effect.
4. Review the before-and-after comparison.
5. Process the selected batch.
6. Find the edited photographs in the generated export folder.

Luma creates a separate export folder for each batch, helping to keep different edits organised. Existing exports are not intentionally overwritten; when a folder name already exists, Luma creates a numbered alternative.

## Command-line interface

Luma also includes `luma-cli` for users who prefer terminal-based workflows.

### Apply a preset

```bash
luma-cli --cinematic
```

Other examples include:

```bash
luma-cli --aurora
luma-cli --forest
luma-cli --noir
luma-cli --dreamy
```

### Choose input and output directories

```bash
luma-cli --cinematic --input photos --output edited
```

### List available presets

```bash
luma-cli --presets
```

The CLI uses `input/` and `output/` as its default directories when no alternatives are supplied.

## Preset collection

Luma's presets are organised into themed categories.

| Category             | Example presets                                                                                |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| Dark & Cinematic     | `cinematic`, `noir`, `thriller`, `horror`, `dramatic`                                          |
| Artistic             | `dreamy`, `ethereal`, `crimson`, `pastel`, `monochrome`, `bleach`                              |
| Vintage              | `retro`, `old-fashioned`, `sepia`, `antique`, `faded`, `polaroid`, `film`, `70s`, `80s`, `90s` |
| Nature               | `forest`, `overgrown`, `autumn`, `golden-hour`, `moss`, `earthy`, `ocean`, `tropical`          |
| Weather & Atmosphere | `aurora`, `storm`, `mist`, `fog`, `overcast`, `moonlight`, `twilight`                          |
| Urban                | `industrial`, `abandoned`, `grunge`, `concrete`, `urban`                                       |

The collection is designed to provide a range of starting points for different photographic moods, rather than requiring users to configure every adjustment manually.

## Supported image formats

Luma supports the following formats:

* `.jpg`
* `.jpeg`
* `.png`
* `.webp`

## Technology stack

Luma combines Python-based image processing with a web-based desktop interface.

| Technology                | Purpose                                 |
| ------------------------- | --------------------------------------- |
| Python                    | Application logic and processing        |
| Pillow                    | Image loading, manipulation, and export |
| NumPy                     | Efficient per-pixel calculations        |
| HTML, CSS, and JavaScript | Desktop interface                       |
| PyWebView                 | Native application window               |
| pytest                    | Automated testing                       |

## Development

Contributions, bug reports, and suggestions are welcome.

### Requirements

* Python 3.12 or newer
* Git
* A supported desktop environment for running the graphical interface

### Clone the repository

```bash
git clone https://github.com/BenjaminBristow/luma.git
cd luma
```

### Create a virtual environment

macOS and Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install the project in editable mode

```bash
python -m pip install -e .
```

### Run the application

Graphical interface:

```bash
luma
```

Command-line interface:

```bash
luma-cli --cinematic
```

### Run the tests

```bash
python -m pytest
```

Luma's automated tests help verify the image-processing behaviour and reduce regressions as the project develops.

## Releases

Luma uses GitHub Actions to automate testing, application builds, and release publishing.

Version-tagged releases build the desktop applications for macOS and Windows, package the relevant files, and attach the resulting downloads to the GitHub release.

See [all releases](https://github.com/BenjaminBristow/luma/releases) for available versions and downloads.

## Licence

Luma is released under the MIT Licence. See [`LICENSE`](LICENSE) for the full terms.

---

**Built by [Benjamin Bristow](https://github.com/BenjaminBristow).**

If you find Luma useful, consider giving the repository a star or opening an issue with feedback and ideas for future improvements.
