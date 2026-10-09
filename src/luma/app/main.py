from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
from datetime import datetime
from pathlib import Path

import webview
from PIL import Image, ImageOps

from luma.presets import PRESETS
from luma.processor import process_image


SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def get_pictures_folder() -> Path:
    home = Path.home()

    if sys.platform == "win32":
        pictures = (
            Path(os.environ.get("USERPROFILE", str(home)))
            / "Pictures"
        )
    else:
        pictures = home / "Pictures"

    return pictures if pictures.exists() else home


def get_settings_folder() -> Path:
    home = Path.home()

    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA")

        return (
            Path(app_data) / "Luma"
            if app_data
            else home / "AppData" / "Roaming" / "Luma"
        )

    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "Luma"

    return home / ".config" / "luma"


def display_name(name: str) -> str:
    return (
        name
        .replace("-", " ")
        .replace("_", " ")
        .title()
    )


def get_preset_by_name(name: str):
    for preset in PRESETS.values():
        if preset.name == name:
            return preset

    return None


class LumaAPI:

    def __init__(self):
        self.window = None

        pictures = get_pictures_folder()

        self.luma_root = pictures / "Luma"

        self.default_input_folder = (
            self.luma_root / "Luma_Input"
        )

        self.output_folder = (
            self.luma_root / "Luma_Output"
        )

        self.default_input_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.input_folder = self._load_saved_input_folder()

        if not self.input_folder.exists():
            self.input_folder = self.default_input_folder

            self.input_folder.mkdir(
                parents=True,
                exist_ok=True,
            )

        self.photo_paths: list[Path] = []

        self.selected_photo_index = 0

        self.selected_preset_name: str | None = None

        self.last_output_folder: Path | None = None

        self.processing = False

        self.processing_status = {
            "processing": False,
            "progress": 0.0,
            "current": 0,
            "total": 0,
            "status": "Ready",
            "successful": 0,
            "failed": 0,
            "output_folder": None,
        }

        self.preview_directory = Path(
            tempfile.mkdtemp(prefix="luma_preview_")
        )

        self.preview_token = 0

    # ---------------------------------------------------------
    # Settings
    # ---------------------------------------------------------

    @property
    def settings_file(self) -> Path:
        return (
            get_settings_folder()
            / "settings.json"
        )

    def _load_saved_input_folder(self) -> Path:

        try:
            if not self.settings_file.exists():
                return self.default_input_folder

            with self.settings_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                settings = json.load(file)

            saved_folder = settings.get("input_folder")

            if saved_folder:
                return Path(saved_folder).expanduser()

        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
        ):
            pass

        return self.default_input_folder

    def _save_input_folder(self):

        try:
            self.settings_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with self.settings_file.open(
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    {
                        "input_folder": str(
                            self.input_folder
                        )
                    },
                    file,
                    indent=4,
                )

        except OSError:
            pass

    # ---------------------------------------------------------
    # File helpers
    # ---------------------------------------------------------

    def _find_images_in_folder(
        self,
        folder: Path,
    ) -> list[Path]:

        if not folder.exists():
            return []

        return sorted(
            path
            for path in folder.rglob("*")
            if (
                path.is_file()
                and path.suffix.lower()
                in SUPPORTED_EXTENSIONS
            )
        )

    def _image_to_uri(self, path: Path) -> str:
        return path.resolve().as_uri()

    # ---------------------------------------------------------
    # Initial state
    # ---------------------------------------------------------

    def get_initial_state(self):

        self.sync_input_folder()

        categories = sorted(
            {
                preset.category
                for preset in PRESETS.values()
            }
        )

        preset_data = {}

        for category in categories:
            preset_data[category] = [
                {
                    "name": preset.name,
                    "display_name": display_name(
                        preset.name
                    ),
                    "category": preset.category,
                }
                for preset in PRESETS.values()
                if preset.category == category
            ]

        if categories and not self.selected_preset_name:
            self.selected_preset_name = (
                preset_data[categories[0]][0]["name"]
                if preset_data[categories[0]]
                else None
            )

        return {
            "input_folder": {
                "name": self.input_folder.name,
                "path": str(self.input_folder),
            },
            "photos": [
                {
                    "path": str(path),
                    "uri": self._image_to_uri(path),
                    "name": path.name,
                }
                for path in self.photo_paths
            ],
            "selected_index": self.selected_photo_index,
            "categories": categories,
            "presets": preset_data,
            "selected_preset": self.selected_preset_name,
            "processing": self.processing_status,
        }

    # ---------------------------------------------------------
    # Folder / photos
    # ---------------------------------------------------------

    def get_folder_images(self):

        images = self._find_images_in_folder(
            self.input_folder
        )

        return [
            {
                "path": str(path),
                "uri": self._image_to_uri(path),
                "name": path.name,
            }
            for path in images
        ]

    def sync_input_folder(self):

        folder_images = self._find_images_in_folder(
            self.input_folder
        )

        folder_set = {
            path.resolve()
            for path in folder_images
        }

        existing_external = []

        for path in self.photo_paths:

            try:
                resolved = path.resolve()

                inside_folder = resolved.is_relative_to(
                    self.input_folder.resolve()
                )

            except (
                OSError,
                ValueError,
            ):
                inside_folder = False
                resolved = path

            if not inside_folder and path.exists():
                existing_external.append(path)

        self.photo_paths = (
            folder_images
            + existing_external
        )

        if self.photo_paths:

            if (
                self.selected_photo_index
                >= len(self.photo_paths)
            ):
                self.selected_photo_index = 0

        else:
            self.selected_photo_index = 0

        return self.get_folder_images()

    def select_folder(self):

        if self.window is None:
            return None

        result = self.window.create_file_dialog(
            webview.FOLDER_DIALOG,
            directory=str(self.input_folder),
        )

        if not result:
            return None

        folder = Path(result[0]).expanduser().resolve()

        folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.input_folder = folder

        self._save_input_folder()

        self.photo_paths = []

        self.selected_photo_index = 0

        self.sync_input_folder()

        return {
            "name": self.input_folder.name,
            "path": str(self.input_folder),
            "photos": self.get_folder_images(),
        }

    def select_images(self):

        if self.window is None:
            return []

        result = self.window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=(
                "Images (*.jpg;*.jpeg;*.png;*.webp)",
                "JPEG (*.jpg;*.jpeg)",
                "PNG (*.png)",
                "WebP (*.webp)",
            ),
        )

        if not result:
            return []

        added = []

        for raw_path in result:

            path = Path(raw_path).expanduser().resolve()

            if (
                path.is_file()
                and path.suffix.lower()
                in SUPPORTED_EXTENSIONS
                and path not in self.photo_paths
            ):
                self.photo_paths.append(path)
                added.append(path)

        if self.photo_paths and not added:
            return self.get_photo_state()

        if added and len(self.photo_paths) == len(added):
            self.selected_photo_index = 0

        return self.get_photo_state()

    def add_dropped_paths(self, paths):

        added = []

        for raw_path in paths:

            path = Path(raw_path).expanduser()

            if path.is_dir():
                candidates = (
                    self._find_images_in_folder(path)
                )
            else:
                candidates = [path]

            for candidate in candidates:

                try:
                    candidate = candidate.resolve()
                except OSError:
                    continue

                if (
                    candidate.is_file()
                    and candidate.suffix.lower()
                    in SUPPORTED_EXTENSIONS
                    and candidate not in self.photo_paths
                ):
                    self.photo_paths.append(candidate)
                    added.append(candidate)

        if added and len(self.photo_paths) == len(added):
            self.selected_photo_index = 0

        return self.get_photo_state()

    def get_photo_state(self):

        return {
            "photos": [
                {
                    "path": str(path),
                    "uri": self._image_to_uri(path),
                    "name": path.name,
                }
                for path in self.photo_paths
            ],
            "selected_index": self.selected_photo_index,
        }

    def select_photo(self, index):

        if not self.photo_paths:
            return self.get_photo_state()

        index = max(
            0,
            min(
                len(self.photo_paths) - 1,
                int(index),
            ),
        )

        self.selected_photo_index = index

        return self.get_photo_state()

    def clear_photos(self):

        if self.processing:
            return self.get_photo_state()

        self.photo_paths.clear()

        self.selected_photo_index = 0

        return self.get_photo_state()

    # ---------------------------------------------------------
    # Presets
    # ---------------------------------------------------------

    def get_presets(self):

        categories = sorted(
            {
                preset.category
                for preset in PRESETS.values()
            }
        )

        result = {}

        for category in categories:

            result[category] = []

            for preset in PRESETS.values():

                if preset.category != category:
                    continue

                result[category].append(
                    {
                        "name": preset.name,
                        "display_name": display_name(
                            preset.name
                        ),
                        "category": preset.category,
                    }
                )

        return {
            "categories": categories,
            "presets": result,
            "selected": self.selected_preset_name,
        }

    def select_preset(self, preset_name):

        preset = get_preset_by_name(
            preset_name
        )

        if preset is None:
            return {
                "success": False,
                "error": "Preset not found.",
            }

        self.selected_preset_name = preset.name

        return {
            "success": True,
            "preset": {
                "name": preset.name,
                "display_name": display_name(
                    preset.name
                ),
                "category": preset.category,
            },
        }

    # ---------------------------------------------------------
    # Preview
    # ---------------------------------------------------------

    def generate_preview(self):

        if not self.photo_paths:
            return {
                "success": False,
                "error": "No photos selected.",
            }

        if (
            self.selected_photo_index
            >= len(self.photo_paths)
        ):
            self.selected_photo_index = 0

        if not self.selected_preset_name:
            return {
                "success": False,
                "error": "No preset selected.",
            }

        preset = get_preset_by_name(
            self.selected_preset_name
        )

        if preset is None:
            return {
                "success": False,
                "error": "Preset not found.",
            }

        input_path = self.photo_paths[
            self.selected_photo_index
        ]

        self.preview_token += 1

        token = self.preview_token

        output_path = (
            self.preview_directory
            / f"preview_{token}.jpg"
        )

        try:

            process_image(
                input_path,
                output_path,
                preset.settings,
            )

            with Image.open(output_path) as image:
                image = ImageOps.exif_transpose(
                    image
                ).convert("RGB")

                image.save(
                    output_path,
                    "JPEG",
                    quality=92,
                )

            return {
                "success": True,
                "token": token,
                "before": self._image_to_uri(
                    input_path
                ),
                "after": self._image_to_uri(
                    output_path
                ),
            }

        except Exception as error:

            return {
                "success": False,
                "error": str(error),
            }

    # ---------------------------------------------------------
    # Processing
    # ---------------------------------------------------------

    def _create_output_folder(
        self,
        count: int,
        preset_name: str,
    ) -> Path:

        timestamp = datetime.now().strftime(
            "%H-%M_%d-%m-%y"
        )

        folder_name = (
            f"{count}_{preset_name}_images_{timestamp}"
        )

        output_folder = (
            self.output_folder / folder_name
        )

        counter = 2

        while output_folder.exists():

            output_folder = (
                self.output_folder
                / f"{folder_name}_{counter}"
            )

            counter += 1

        output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        return output_folder

    def _get_unique_output_path(
        self,
        output_folder: Path,
        filename: str,
    ) -> Path:

        output_path = (
            output_folder / filename
        )

        if not output_path.exists():
            return output_path

        original = Path(filename)

        counter = 2

        while True:

            output_path = (
                output_folder
                / f"{original.stem}_{counter}{original.suffix}"
            )

            if not output_path.exists():
                return output_path

            counter += 1

    def process_photos(self):

        if self.processing:
            return {
                "success": False,
                "error": "Already processing.",
            }

        if not self.photo_paths:
            return {
                "success": False,
                "error": "No photos selected.",
            }

        if not self.selected_preset_name:
            return {
                "success": False,
                "error": "No preset selected.",
            }

        preset = get_preset_by_name(
            self.selected_preset_name
        )

        if preset is None:
            return {
                "success": False,
                "error": "Preset not found.",
            }

        photos = list(self.photo_paths)

        self.processing = True

        self.processing_status = {
            "processing": True,
            "progress": 0.0,
            "current": 0,
            "total": len(photos),
            "status": "Preparing photos...",
            "successful": 0,
            "failed": 0,
            "output_folder": None,
        }

        thread = threading.Thread(
            target=self._process_worker,
            args=(photos, preset),
            daemon=True,
        )

        thread.start()

        return {
            "success": True,
        }

    def _process_worker(
        self,
        photos,
        preset,
    ):

        total = len(photos)

        successful = 0
        failed = 0

        output_folder = self._create_output_folder(
            total,
            preset.name,
        )

        for index, input_path in enumerate(
            photos,
            start=1,
        ):

            try:

                output_path = (
                    self._get_unique_output_path(
                        output_folder,
                        input_path.name,
                    )
                )

                process_image(
                    input_path,
                    output_path,
                    preset.settings,
                )

                successful += 1

            except Exception:
                failed += 1

            self.processing_status = {
                "processing": True,
                "progress": index / total,
                "current": index,
                "total": total,
                "status": (
                    f"Editing {index} of {total}..."
                ),
                "successful": successful,
                "failed": failed,
                "output_folder": str(output_folder),
            }

        self.processing = False

        self.last_output_folder = output_folder

        self.processing_status = {
            "processing": False,
            "progress": 1.0,
            "current": total,
            "total": total,
            "status": (
                f"Finished — {successful} "
                f"photo"
                f"{'s' if successful != 1 else ''} "
                f"edited successfully."
                if failed == 0
                else
                f"Finished — {successful} succeeded, "
                f"{failed} failed."
            ),
            "successful": successful,
            "failed": failed,
            "output_folder": str(output_folder),
        }

    def get_processing_status(self):
        return self.processing_status

    # ---------------------------------------------------------
    # Output
    # ---------------------------------------------------------

    def open_output_folder(self):

        folder = (
            self.last_output_folder
            if (
                self.last_output_folder
                and self.last_output_folder.exists()
            )
            else self.output_folder
        )

        try:

            if sys.platform == "darwin":

                subprocess.run(
                    ["open", str(folder)],
                    check=False,
                )

            elif sys.platform == "win32":

                os.startfile(str(folder))

            else:

                subprocess.run(
                    ["xdg-open", str(folder)],
                    check=False,
                )

            return {
                "success": True,
            }

        except Exception as error:

            return {
                "success": False,
                "error": str(error),
            }


def main():

    api = LumaAPI()

    window = webview.create_window(
        "Luma",
        (
            Path(__file__).parent
            / "web"
            / "index.html"
        ).as_uri(),
        js_api=api,
        width=1450,
        height=900,
        min_size=(1180, 760),
        background_color="#111111",
    )

    api.window = window

    webview.start(
        debug=False,
    )


if __name__ == "__main__":
    main()

