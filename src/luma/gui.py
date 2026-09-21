from __future__ import annotations

import threading
import tempfile
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

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")


# ---------------------------------------------------------------------------
# Preset helpers
# ---------------------------------------------------------------------------

def get_preset_categories() -> list[str]:
    """Return all preset categories in alphabetical order."""

    return sorted(
        {
            preset.category
            for preset in PRESETS.values()
        }
    )


def get_presets_for_category(category: str) -> list[str]:
    """Return the preset names belonging to a specific category."""

    return [
        preset.name
        for preset in PRESETS.values()
        if preset.category == category
    ]


def get_preset_by_name(name: str):
    """Return the registered preset class matching the supplied name."""

    for preset in PRESETS.values():
        if preset.name == name:
            return preset

    return None


def display_name(name: str) -> str:
    """
    Convert an internal preset name into a nicer name for the GUI.

    Example:
        old-fashioned -> Old Fashioned
        golden-hour   -> Golden Hour
    """

    return name.replace("-", " ").replace("_", " ").title()


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

class LumaApp:
    """Main Luma desktop application."""

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

    def __init__(self):
        # TkinterDnD.Tk gives the application native drag-and-drop support.
        # CustomTkinter widgets can still be placed inside this root window.
        if DND_AVAILABLE:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()

        self.root.title("Luma")
        self.root.geometry("1180x820")
        self.root.minsize(1000, 720)
        self.root.configure(bg=self.BG)

        # ------------------------------------------------------------------
        # Application state
        # ------------------------------------------------------------------

        self.photo_paths: list[Path] = []

        # The first image added becomes the example image shown in the
        # BEFORE/AFTER preview area.
        self.example_image_path: Path | None = None

        self.preview_photo_before = None
        self.preview_photo_after = None

        self.current_preview_token = 0

        self.processing = False
        self.last_output_folder: Path | None = None

        self.default_output_root = (
            Path.home() / "Pictures" / "Luma"
        )

        # ------------------------------------------------------------------
        # Build interface
        # ------------------------------------------------------------------

        self._build_interface()

        if DND_AVAILABLE:
            self._setup_drag_and_drop()

        self._update_photo_count()

    # ----------------------------------------------------------------------
    # Interface construction
    # ----------------------------------------------------------------------

    def _build_interface(self):
        """Create the complete Luma interface."""

        self.main = ctk.CTkFrame(
            self.root,
            fg_color=self.BG,
            corner_radius=0,
        )
        self.main.pack(fill="both", expand=True)

        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_controls()
        self._build_preview()
        self._build_bottom_bar()

    # ----------------------------------------------------------------------
    # Header
    # ----------------------------------------------------------------------

    def _build_header(self):
        """Build the Luma title and application subtitle."""

        header = ctk.CTkFrame(
            self.main,
            fg_color="transparent",
        )
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=48,
            pady=(32, 8),
        )

        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Luma",
            font=ctk.CTkFont(
                family="Arial",
                size=32,
                weight="bold",
            ),
            text_color=self.TEXT,
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Make your photos look the way you imagined.",
            font=ctk.CTkFont(
                family="Arial",
                size=14,
            ),
            text_color=self.SECONDARY_TEXT,
        )
        subtitle.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(2, 0),
        )

        clear_button = ctk.CTkButton(
            header,
            text="Clear photos",
            width=110,
            height=36,
            corner_radius=10,
            fg_color="#FFFFFF",
            hover_color="#ECEEF1",
            text_color=self.SECONDARY_TEXT,
            border_width=1,
            border_color=self.CARD_BORDER,
            command=self.clear_photos,
        )
        clear_button.grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="e",
        )

    # ----------------------------------------------------------------------
    # Controls
    # ----------------------------------------------------------------------

    def _build_controls(self):
        """Build the photo drop area and preset controls."""

        controls = ctk.CTkFrame(
            self.main,
            fg_color="transparent",
        )
        controls.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=48,
            pady=(12, 12),
        )

        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=1)

        self._build_drop_card(controls)
        self._build_preset_card(controls)

    # ----------------------------------------------------------------------
    # Drop area
    # ----------------------------------------------------------------------

    def _build_drop_card(self, parent):
        """Build the photo import card."""

        card = ctk.CTkFrame(
            parent,
            fg_color=self.CARD,
            corner_radius=self.RADIUS,
            border_width=1,
            border_color=self.CARD_BORDER,
        )
        card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8),
        )

        card.grid_columnconfigure(0, weight=1)

        icon = ctk.CTkLabel(
            card,
            text="+",
            font=ctk.CTkFont(
                family="Arial",
                size=34,
                weight="bold",
            ),
            text_color=self.ACCENT,
        )
        icon.grid(
            row=0,
            column=0,
            pady=(20, 2),
        )

        title = ctk.CTkLabel(
            card,
            text="Drop your photos here",
            font=ctk.CTkFont(
                family="Arial",
                size=17,
                weight="bold",
            ),
            text_color=self.TEXT,
        )
        title.grid(row=1, column=0)

        subtitle = ctk.CTkLabel(
            card,
            text="or choose photos from your Mac",
            font=ctk.CTkFont(
                family="Arial",
                size=12,
            ),
            text_color=self.SECONDARY_TEXT,
        )
        subtitle.grid(
            row=2,
            column=0,
            pady=(2, 12),
        )

        choose_button = ctk.CTkButton(
            card,
            text="Choose Photos",
            width=150,
            height=38,
            corner_radius=10,
            fg_color=self.ACCENT,
            hover_color=self.ACCENT_HOVER,
            command=self.choose_photos,
        )
        choose_button.grid(
            row=3,
            column=0,
            pady=(0, 18),
        )

        self.drop_card = card

    # ----------------------------------------------------------------------
    # Preset controls
    # ----------------------------------------------------------------------

    def _build_preset_card(self, parent):
        """Build the theme and preset selection card."""

        card = ctk.CTkFrame(
            parent,
            fg_color=self.CARD,
            corner_radius=self.RADIUS,
            border_width=1,
            border_color=self.CARD_BORDER,
        )
        card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(8, 0),
        )

        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        heading = ctk.CTkLabel(
            card,
            text="Choose your look",
            font=ctk.CTkFont(
                family="Arial",
                size=17,
                weight="bold",
            ),
            text_color=self.TEXT,
        )
        heading.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            padx=20,
            pady=(18, 14),
        )

        theme_label = ctk.CTkLabel(
            card,
            text="THEME",
            font=ctk.CTkFont(
                family="Arial",
                size=10,
                weight="bold",
            ),
            text_color=self.MUTED_TEXT,
        )
        theme_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=(20, 8),
        )

        preset_label = ctk.CTkLabel(
            card,
            text="PRESET",
            font=ctk.CTkFont(
                family="Arial",
                size=10,
                weight="bold",
            ),
            text_color=self.MUTED_TEXT,
        )
        preset_label.grid(
            row=1,
            column=1,
            sticky="w",
            padx=(8, 20),
        )

        categories = get_preset_categories()

        self.theme_menu = ctk.CTkOptionMenu(
            card,
            values=categories,
            height=40,
            corner_radius=10,
            fg_color="#F2F3F5",
            button_color="#E6E8EC",
            button_hover_color="#DDE0E5",
            text_color=self.TEXT,
            dropdown_fg_color="#FFFFFF",
            dropdown_hover_color="#EEF2FF",
            dropdown_text_color=self.TEXT,
            command=self._theme_changed,
        )
        self.theme_menu.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=(20, 8),
            pady=(6, 18),
        )

        initial_category = categories[0] if categories else ""

        presets = get_presets_for_category(initial_category)

        self.preset_menu = ctk.CTkOptionMenu(
            card,
            values=presets,
            height=40,
            corner_radius=10,
            fg_color="#F2F3F5",
            button_color="#E6E8EC",
            button_hover_color="#DDE0E5",
            text_color=self.TEXT,
            dropdown_fg_color="#FFFFFF",
            dropdown_hover_color="#EEF2FF",
            dropdown_text_color=self.TEXT,
            command=self._preset_changed,
        )
        self.preset_menu.grid(
            row=2,
            column=1,
            sticky="ew",
            padx=(8, 20),
            pady=(6, 18),
        )

        if categories:
            self.theme_menu.set(categories[0])

        if presets:
            self.preset_menu.set(presets[0])

    # ----------------------------------------------------------------------
    # Preview area
    # ----------------------------------------------------------------------

    def _build_preview(self):
        """Build the BEFORE and AFTER preview section."""

        preview_section = ctk.CTkFrame(
            self.main,
            fg_color="transparent",
        )
        preview_section.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=48,
            pady=(8, 8),
        )

        preview_section.grid_columnconfigure(0, weight=1)
        preview_section.grid_columnconfigure(1, weight=1)
        preview_section.grid_rowconfigure(1, weight=1)

        heading = ctk.CTkFrame(
            preview_section,
            fg_color="transparent",
        )
        heading.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, 8),
        )

        heading.grid_columnconfigure(0, weight=1)

        preview_title = ctk.CTkLabel(
            heading,
            text="Preview",
            font=ctk.CTkFont(
                family="Arial",
                size=17,
                weight="bold",
            ),
            text_color=self.TEXT,
        )
        preview_title.grid(row=0, column=0, sticky="w")

        self.photo_count_label = ctk.CTkLabel(
            heading,
            text="No photos added",
            font=ctk.CTkFont(
                family="Arial",
                size=12,
            ),
            text_color=self.SECONDARY_TEXT,
        )
        self.photo_count_label.grid(row=0, column=1, sticky="e")

        self.before_card = self._create_preview_card(
            preview_section,
            "BEFORE",
            0,
        )

        self.after_card = self._create_preview_card(
            preview_section,
            "AFTER",
            1,
        )

    def _create_preview_card(self, parent, label_text, column):
        """Create one preview card."""

        card = ctk.CTkFrame(
            parent,
            fg_color=self.CARD,
            corner_radius=self.RADIUS,
            border_width=1,
            border_color=self.CARD_BORDER,
        )
        card.grid(
            row=1,
            column=column,
            sticky="nsew",
            padx=(0, 6) if column == 0 else (6, 0),
        )

        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        label = ctk.CTkLabel(
            card,
            text=label_text,
            font=ctk.CTkFont(
                family="Arial",
                size=10,
                weight="bold",
            ),
            text_color=self.MUTED_TEXT,
        )
        label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=18,
            pady=(14, 8),
        )

        image_label = ctk.CTkLabel(
            card,
            text="Add a photo to see a preview",
            font=ctk.CTkFont(
                family="Arial",
                size=13,
            ),
            text_color=self.MUTED_TEXT,
        )
        image_label.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=16,
            pady=(0, 16),
        )

        return {
            "card": card,
            "image": image_label,
        }

    # ----------------------------------------------------------------------
    # Bottom action bar
    # ----------------------------------------------------------------------

    def _build_bottom_bar(self):
        """Build the export controls and main edit button."""

        bar = ctk.CTkFrame(
            self.main,
            fg_color=self.CARD,
            corner_radius=0,
            border_width=1,
            border_color=self.CARD_BORDER,
        )
        bar.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )

        bar.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(
            bar,
            fg_color="transparent",
        )
        left.grid(
            row=0,
            column=0,
            sticky="w",
            padx=48,
            pady=16,
        )

        self.output_label = ctk.CTkLabel(
            left,
            text="Output: Pictures/Luma",
            font=ctk.CTkFont(
                family="Arial",
                size=12,
            ),
            text_color=self.SECONDARY_TEXT,
        )
        self.output_label.pack(side="left")

        output_button = ctk.CTkButton(
            left,
            text="Change",
            width=72,
            height=30,
            corner_radius=8,
            fg_color="#F1F2F4",
            hover_color="#E6E8EC",
            text_color=self.TEXT,
            command=self.choose_output_folder,
        )
        output_button.pack(
            side="left",
            padx=(10, 0),
        )

        self.progress = ctk.CTkProgressBar(
            bar,
            width=180,
            height=8,
            corner_radius=5,
            progress_color=self.ACCENT,
        )
        self.progress.set(0)
        self.progress.grid(
            row=0,
            column=1,
            padx=(10, 18),
        )

        self.status_label = ctk.CTkLabel(
            bar,
            text="Ready",
            font=ctk.CTkFont(
                family="Arial",
                size=12,
            ),
            text_color=self.SECONDARY_TEXT,
        )
        self.status_label.grid(
            row=0,
            column=2,
            padx=(0, 18),
        )

        self.edit_button = ctk.CTkButton(
            bar,
            text="EDIT PHOTOS",
            width=170,
            height=46,
            corner_radius=13,
            fg_color=self.ACCENT,
            hover_color=self.ACCENT_HOVER,
            font=ctk.CTkFont(
                family="Arial",
                size=13,
                weight="bold",
            ),
            command=self.start_processing,
        )
        self.edit_button.grid(
            row=0,
            column=3,
            padx=(0, 48),
            pady=10,
        )

        self._update_output_label()

    # ----------------------------------------------------------------------
    # Drag and drop
    # ----------------------------------------------------------------------

    def _setup_drag_and_drop(self):
        """Register the application as a native file drop target."""

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind(
            "<<Drop>>",
            self._handle_drop,
        )

    def _handle_drop(self, event):
        """Handle files dragged onto the Luma window."""

        paths = self.root.tk.splitlist(event.data)

        self._add_photo_paths(
            [Path(path) for path in paths]
        )

    # ----------------------------------------------------------------------
    # Photo selection
    # ----------------------------------------------------------------------

    def choose_photos(self):
        """Open the native macOS photo picker."""

        paths = filedialog.askopenfilenames(
            title="Choose photos",
            filetypes=[
                (
                    "Images",
                    "*.jpg *.jpeg *.png *.webp",
                ),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("WebP", "*.webp"),
            ],
        )

        if paths:
            self._add_photo_paths(
                [Path(path) for path in paths]
            )

    def _add_photo_paths(self, paths: list[Path]):
        """Add supported image files to the current batch."""

        supported = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        }

        added = []

        for path in paths:
            if not path.is_file():
                continue

            if path.suffix.lower() not in supported:
                continue

            if path not in self.photo_paths:
                self.photo_paths.append(path)
                added.append(path)

        if not added:
            return

        # The very first image added becomes the example image.
        if self.example_image_path is None:
            self.example_image_path = added[0]

        self._update_photo_count()
        self._show_before_preview()
        self._generate_preview()

    # ----------------------------------------------------------------------
    # Photo clearing
    # ----------------------------------------------------------------------

    def clear_photos(self):
        """Remove all photos from the current batch."""

        if self.processing:
            return

        self.photo_paths.clear()
        self.example_image_path = None

        self.before_card["image"].configure(
            image=None,
            text="Add a photo to see a preview",
        )

        self.after_card["image"].configure(
            image=None,
            text="Add a photo to see a preview",
        )

        self.preview_photo_before = None
        self.preview_photo_after = None

        self._update_photo_count()
        self._set_status("Ready")

    # ----------------------------------------------------------------------
    # Preset changes
    # ----------------------------------------------------------------------

    def _theme_changed(self, category: str):
        """Update the preset dropdown when the theme changes."""

        presets = get_presets_for_category(category)

        if not presets:
            self.preset_menu.configure(values=[])
            return

        self.preset_menu.configure(values=presets)
        self.preset_menu.set(presets[0])

        self._generate_preview()

    def _preset_changed(self, _preset_name: str):
        """Regenerate the example preview after changing preset."""

        self._generate_preview()

    # ----------------------------------------------------------------------
    # Preview generation
    # ----------------------------------------------------------------------

    def _show_before_preview(self):
        """Display the first added image in the BEFORE panel."""

        if self.example_image_path is None:
            return

        try:
            with Image.open(self.example_image_path) as image:
                image = ImageOps.exif_transpose(image)
                image = image.convert("RGB")

                preview = self._fit_image(
                    image,
                    470,
                    280,
                )

                self.preview_photo_before = ImageTk.PhotoImage(preview)

                self.before_card["image"].configure(
                    image=self.preview_photo_before,
                    text="",
                )

        except Exception as error:
            self.before_card["image"].configure(
                image=None,
                text=f"Unable to preview image\n{error}",
            )

    def _generate_preview(self):
        """Generate the AFTER preview in a background thread."""

        if self.example_image_path is None:
            return

        preset_name = self.preset_menu.get()
        preset = get_preset_by_name(preset_name)

        if preset is None:
            return

        # Incrementing the token means an older preview cannot overwrite
        # a newer preview if the user changes presets quickly.
        self.current_preview_token += 1
        token = self.current_preview_token

        self._set_status("Generating preview...")

        thread = threading.Thread(
            target=self._preview_worker,
            args=(
                self.example_image_path,
                preset,
                token,
            ),
            daemon=True,
        )
        thread.start()

    def _preview_worker(self, image_path, preset, token):
        """Process the example image away from the GUI thread."""

        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=image_path.suffix,
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)

            process_image(
                image_path,
                temp_path,
                preset.settings,
            )

            with Image.open(temp_path) as image:
                image = ImageOps.exif_transpose(image)
                image = image.convert("RGB")

                preview = self._fit_image(
                    image,
                    470,
                    280,
                )

                photo = ImageTk.PhotoImage(preview)

            self.root.after(
                0,
                lambda: self._apply_preview(
                    photo,
                    token,
                ),
            )

        except Exception as error:
            self.root.after(
                0,
                lambda: self._preview_failed(
                    error,
                    token,
                ),
            )

        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    def _apply_preview(self, photo, token):
        """Apply a preview only if it is still the latest request."""

        if token != self.current_preview_token:
            return

        self.preview_photo_after = photo

        self.after_card["image"].configure(
            image=self.preview_photo_after,
            text="",
        )

        self._set_status("Ready")

    def _preview_failed(self, error, token):
        """Display a preview error if it belongs to the latest request."""

        if token != self.current_preview_token:
            return

        self.after_card["image"].configure(
            image=None,
            text=f"Preview unavailable\n{error}",
        )

        self._set_status("Preview failed")

    # ----------------------------------------------------------------------
    # Image sizing
    # ----------------------------------------------------------------------

    @staticmethod
    def _fit_image(image: Image.Image, max_width: int, max_height: int):
        """Resize an image to fit inside the preview without distortion."""

        preview = image.copy()
        preview.thumbnail(
            (max_width, max_height),
            Image.Resampling.LANCZOS,
        )

        canvas = Image.new(
            "RGB",
            (max_width, max_height),
            "#F1F2F4",
        )

        x = (max_width - preview.width) // 2
        y = (max_height - preview.height) // 2

        canvas.paste(
            preview,
            (x, y),
        )

        return canvas

    # ----------------------------------------------------------------------
    # Output location
    # ----------------------------------------------------------------------

    def choose_output_folder(self):
        """Choose the parent directory for Luma exports."""

        folder = filedialog.askdirectory(
            title="Choose Luma output location",
        )

        if not folder:
            return

        self.default_output_root = Path(folder)
        self._update_output_label()

    def _update_output_label(self):
        """Update the small output location label."""

        try:
            display = self.default_output_root.relative_to(
                Path.home()
            )
            display_text = f"Output: ~/{display}"
        except ValueError:
            display_text = f"Output: {self.default_output_root}"

        self.output_label.configure(
            text=display_text,
        )

    # ----------------------------------------------------------------------
    # Export folder creation
    # ----------------------------------------------------------------------

    def _create_export_folder(self, preset_name: str, quantity: int) -> Path:
        """
        Create the folder for one Luma export.

        Format:
            number_preset_images_HH-MM_DD-MM-YY

        Example:
            12_cinematic_images_01-23_21-09-26

        If a folder with the same name already exists, a numeric suffix
        is added so existing exports are never overwritten.
        """

        luma_output = (
            self.default_output_root / "Luma_Output"
        )

        luma_output.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%H-%M_%d-%m-%y"
        )

        clean_preset = (
            preset_name
            .lower()
            .replace(" ", "-")
            .replace("/", "-")
        )

        base_name = (
            f"{quantity}_{clean_preset}_images_{timestamp}"
        )

        folder = luma_output / base_name

        counter = 2

        while folder.exists():
            folder = luma_output / f"{base_name}_{counter}"
            counter += 1

        folder.mkdir(
            parents=True,
            exist_ok=False,
        )

        return folder

    # ----------------------------------------------------------------------
    # Processing
    # ----------------------------------------------------------------------

    def start_processing(self):
        """Start processing the current photo batch."""

        if self.processing:
            return

        if not self.photo_paths:
            messagebox.showinfo(
                "No photos",
                "Add at least one photo before editing.",
            )
            return

        preset_name = self.preset_menu.get()
        preset = get_preset_by_name(preset_name)

        if preset is None:
            messagebox.showerror(
                "Preset error",
                "The selected preset could not be found.",
            )
            return

        self.processing = True
        self.edit_button.configure(
            text="EDITING...",
            state="disabled",
        )

        self.progress.set(0)

        self._set_status(
            f"Preparing {len(self.photo_paths)} photos..."
        )

        thread = threading.Thread(
            target=self._processing_worker,
            args=(
                list(self.photo_paths),
                preset_name,
                preset.settings,
            ),
            daemon=True,
        )
        thread.start()

    def _processing_worker(
        self,
        photo_paths: list[Path],
        preset_name: str,
        settings: dict,
    ):
        """Process the entire batch in a background thread."""

        successful = 0
        failed = 0

        try:
            output_folder = self._create_export_folder(
                preset_name,
                len(photo_paths),
            )

            total = len(photo_paths)

            for index, input_path in enumerate(photo_paths, start=1):

                output_path = (
                    output_folder / input_path.name
                )

                # Avoid accidentally overwriting a file if two selected
                # images have the same filename from different folders.
                output_path = self._unique_file_path(
                    output_path
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

                    print(
                        f"Failed to process "
                        f"{input_path}: {error}"
                    )

                progress = index / total

                self.root.after(
                    0,
                    lambda p=progress, i=index, t=total:
                    self._update_processing_progress(
                        p,
                        i,
                        t,
                    ),
                )

            self.last_output_folder = output_folder

            self.root.after(
                0,
                lambda: self._processing_finished(
                    output_folder,
                    successful,
                    failed,
                ),
            )

        except Exception as error:
            self.root.after(
                0,
                lambda: self._processing_error(error),
            )

    @staticmethod
    def _unique_file_path(path: Path) -> Path:
        """Return a non-conflicting output path."""

        if not path.exists():
            return path

        counter = 2

        while True:
            candidate = (
                path.parent
                / f"{path.stem}_{counter}{path.suffix}"
            )

            if not candidate.exists():
                return candidate

            counter += 1

    def _update_processing_progress(
        self,
        progress: float,
        current: int,
        total: int,
    ):
        """Update the progress bar safely on the GUI thread."""

        self.progress.set(progress)

        self._set_status(
            f"Editing {current} of {total}..."
        )

    def _processing_finished(
        self,
        output_folder: Path,
        successful: int,
        failed: int,
    ):
        """Handle successful completion of a batch."""

        self.processing = False

        self.edit_button.configure(
            text="EDIT PHOTOS",
            state="normal",
        )

        self.progress.set(1)

        if failed == 0:
            self._set_status(
                f"{successful} photos edited"
            )
        else:
            self._set_status(
                f"{successful} edited, {failed} failed"
            )

        message = (
            f"{successful} photo"
            f"{'s' if successful != 1 else ''} edited successfully."
        )

        if failed:
            message += (
                f"\n\n{failed} photo"
                f"{'s' if failed != 1 else ''} failed."
            )

        message += (
            f"\n\nSaved to:\n{output_folder}"
        )

        answer = messagebox.askyesno(
            "Luma finished",
            message + "\n\nOpen the output folder?",
        )

        if answer:
            self.open_output_folder()

    def _processing_error(self, error):
        """Handle an error that prevented the batch from starting."""

        self.processing = False

        self.edit_button.configure(
            text="EDIT PHOTOS",
            state="normal",
        )

        self.progress.set(0)
        self._set_status("Export failed")

        messagebox.showerror(
            "Luma export failed",
            str(error),
        )

    # ----------------------------------------------------------------------
    # Output opening
    # ----------------------------------------------------------------------

    def open_output_folder(self):
        """Open the most recent Luma export folder in Finder."""

        if self.last_output_folder is None:
            return

        try:
            import subprocess

            subprocess.run(
                [
                    "open",
                    str(self.last_output_folder),
                ],
                check=False,
            )

        except Exception as error:
            messagebox.showerror(
                "Unable to open folder",
                str(error),
            )

    # ----------------------------------------------------------------------
    # Status
    # ----------------------------------------------------------------------

    def _set_status(self, text: str):
        """Update the status label."""

        self.status_label.configure(
            text=text,
        )

    def _update_photo_count(self):
        """Update the number of photos currently selected."""

        count = len(self.photo_paths)

        if count == 0:
            text = "No photos added"
        elif count == 1:
            text = "1 photo added"
        else:
            text = f"{count} photos added"

        self.photo_count_label.configure(
            text=text,
        )

    # ----------------------------------------------------------------------
    # Application start
    # ----------------------------------------------------------------------

    def run(self):
        """Start the Luma event loop."""

        self.root.mainloop()


def main():
    """Application entry point."""

    app = LumaApp()
    app.run()


if __name__ == "__main__":
    main()