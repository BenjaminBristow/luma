from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageOps, ImageTk

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES

    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from luma.presets import PRESETS
from luma.processor import process_image


# ---------------------------------------------------------------------------
# Appearance
# ---------------------------------------------------------------------------

BG = "#F4F5F7"
CARD = "#FFFFFF"
CARD_BORDER = "#E7E9ED"

TEXT = "#17191C"
SECONDARY_TEXT = "#73777F"
MUTED_TEXT = "#A0A4AA"

ACCENT = "#4F7CFF"
ACCENT_HOVER = "#3F6CEB"

SUCCESS = "#2E9B63"
ERROR = "#D94A4A"

RADIUS = 18

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


# ---------------------------------------------------------------------------
# Platform helpers
# ---------------------------------------------------------------------------

def get_pictures_folder() -> Path:
    """
    Return the user's normal Pictures folder.

    macOS and Linux normally use ~/Pictures.

    Windows normally uses the Pictures folder inside the user's
    user profile.
    """

    home = Path.home()

    if sys.platform == "win32":
        pictures = Path(
            os.environ.get(
                "USERPROFILE",
                str(home),
            )
        ) / "Pictures"

    else:
        pictures = home / "Pictures"

    # If the Pictures folder does not exist, use the home folder
    # as a safe fallback.
    if not pictures.exists():
        pictures = home

    return pictures


def get_settings_folder() -> Path:
    """
    Return a suitable folder for Luma's small settings file.

    The exact location differs between operating systems, so we
    keep this logic separate from the rest of the GUI.
    """

    home = Path.home()

    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA")

        if app_data:
            return Path(app_data) / "Luma"

        return home / "AppData" / "Roaming" / "Luma"

    if sys.platform == "darwin":
        return (
            home
            / "Library"
            / "Application Support"
            / "Luma"
        )

    # Linux and other Unix-like systems.
    return home / ".config" / "luma"


# ---------------------------------------------------------------------------
# Preset helpers
# ---------------------------------------------------------------------------

def get_preset_categories() -> list[str]:
    """Return all available preset categories."""

    return sorted(
        {
            preset.category
            for preset in PRESETS.values()
        }
    )


def get_presets_for_category(
    category: str,
) -> list[str]:
    """Return preset names belonging to a category."""

    return [
        preset.name
        for preset in PRESETS.values()
        if preset.category == category
    ]


def get_preset_by_name(name: str):
    """Find a preset by its name."""

    for preset in PRESETS.values():
        if preset.name == name:
            return preset

    return None


def display_name(name: str) -> str:
    """Turn an internal name into readable UI text."""

    return (
        name
        .replace("-", " ")
        .replace("_", " ")
        .title()
    )


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class LumaApp:
    """Main Luma graphical application."""

    def __init__(self, root):
        self.root = root

        self.root.title("Luma")
        self.root.geometry("1180x820")
        self.root.minsize(1000, 720)

        # -------------------------------------------------------------------
        # Luma folders
        # -------------------------------------------------------------------

        self.luma_root = get_pictures_folder() / "Luma"

        self.default_input_folder = (
            self.luma_root / "Luma_Input"
        )

        self.output_folder = (
            self.luma_root / "Luma_Output"
        )

        # These folders are created automatically the first time
        # Luma is opened.
        self.default_input_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        # The active input folder can be changed by the user.
        self.input_folder = (
            self._load_saved_input_folder()
        )

        # If a previously selected folder no longer exists,
        # fall back to Luma_Input.
        if not self.input_folder.exists():
            self.input_folder = (
                self.default_input_folder
            )

        self.input_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        # -------------------------------------------------------------------
        # Application state
        # -------------------------------------------------------------------

        self.photo_paths: list[Path] = []

        self.example_image_path: Path | None = None

        self.preview_photo_before = None
        self.preview_photo_after = None

        # Each preview receives a token. This prevents an older
        # background preview from replacing a newer one.
        self.current_preview_token = 0

        self.processing = False

        self.last_output_folder: Path | None = None

        # -------------------------------------------------------------------
        # Build interface
        # -------------------------------------------------------------------

        self._configure_appearance()
        self._build_interface()

        if DND_AVAILABLE:
            self._setup_drag_and_drop()

        # Automatically load photos from the current input folder.
        self.load_input_folder()

    # -----------------------------------------------------------------------
    # Appearance
    # -----------------------------------------------------------------------

    def _configure_appearance(self):
        """Configure CustomTkinter's appearance."""

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.root.configure(
            background=BG,
        )

    # -----------------------------------------------------------------------
    # Interface
    # -----------------------------------------------------------------------

    def _build_interface(self):
        """Build the complete Luma interface."""

        self.root.grid_rowconfigure(
            1,
            weight=1,
        )

        self.root.grid_columnconfigure(
            0,
            weight=1,
        )

        main = ctk.CTkFrame(
            self.root,
            fg_color=BG,
            corner_radius=0,
        )

        main.grid(
            row=0,
            column=0,
            rowspan=2,
            sticky="nsew",
            padx=28,
            pady=24,
        )

        main.grid_rowconfigure(
            2,
            weight=1,
        )

        main.grid_columnconfigure(
            0,
            weight=1,
        )

        self._build_header(main)

        controls = ctk.CTkFrame(
            main,
            fg_color="transparent",
        )

        controls.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(24, 18),
        )

        controls.grid_columnconfigure(
            0,
            weight=1,
        )

        controls.grid_columnconfigure(
            1,
            weight=1,
        )

        self._build_import_card(controls)
        self._build_preset_card(controls)

        self._build_preview_section(main)

        self._build_bottom_bar(main)

    def _build_header(self, parent):
        """Build the application header."""

        header = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        header.grid_columnconfigure(
            0,
            weight=1,
        )

        title = ctk.CTkLabel(
            header,
            text="Luma",
            font=ctk.CTkFont(
                family="Arial",
                size=30,
                weight="bold",
            ),
            text_color=TEXT,
        )

        title.grid(
            row=0,
            column=0,
            sticky="w",
        )

        subtitle = ctk.CTkLabel(
            header,
            text="Simple photo editing without the complicated bits.",
            font=ctk.CTkFont(
                family="Arial",
                size=13,
            ),
            text_color=SECONDARY_TEXT,
        )

        subtitle.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(2, 0),
        )

        self.clear_button = ctk.CTkButton(
            header,
            text="Clear photos",
            width=115,
            height=36,
            corner_radius=10,
            fg_color="#F1F2F4",
            hover_color="#E6E8EC",
            text_color=TEXT,
            border_width=1,
            border_color=CARD_BORDER,
            command=self.clear_photos,
        )

        self.clear_button.grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="e",
        )

    # -----------------------------------------------------------------------
    # Import card
    # -----------------------------------------------------------------------

    def _build_import_card(self, parent):
        """Build the input-folder and photo import card."""

        card = ctk.CTkFrame(
            parent,
            fg_color=CARD,
            corner_radius=RADIUS,
            border_width=1,
            border_color=CARD_BORDER,
        )

        card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8),
        )

        card.grid_columnconfigure(
            0,
            weight=1,
        )

        icon = ctk.CTkLabel(
            card,
            text="+",
            font=ctk.CTkFont(
                family="Arial",
                size=34,
                weight="bold",
            ),
            text_color=ACCENT,
        )

        icon.grid(
            row=0,
            column=0,
            pady=(18, 0),
        )

        title = ctk.CTkLabel(
            card,
            text="Import Photos",
            font=ctk.CTkFont(
                family="Arial",
                size=17,
                weight="bold",
            ),
            text_color=TEXT,
        )

        title.grid(
            row=1,
            column=0,
        )

        current_label = ctk.CTkLabel(
            card,
            text="Current folder:",
            font=ctk.CTkFont(
                family="Arial",
                size=12,
            ),
            text_color=SECONDARY_TEXT,
        )

        current_label.grid(
            row=2,
            column=0,
            pady=(10, 2),
        )

        # This displays only the folder name to keep the interface
        # simple. The full path is available in the tooltip-like
        # secondary label underneath.
        self.input_folder_name_label = ctk.CTkLabel(
            card,
            text=self.input_folder.name,
            font=ctk.CTkFont(
                family="Arial",
                size=16,
                weight="bold",
            ),
            text_color=TEXT,
        )

        self.input_folder_name_label.grid(
            row=3,
            column=0,
        )

        self.input_folder_path_label = ctk.CTkLabel(
            card,
            text=self._shorten_path(
                self.input_folder
            ),
            font=ctk.CTkFont(
                family="Arial",
                size=10,
            ),
            text_color=MUTED_TEXT,
        )

        self.input_folder_path_label.grid(
            row=4,
            column=0,
            pady=(1, 12),
        )

        self.change_folder_button = ctk.CTkButton(
            card,
            text="Change Folder",
            width=150,
            height=36,
            corner_radius=10,
            fg_color="#F1F2F4",
            hover_color="#E6E8EC",
            text_color=TEXT,
            border_width=1,
            border_color=CARD_BORDER,
            command=self.choose_folder,
        )

        self.change_folder_button.grid(
            row=5,
            column=0,
            pady=(0, 7),
        )

        self.add_photos_button = ctk.CTkButton(
            card,
            text="Add Photos",
            width=150,
            height=36,
            corner_radius=10,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=self.choose_photos,
        )

        self.add_photos_button.grid(
            row=6,
            column=0,
            pady=(0, 18),
        )

        self.drop_card = card

    # -----------------------------------------------------------------------
    # Preset card
    # -----------------------------------------------------------------------

    def _build_preset_card(self, parent):
        """Build the theme and preset controls."""

        card = ctk.CTkFrame(
            parent,
            fg_color=CARD,
            corner_radius=RADIUS,
            border_width=1,
            border_color=CARD_BORDER,
        )

        card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(8, 0),
        )

        card.grid_columnconfigure(
            0,
            weight=1,
        )

        title = ctk.CTkLabel(
            card,
            text="Choose a style",
            font=ctk.CTkFont(
                family="Arial",
                size=17,
                weight="bold",
            ),
            text_color=TEXT,
        )

        title.grid(
            row=0,
            column=0,
            sticky="w",
            padx=22,
            pady=(20, 2),
        )

        subtitle = ctk.CTkLabel(
            card,
            text="Pick a theme, then choose a preset",
            font=ctk.CTkFont(
                family="Arial",
                size=12,
            ),
            text_color=SECONDARY_TEXT,
        )

        subtitle.grid(
            row=1,
            column=0,
            sticky="w",
            padx=22,
            pady=(0, 12),
        )

        categories = get_preset_categories()

        category_values = [
            display_name(category)
            for category in categories
        ]

        self.category_map = dict(
            zip(
                category_values,
                categories,
            )
        )

        initial_category = (
            category_values[0]
            if category_values
            else ""
        )

        self.category_menu = ctk.CTkOptionMenu(
            card,
            values=category_values
            or ["No themes available"],
            width=230,
            height=38,
            corner_radius=10,
            fg_color="#F1F2F4",
            button_color="#E5E7EB",
            button_hover_color="#D9DCE1",
            text_color=TEXT,
            dropdown_fg_color=CARD,
            dropdown_hover_color="#EEF1F5",
            dropdown_text_color=TEXT,
            command=self._category_changed,
        )

        self.category_menu.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=22,
            pady=(0, 8),
        )

        presets = (
            get_presets_for_category(
                self.category_map[
                    initial_category
                ]
            )
            if initial_category
            else []
        )

        preset_values = [
            display_name(preset)
            for preset in presets
        ]

        self.preset_map = dict(
            zip(
                preset_values,
                presets,
            )
        )

        self.preset_menu = ctk.CTkOptionMenu(
            card,
            values=preset_values
            or ["No presets available"],
            width=230,
            height=38,
            corner_radius=10,
            fg_color="#F1F2F4",
            button_color="#E5E7EB",
            button_hover_color="#D9DCE1",
            text_color=TEXT,
            dropdown_fg_color=CARD,
            dropdown_hover_color="#EEF1F5",
            dropdown_text_color=TEXT,
            command=self._preset_changed,
        )

        self.preset_menu.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=22,
            pady=(0, 20),
        )

        if preset_values:
            self.preset_menu.set(
                preset_values[0]
            )

    # -----------------------------------------------------------------------
    # Preview
    # -----------------------------------------------------------------------

    def _build_preview_section(self, parent):
        """Build the BEFORE and AFTER preview area."""

        preview_container = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )

        preview_container.grid(
            row=2,
            column=0,
            sticky="nsew",
        )

        preview_container.grid_columnconfigure(
            0,
            weight=1,
        )

        preview_container.grid_columnconfigure(
            1,
            weight=1,
        )

        preview_container.grid_rowconfigure(
            1,
            weight=1,
        )

        before_title = ctk.CTkLabel(
            preview_container,
            text="BEFORE",
            font=ctk.CTkFont(
                family="Arial",
                size=11,
                weight="bold",
            ),
            text_color=SECONDARY_TEXT,
        )

        before_title.grid(
            row=0,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(0, 7),
        )

        after_title = ctk.CTkLabel(
            preview_container,
            text="AFTER",
            font=ctk.CTkFont(
                family="Arial",
                size=11,
                weight="bold",
            ),
            text_color=SECONDARY_TEXT,
        )

        after_title.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(8, 0),
            pady=(0, 7),
        )

        self.before_card = ctk.CTkFrame(
            preview_container,
            fg_color=CARD,
            corner_radius=RADIUS,
            border_width=1,
            border_color=CARD_BORDER,
        )

        self.before_card.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(0, 8),
        )

        self.after_card = ctk.CTkFrame(
            preview_container,
            fg_color=CARD,
            corner_radius=RADIUS,
            border_width=1,
            border_color=CARD_BORDER,
        )

        self.after_card.grid(
            row=1,
            column=1,
            sticky="nsew",
            padx=(8, 0),
        )

        self.before_label = ctk.CTkLabel(
            self.before_card,
            text="Add a photo to see a preview",
            font=ctk.CTkFont(
                family="Arial",
                size=13,
            ),
            text_color=MUTED_TEXT,
        )

        self.before_label.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
        )

        self.after_label = ctk.CTkLabel(
            self.after_card,
            text="Your edited preview will appear here",
            font=ctk.CTkFont(
                family="Arial",
                size=13,
            ),
            text_color=MUTED_TEXT,
        )

        self.after_label.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
        )

    # -----------------------------------------------------------------------
    # Bottom bar
    # -----------------------------------------------------------------------

    def _build_bottom_bar(self, parent):
        """Build status, progress and processing controls."""

        bottom = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )

        bottom.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(18, 0),
        )

        bottom.grid_columnconfigure(
            0,
            weight=1,
        )

        self.photo_count_label = ctk.CTkLabel(
            bottom,
            text="0 photos",
            font=ctk.CTkFont(
                family="Arial",
                size=12,
            ),
            text_color=SECONDARY_TEXT,
        )

        self.photo_count_label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.status_label = ctk.CTkLabel(
            bottom,
            text="Ready",
            font=ctk.CTkFont(
                family="Arial",
                size=12,
            ),
            text_color=SECONDARY_TEXT,
        )

        self.status_label.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(2, 0),
        )

        self.progress = ctk.CTkProgressBar(
            bottom,
            width=260,
            height=8,
            corner_radius=5,
        )

        self.progress.grid(
            row=0,
            column=1,
            rowspan=2,
            padx=18,
        )

        self.progress.set(0)

        self.output_button = ctk.CTkButton(
            bottom,
            text="Open Output",
            width=115,
            height=38,
            corner_radius=10,
            fg_color="#F1F2F4",
            hover_color="#E6E8EC",
            text_color=TEXT,
            border_width=1,
            border_color=CARD_BORDER,
            command=self.open_output_folder,
        )

        self.output_button.grid(
            row=0,
            column=2,
            rowspan=2,
            padx=(0, 10),
        )

        self.edit_button = ctk.CTkButton(
            bottom,
            text="EDIT PHOTOS",
            width=160,
            height=44,
            corner_radius=12,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(
                family="Arial",
                size=13,
                weight="bold",
            ),
            command=self.process_photos,
        )

        self.edit_button.grid(
            row=0,
            column=3,
            rowspan=2,
        )

    # -----------------------------------------------------------------------
    # Folder memory
    # -----------------------------------------------------------------------

    @property
    def settings_file(self) -> Path:
        """Return the location of Luma's settings file."""

        return (
            get_settings_folder()
            / "settings.json"
        )

    def _load_saved_input_folder(self) -> Path:
        """Load the user's previously selected input folder."""

        try:
            if not self.settings_file.exists():
                return self.default_input_folder

            with self.settings_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                settings = json.load(file)

            saved_folder = settings.get(
                "input_folder"
            )

            if not saved_folder:
                return self.default_input_folder

            return Path(saved_folder).expanduser()

        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
        ):
            # A broken settings file should never stop Luma
            # from opening.
            return self.default_input_folder

    def _save_input_folder(self):
        """Remember the currently selected input folder."""

        try:
            settings_folder = (
                self.settings_file.parent
            )

            settings_folder.mkdir(
                parents=True,
                exist_ok=True,
            )

            settings = {
                "input_folder": str(
                    self.input_folder
                ),
            }

            with self.settings_file.open(
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    settings,
                    file,
                    indent=4,
                )

        except OSError:
            # Folder memory is a convenience, so a failure here
            # should not prevent the application from working.
            pass

    def _update_input_folder_display(self):
        """Update the folder name and path shown in the GUI."""

        self.input_folder_name_label.configure(
            text=self.input_folder.name
        )

        self.input_folder_path_label.configure(
            text=self._shorten_path(
                self.input_folder
            )
        )

    # -----------------------------------------------------------------------
    # Drag and drop
    # -----------------------------------------------------------------------

    def _setup_drag_and_drop(self):
        """Enable drag-and-drop support."""

        self.root.drop_target_register(
            DND_FILES
        )

        self.root.dnd_bind(
            "<<Drop>>",
            self._handle_drop,
        )

    def _handle_drop(self, event):
        """Handle files or folders dropped onto Luma."""

        paths = self.root.tk.splitlist(
            event.data
        )

        collected_paths = []

        for raw_path in paths:
            path = Path(raw_path)

            if path.is_dir():
                collected_paths.extend(
                    self._find_images_in_folder(
                        path
                    )
                )

            elif path.is_file():
                collected_paths.append(path)

        self._add_photo_paths(
            collected_paths
        )

    # -----------------------------------------------------------------------
    # Folder / photo importing
    # -----------------------------------------------------------------------

    def choose_folder(self):
        """Choose and remember a new input folder."""

        folder = filedialog.askdirectory(
            title="Choose photo folder",
        )

        if not folder:
            return

        new_folder = Path(folder)

        # Save the user's choice so it is remembered next time
        # Luma is opened.
        self.input_folder = new_folder

        self.input_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._save_input_folder()
        self._update_input_folder_display()

        # Changing folders should replace the current batch rather
        # than adding another folder's images to it.
        self.photo_paths.clear()
        self.example_image_path = None

        self.preview_photo_before = None
        self.preview_photo_after = None

        self.current_preview_token += 1

        self.before_label.configure(
            image="",
            text="Add a photo to see a preview",
            text_color=MUTED_TEXT,
        )

        self.after_label.configure(
            image="",
            text="Your edited preview will appear here",
            text_color=MUTED_TEXT,
        )

        self.load_input_folder()

        self.status_label.configure(
            text=f"Using {self.input_folder.name}",
            text_color=SUCCESS,
        )

    def choose_photos(self):
        """Add individual photos to the current batch."""

        paths = filedialog.askopenfilenames(
            title="Add photos",
            filetypes=[
                (
                    "Images",
                    "*.jpg *.jpeg *.png *.webp",
                ),
                (
                    "JPEG",
                    "*.jpg *.jpeg",
                ),
                (
                    "PNG",
                    "*.png",
                ),
                (
                    "WebP",
                    "*.webp",
                ),
            ],
        )

        if paths:
            self._add_photo_paths(
                [
                    Path(path)
                    for path in paths
                ]
            )

    def load_input_folder(self):
        """Load all supported images from the active input folder."""

        paths = self._find_images_in_folder(
            self.input_folder
        )

        if paths:
            self._add_photo_paths(
                paths,
                show_status=False,
            )

        else:
            self._update_photo_count()

    def _find_images_in_folder(
        self,
        folder: Path,
    ) -> list[Path]:
        """Recursively find supported images in a folder."""

        if not folder.exists():
            return []

        paths = []

        # rglob() allows users to keep images inside subfolders.
        for path in folder.rglob("*"):
            if not path.is_file():
                continue

            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            paths.append(path)

        return sorted(paths)

    def _add_photo_paths(
        self,
        paths: list[Path],
        show_status: bool = True,
    ):
        """Add valid images to the current batch."""

        added = []

        for path in paths:
            try:
                path = path.resolve()
            except OSError:
                continue

            if not path.is_file():
                continue

            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            if path in self.photo_paths:
                continue

            self.photo_paths.append(path)
            added.append(path)

        if not added:
            return

        if self.example_image_path is None:
            self.example_image_path = added[0]

        self._update_photo_count()

        if show_status:
            self.status_label.configure(
                text=(
                    f"Added {len(added)} photo"
                    + (
                        "s"
                        if len(added) != 1
                        else ""
                    )
                ),
                text_color=SUCCESS,
            )

        self._show_before_preview()
        self._generate_preview()

    # -----------------------------------------------------------------------
    # Photo count / clearing
    # -----------------------------------------------------------------------

    def _update_photo_count(self):
        """Update the photo counter."""

        count = len(self.photo_paths)

        if count == 1:
            text = "1 photo"
        else:
            text = f"{count} photos"

        self.photo_count_label.configure(
            text=text
        )

    def clear_photos(self):
        """Clear the current batch without changing the input folder."""

        if self.processing:
            return

        self.photo_paths.clear()
        self.example_image_path = None

        self.preview_photo_before = None
        self.preview_photo_after = None

        self.current_preview_token += 1

        self.before_label.configure(
            image="",
            text="Add a photo to see a preview",
            text_color=MUTED_TEXT,
        )

        self.after_label.configure(
            image="",
            text="Your edited preview will appear here",
            text_color=MUTED_TEXT,
        )

        self._update_photo_count()

        self.status_label.configure(
            text="Ready",
            text_color=SECONDARY_TEXT,
        )

    # -----------------------------------------------------------------------
    # Preset controls
    # -----------------------------------------------------------------------

    def _category_changed(
        self,
        display_category: str,
    ):
        """Update the preset list when the theme changes."""

        category = self.category_map.get(
            display_category
        )

        if not category:
            return

        presets = get_presets_for_category(
            category
        )

        display_presets = [
            display_name(preset)
            for preset in presets
        ]

        self.preset_map = dict(
            zip(
                display_presets,
                presets,
            )
        )

        self.preset_menu.configure(
            values=display_presets
            or ["No presets available"]
        )

        if display_presets:
            self.preset_menu.set(
                display_presets[0]
            )

            self._preset_changed(
                display_presets[0]
            )

    def _preset_changed(
        self,
        display_preset: str,
    ):
        """Regenerate the preview when the preset changes."""

        if display_preset == "No presets available":
            return

        self._generate_preview()

    # -----------------------------------------------------------------------
    # Preview
    # -----------------------------------------------------------------------

    def _show_before_preview(self):
        """Display the first imported image in the BEFORE panel."""

        if self.example_image_path is None:
            return

        try:
            image = Image.open(
                self.example_image_path
            )

            # Apply the camera's EXIF orientation so portrait
            # photographs are displayed the correct way up.
            image = ImageOps.exif_transpose(
                image
            ).convert("RGB")

            self._set_preview_image(
                self.before_label,
                image,
                before=True,
            )

        except Exception as error:
            self.before_label.configure(
                image="",
                text="Could not load image",
                text_color=ERROR,
            )

            self.status_label.configure(
                text=f"Could not load preview: {error}",
                text_color=ERROR,
            )

    def _generate_preview(self):
        """Generate an edited preview in the background."""

        if self.example_image_path is None:
            return

        display_preset = self.preset_menu.get()

        if not display_preset:
            return

        preset_name = self.preset_map.get(
            display_preset
        )

        if not preset_name:
            return

        preset = get_preset_by_name(
            preset_name
        )

        if preset is None:
            return

        self.current_preview_token += 1

        token = self.current_preview_token

        input_path = self.example_image_path

        self.after_label.configure(
            image="",
            text="Generating preview...",
            text_color=MUTED_TEXT,
        )

        def worker():
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    output_path = (
                        Path(temp_dir)
                        / "preview.jpg"
                    )

                    process_image(
                        input_path,
                        output_path,
                        preset.settings,
                    )

                    preview = Image.open(
                        output_path
                    ).convert("RGB")

                    preview.load()

                self.root.after(
                    0,
                    lambda: self._finish_preview(
                        token,
                        preview,
                    ),
                )

            except Exception as error:
                self.root.after(
                    0,
                    lambda: self._preview_error(
                        token,
                        error,
                    ),
                )

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()

    def _finish_preview(
        self,
        token: int,
        image: Image.Image,
    ):
        """Display a preview if it is still the newest one."""

        if token != self.current_preview_token:
            return

        self._set_preview_image(
            self.after_label,
            image,
            before=False,
        )

    def _preview_error(
        self,
        token: int,
        error: Exception,
    ):
        """Display a preview error."""

        if token != self.current_preview_token:
            return

        self.after_label.configure(
            image="",
            text="Could not generate preview",
            text_color=ERROR,
        )

        self.status_label.configure(
            text=f"Preview error: {error}",
            text_color=ERROR,
        )

    def _set_preview_image(
        self,
        label,
        image: Image.Image,
        before: bool,
    ):
        """Resize an image to fit the preview panel."""

        image = image.copy()

        image.thumbnail(
            (470, 280),
            Image.Resampling.LANCZOS,
        )

        photo = ImageTk.PhotoImage(
            image
        )

        label.configure(
            image=photo,
            text="",
        )

        # Tkinter needs a Python reference to prevent the image
        # from being garbage collected.
        if before:
            self.preview_photo_before = photo
        else:
            self.preview_photo_after = photo

    # -----------------------------------------------------------------------
    # Processing
    # -----------------------------------------------------------------------

    def process_photos(self):
        """Process every currently loaded photo."""

        if self.processing:
            return

        if not self.photo_paths:
            messagebox.showinfo(
                "No photos",
                "Add some photos before editing them.",
            )
            return

        display_preset = self.preset_menu.get()

        preset_name = self.preset_map.get(
            display_preset
        )

        if not preset_name:
            messagebox.showerror(
                "No preset",
                "Please choose a preset.",
            )
            return

        preset = get_preset_by_name(
            preset_name
        )

        if preset is None:
            messagebox.showerror(
                "Preset error",
                "The selected preset could not be found.",
            )
            return

        self.processing = True

        self.progress.set(0)

        self.edit_button.configure(
            state="disabled",
            text="EDITING...",
        )

        self.clear_button.configure(
            state="disabled"
        )

        self.change_folder_button.configure(
            state="disabled"
        )

        self.add_photos_button.configure(
            state="disabled"
        )

        self.status_label.configure(
            text="Preparing photos...",
            text_color=SECONDARY_TEXT,
        )

        photos = list(
            self.photo_paths
        )

        threading.Thread(
            target=self._process_worker,
            args=(
                photos,
                preset,
            ),
            daemon=True,
        ).start()

    def _process_worker(
        self,
        photos: list[Path],
        preset,
    ):
        """Process the batch in a background thread."""

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

            progress = index / total

            self.root.after(
                0,
                lambda
                value=progress,
                current=index,
                total_count=total:
                    self._update_progress(
                        value,
                        current,
                        total_count,
                    ),
            )

        self.root.after(
            0,
            lambda: self._processing_finished(
                output_folder,
                successful,
                failed,
            ),
        )

    def _update_progress(
        self,
        value: float,
        current: int,
        total: int,
    ):
        """Update progress safely on the UI thread."""

        self.progress.set(value)

        self.status_label.configure(
            text=(
                f"Editing {current} "
                f"of {total}..."
            )
        )

    def _processing_finished(
        self,
        output_folder: Path,
        successful: int,
        failed: int,
    ):
        """Restore the interface after processing."""

        self.processing = False

        self.last_output_folder = output_folder

        self.edit_button.configure(
            state="normal",
            text="EDIT PHOTOS",
        )

        self.clear_button.configure(
            state="normal"
        )

        self.change_folder_button.configure(
            state="normal"
        )

        self.add_photos_button.configure(
            state="normal"
        )

        self.progress.set(1)

        if failed == 0:
            status = (
                f"Finished — {successful} photo"
                + (
                    "s"
                    if successful != 1
                    else ""
                )
                + " edited successfully."
            )

            self.status_label.configure(
                text=status,
                text_color=SUCCESS,
            )

        else:
            status = (
                f"Finished — {successful} succeeded, "
                f"{failed} failed."
            )

            self.status_label.configure(
                text=status,
                text_color=ERROR,
            )

        result = messagebox.askyesno(
            "Luma finished",
            (
                f"{successful} photo"
                + (
                    "s"
                    if successful != 1
                    else ""
                )
                + " edited successfully.\n\n"
                + (
                    f"{failed} photo"
                    + (
                        "s"
                        if failed != 1
                        else ""
                    )
                    + " failed.\n\n"
                    if failed
                    else ""
                )
                + "Open the output folder?"
            ),
        )

        if result:
            self.open_output_folder()

    # -----------------------------------------------------------------------
    # Output handling
    # -----------------------------------------------------------------------

    def _create_output_folder(
        self,
        count: int,
        preset_name: str,
    ) -> Path:
        """
        Create a timestamped output folder.

        Example:
        12_cinematic_images_01-23_21-09-26
        """

        timestamp = datetime.now().strftime(
            "%H-%M_%d-%m-%y"
        )

        folder_name = (
            f"{count}_"
            f"{preset_name}_"
            f"images_"
            f"{timestamp}"
        )

        output_folder = (
            self.output_folder
            / folder_name
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
        """Prevent duplicate filenames from being overwritten."""

        output_path = (
            output_folder
            / filename
        )

        if not output_path.exists():
            return output_path

        original = Path(filename)

        stem = original.stem
        suffix = original.suffix

        counter = 2

        while True:
            output_path = (
                output_folder
                / f"{stem}_{counter}{suffix}"
            )

            if not output_path.exists():
                return output_path

            counter += 1

    def open_output_folder(self):
        """Open the Luma_Output folder or latest export."""

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

        except Exception as error:
            messagebox.showerror(
                "Could not open folder",
                str(error),
            )

    # -----------------------------------------------------------------------
    # Utility
    # -----------------------------------------------------------------------

    @staticmethod
    def _shorten_path(path: Path) -> str:
        """Make a long folder path easier to display."""

        text = str(path)

        if len(text) <= 55:
            return text

        return "..." + text[-52:]


# ---------------------------------------------------------------------------
# Application entry point
# ---------------------------------------------------------------------------

def main():
    """Start the Luma GUI."""

    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    LumaApp(root)

    root.mainloop()


if __name__ == "__main__":
    main()