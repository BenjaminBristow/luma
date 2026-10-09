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

BG = "#11141A"
SIDEBAR = "#171A21"
PANEL = "#1B1F28"
BORDER = "#2B3240"
TEXT = "#F2F4F7"
SECONDARY_TEXT = "#9AA2B1"
MUTED_TEXT = "#687182"

ACCENT = "#6C8CFF"
ACCENT_HOVER = "#5879EE"
HOVER_BORDER = "#777F8D"

SUCCESS = "#55C98A"
ERROR = "#F06A6A"

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


# ---------------------------------------------------------------------------
# Platform helpers
# ---------------------------------------------------------------------------

def get_pictures_folder() -> Path:
    home = Path.home()
    if sys.platform == "win32":
        pictures = Path(os.environ.get("USERPROFILE", str(home))) / "Pictures"
    else:
        pictures = home / "Pictures"
    return pictures if pictures.exists() else home


def get_settings_folder() -> Path:
    home = Path.home()
    if sys.platform == "win32":
        app_data = os.environ.get("APPDATA")
        return Path(app_data) / "Luma" if app_data else home / "AppData" / "Roaming" / "Luma"
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "Luma"
    return home / ".config" / "luma"


# ---------------------------------------------------------------------------
# Preset helpers
# ---------------------------------------------------------------------------

def get_preset_categories() -> list[str]:
    return sorted({preset.category for preset in PRESETS.values()})


def get_presets_for_category(category: str) -> list[str]:
    return [preset.name for preset in PRESETS.values() if preset.category == category]


def get_preset_by_name(name: str):
    for preset in PRESETS.values():
        if preset.name == name:
            return preset
    return None


def display_name(name: str) -> str:
    return name.replace("-", " ").replace("_", " ").title()


class LumaApp:
    """Luma photo editor with a centred, animated folder carousel."""

    def __init__(self, root):
        self.root = root
        self.root.title("Luma")
        self.root.geometry("1450x900")
        self.root.minsize(1180, 760)
        self.root.configure(bg=BG)

        self.luma_root = get_pictures_folder() / "Luma"
        self.default_input_folder = self.luma_root / "Luma_Input"
        self.output_folder = self.luma_root / "Luma_Output"
        self.default_input_folder.mkdir(parents=True, exist_ok=True)
        self.output_folder.mkdir(parents=True, exist_ok=True)

        self.input_folder = self._load_saved_input_folder()
        if not self.input_folder.exists():
            self.input_folder = self.default_input_folder
        self.input_folder.mkdir(parents=True, exist_ok=True)

        self.photo_paths: list[Path] = []
        self.example_image_path: Path | None = None
        self.selected_photo_index = 0
        self.hovered_photo_index: int | None = None

        # Carousel animation state.
        self.carousel_position = 0.0
        self.carousel_target = 0.0
        self.carousel_animation_job = None
        self.carousel_redraw_job = None
        self.carousel_dragging = False
        self.carousel_drag_start_x = 0
        self.carousel_drag_start_position = 0.0
        self.carousel_photo_refs: list[ImageTk.PhotoImage] = []
        self.carousel_source_cache = {}
        self.carousel_items: dict[int, tuple[float, float, float, float, float]] = {}
        self.carousel_mouse_over = False

        # Before/after comparison state. This is deliberately separate from
        # the moving carousel so the comparison never moves while browsing.
        self.preview_before_image: Image.Image | None = None
        self.preview_after_image: Image.Image | None = None
        self.preview_divider = 0.5
        self.preview_dragging = False
        self.preview_resize_job = None
        self.preview_canvas_photo_before = None
        self.preview_canvas_photo_after = None
        self.current_preview_token = 0

        # General state.
        self.processing = False
        self.last_output_folder: Path | None = None
        self.category_map: dict[str, str] = {}
        self.preset_map: dict[str, str] = {}
        self.selected_preset_name: str | None = None
        self.folder_signature: tuple = ()
        self.sync_running = False
        self.preset_mouse_over = False

        self._configure_appearance()
        self._build_interface()

        if DND_AVAILABLE:
            self._setup_drag_and_drop()

        self.load_input_folder()
        self._schedule_folder_sync()

    # ------------------------------------------------------------------
    # Appearance
    # ------------------------------------------------------------------

    def _configure_appearance(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

    def _font(self, size, weight="normal"):
        return ctk.CTkFont(family="Arial", size=size, weight=weight)

    def _card(self, parent, **kwargs):
        return ctk.CTkFrame(
            parent,
            fg_color=PANEL,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------

    def _build_interface(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        shell = ctk.CTkFrame(self.root, fg_color=BG, corner_radius=0)
        shell.grid(row=0, column=0, sticky="nsew")
        shell.grid_rowconfigure(0, weight=1)
        shell.grid_columnconfigure(1, weight=1)

        self._build_sidebar(shell)

        main = ctk.CTkFrame(shell, fg_color=BG, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        self._build_topbar(main)
        self._build_workspace(main)
        self._build_status_bar(main)

    def _build_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, width=220, fg_color=SIDEBAR, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(5, weight=1)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=22, pady=(28, 34))
        ctk.CTkLabel(
            brand, text="L", width=38, height=38, corner_radius=11,
            fg_color=ACCENT, text_color="#FFFFFF", font=self._font(21, "bold")
        ).grid(row=0, column=0)
        ctk.CTkLabel(
            brand, text="LUMA", text_color=TEXT, font=self._font(20, "bold")
        ).grid(row=0, column=1, padx=(11, 0), sticky="w")

        self._nav_button(sidebar, "⌂   Home", 1, active=True)
        self._nav_button(sidebar, "✦   Presets", 2)
        self._nav_button(sidebar, "⚙   Settings", 3)
        self._nav_button(sidebar, "ⓘ   About", 4)

        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.grid(row=6, column=0, sticky="ew", padx=22, pady=22)
        ctk.CTkLabel(footer, text="PHOTO WORKFLOW", text_color=MUTED_TEXT,
                     font=self._font(10, "bold")).pack(anchor="w")
        ctk.CTkLabel(footer, text="Fast • Simple • Local", text_color=SECONDARY_TEXT,
                     font=self._font(11)).pack(anchor="w", pady=(4, 0))

    def _nav_button(self, parent, text, row, active=False):
        button = ctk.CTkButton(
            parent, text=text, anchor="w", height=42, corner_radius=10,
            fg_color="#222733" if active else "transparent",
            hover_color="#252B38", text_color=TEXT if active else SECONDARY_TEXT,
            font=self._font(13, "bold" if active else "normal"), command=lambda: None,
        )
        button.grid(row=row, column=0, sticky="ew", padx=14, pady=3)

    def _build_topbar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", pady=(2, 16))
        bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(bar, text="Photo workspace", text_color=TEXT,
                     font=self._font(25, "bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(bar, text="Browse your input folder and edit any photo with Luma presets",
                     text_color=SECONDARY_TEXT, font=self._font(12)).grid(row=1, column=0,
                                                                            sticky="w", pady=(3, 0))

        self.clear_button = ctk.CTkButton(
            bar, text="Clear batch", width=110, height=36, corner_radius=9,
            fg_color=PANEL, hover_color="#252B38", border_width=1,
            border_color=BORDER, text_color=TEXT, command=self.clear_photos,
        )
        self.clear_button.grid(row=0, column=1, rowspan=2, sticky="e")

    def _build_workspace(self, parent):
        workspace = ctk.CTkFrame(parent, fg_color="transparent")
        workspace.grid(row=1, column=0, sticky="nsew")
        workspace.grid_columnconfigure(0, weight=1, minsize=700)
        workspace.grid_columnconfigure(1, weight=0, minsize=355)
        workspace.grid_rowconfigure(0, weight=0)
        workspace.grid_rowconfigure(1, weight=1)
        workspace.grid_rowconfigure(2, weight=0, minsize=170)

        left = ctk.CTkFrame(workspace, fg_color="transparent")
        left.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(0, 10))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=0)
        left.grid_rowconfigure(1, weight=1)
        left.grid_rowconfigure(2, weight=0, minsize=170)

        right = ctk.CTkFrame(workspace, fg_color="transparent")
        right.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=(10, 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        self._build_import_panel(left)

        # The preview fills all of the vertical space between the import panel
        # and the carousel. The preset column and carousel share the same bottom.
        self._build_comparison_panel(left)
        self._build_carousel_panel(left)
        self._build_preset_panel(right)

    def _build_import_panel(self, parent):
        card = self._card(parent)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="INPUT FOLDER", text_color=MUTED_TEXT,
                     font=self._font(10, "bold")).grid(row=0, column=0, columnspan=2,
                                                        sticky="w", padx=18, pady=(15, 3))
        self.input_folder_name_label = ctk.CTkLabel(card, text=self.input_folder.name,
                                                     text_color=TEXT, font=self._font(15, "bold"))
        self.input_folder_name_label.grid(row=1, column=0, sticky="w", padx=18)
        self.input_folder_path_label = ctk.CTkLabel(card, text=self._shorten_path(self.input_folder),
                                                     text_color=SECONDARY_TEXT, font=self._font(10))
        self.input_folder_path_label.grid(row=2, column=0, sticky="w", padx=18, pady=(1, 14))

        self.folder_watch_label = ctk.CTkLabel(card, text="●  Watching folder", text_color=SUCCESS,
                                               font=self._font(11, "bold"))
        self.folder_watch_label.grid(row=1, column=1, sticky="e", padx=18)

        self.change_folder_button = ctk.CTkButton(
            card, text="Change folder", width=125, height=34, corner_radius=9,
            fg_color="#252B38", hover_color="#2D3442", border_width=1, border_color=BORDER,
            text_color=TEXT, command=self.choose_folder,
        )
        self.change_folder_button.grid(row=2, column=1, sticky="e", padx=18, pady=(0, 14))

    # ------------------------------------------------------------------
    # Carousel
    # ------------------------------------------------------------------

    def _build_carousel_panel(self, parent):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        wrapper.grid_columnconfigure(1, weight=1)
        wrapper.grid_rowconfigure(1, weight=1)

        heading = ctk.CTkFrame(wrapper, fg_color="transparent")
        heading.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 6))
        heading.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(heading, text="PHOTOS", text_color=MUTED_TEXT,
                     font=self._font(10, "bold")).grid(row=0, column=0, sticky="w")
        self.carousel_hint_label = ctk.CTkLabel(
            heading, text="Scroll, drag, or use the arrows", text_color=SECONDARY_TEXT,
            font=self._font(10)
        )
        self.carousel_hint_label.grid(row=0, column=1, sticky="e")

        self.carousel_left_button = ctk.CTkButton(
            wrapper, text="‹", width=34, height=112, corner_radius=10,
            fg_color=PANEL, hover_color="#252B38", border_width=1, border_color=BORDER,
            text_color=TEXT, font=self._font(24), command=lambda: self._move_carousel(-1)
        )
        self.carousel_left_button.grid(row=1, column=0, sticky="nsw", padx=(0, 6))

        self.carousel_card = self._card(wrapper)
        self.carousel_card.grid(row=1, column=1, sticky="nsew")
        self.carousel_card.grid_rowconfigure(0, weight=1)
        self.carousel_card.grid_columnconfigure(0, weight=1)

        self.carousel_canvas = tk.Canvas(
            self.carousel_card, bg="#0C0F14", highlightthickness=0, bd=0, cursor="hand2",
            height=112
        )
        self.carousel_canvas.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        for sequence in ("<Configure>", "<Enter>", "<Motion>", "<Leave>", "<Button-1>",
                         "<ButtonPress-1>", "<B1-Motion>", "<ButtonRelease-1>"):
            if sequence == "<Configure>":
                self.carousel_canvas.bind(sequence, self._schedule_carousel_redraw)
            elif sequence == "<Enter>":
                self.carousel_canvas.bind(sequence, self._carousel_enter)
            elif sequence == "<Motion>":
                self.carousel_canvas.bind(sequence, self._carousel_motion)
            elif sequence == "<Leave>":
                self.carousel_canvas.bind(sequence, self._carousel_leave)
            elif sequence == "<Button-1>":
                self.carousel_canvas.bind(sequence, self._carousel_click)
            elif sequence == "<ButtonPress-1>":
                self.carousel_canvas.bind(sequence, self._carousel_drag_start)
            elif sequence == "<B1-Motion>":
                self.carousel_canvas.bind(sequence, self._carousel_drag_move)
            elif sequence == "<ButtonRelease-1>":
                self.carousel_canvas.bind(sequence, self._carousel_drag_end)

        self.carousel_right_button = ctk.CTkButton(
            wrapper, text="›", width=34, height=112, corner_radius=10,
            fg_color=PANEL, hover_color="#252B38", border_width=1, border_color=BORDER,
            text_color=TEXT, font=self._font(24), command=lambda: self._move_carousel(1)
        )
        self.carousel_right_button.grid(row=1, column=2, sticky="nse", padx=(6, 0))

        footer = ctk.CTkFrame(wrapper, fg_color="transparent")
        footer.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(5, 0))
        footer.grid_columnconfigure(0, weight=1)
        self.selected_photo_label = ctk.CTkLabel(
            footer, text="No photos", text_color=SECONDARY_TEXT, font=self._font(10)
        )
        self.selected_photo_label.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            footer, text="Blue = selected   •   Grey = hover", text_color=MUTED_TEXT,
            font=self._font(9)
        ).grid(row=0, column=1, sticky="e")

    def _schedule_carousel_redraw(self, _event=None):
        if self.carousel_redraw_job is not None:
            try:
                self.root.after_cancel(self.carousel_redraw_job)
            except Exception:
                pass
        self.carousel_redraw_job = self.root.after(20, self._redraw_carousel)

    def _carousel_enter(self, _event):
        self.carousel_mouse_over = True

    def _carousel_motion(self, event):
        self.carousel_mouse_over = True
        if not self.photo_paths:
            return

        hovered = None
        for index, item in self.carousel_items.items():
            cx, cy, width, height, opacity = item
            if opacity <= 0.05:
                continue
            if (cx - width / 2 <= event.x <= cx + width / 2 and
                    cy - height / 2 <= event.y <= cy + height / 2):
                hovered = index
                break

        if hovered != self.hovered_photo_index:
            self.hovered_photo_index = hovered
            self._redraw_carousel()

    def _move_carousel(self, direction):
        """Move the carousel by one photo and select the destination."""
        if not self.photo_paths:
            return

        destination = int(round(self.carousel_target)) + int(direction)
        destination = max(0, min(len(self.photo_paths) - 1, destination))
        self._select_photo(destination, animate=True)

    def _select_photo(self, index, animate=True):
        """Select a photo and move it to the centre of the carousel."""
        if not self.photo_paths:
            return

        index = max(0, min(len(self.photo_paths) - 1, int(index)))
        self.selected_photo_index = index
        self.example_image_path = self.photo_paths[index]
        self.hovered_photo_index = None
        self._update_selected_photo_label()
        self._show_before_preview()
        self._generate_preview()

        self.carousel_target = float(index)
        if animate:
            self._animate_carousel()
        else:
            self.carousel_position = float(index)
            self._redraw_carousel()

    def _carousel_mousewheel(self, event):
        if not self.photo_paths:
            return "break"

        if getattr(event, "num", None) == 4:
            movement = -0.65
        elif getattr(event, "num", None) == 5:
            movement = 0.65
        else:
            delta = float(getattr(event, "delta", 0) or 0)
            if delta == 0:
                return "break"

            # macOS trackpads send many small deltas. Use the raw delta but
            # clamp each event so a fast swipe cannot jump the whole folder.
            movement = -(delta / 120.0) * 0.22
            movement = max(-0.65, min(0.65, movement))

            # Make very small trackpad events visible while preserving their
            # direction and smoothness.
            if abs(movement) < 0.025:
                movement = -0.025 if movement < 0 else 0.025

        self.carousel_target = max(
            0.0,
            min(float(len(self.photo_paths) - 1), self.carousel_target + movement),
        )
        self._animate_carousel()
        return "break"

    def _carousel_leave(self, _event):
        self.carousel_mouse_over = False
        if self.hovered_photo_index is not None:
            self.hovered_photo_index = None
            self._redraw_carousel()

    def _carousel_global_wheel(self, event):
        if not self.carousel_mouse_over:
            return
        self._carousel_mousewheel(event)

    def _carousel_click(self, event):
        if not self.photo_paths:
            return
        clicked = None
        for index, item in self.carousel_items.items():
            cx, cy, width, height, opacity = item
            if opacity <= 0.05:
                continue
            if (cx - width / 2 <= event.x <= cx + width / 2 and
                    cy - height / 2 <= event.y <= cy + height / 2):
                clicked = index
                break
        if clicked is not None:
            self._select_photo(clicked, animate=True)

    def _carousel_drag_start(self, event):
        self.carousel_dragging = True
        self.carousel_drag_start_x = event.x
        self.carousel_drag_start_position = self.carousel_position

    def _carousel_drag_move(self, event):
        if not self.carousel_dragging or not self.photo_paths:
            return
        dx = event.x - self.carousel_drag_start_x
        canvas_width = max(1, self.carousel_canvas.winfo_width())
        step_pixels = max(100, min(180, canvas_width * 0.13))
        position = self.carousel_drag_start_position - dx / step_pixels
        position = max(0.0, min(len(self.photo_paths) - 1, position))
        self.carousel_position = position
        nearest = int(round(position))
        self.selected_photo_index = nearest
        self.example_image_path = self.photo_paths[nearest]
        self.carousel_target = float(nearest)
        self._update_selected_photo_label()
        self._redraw_carousel()

    def _carousel_drag_end(self, _event):
        if not self.carousel_dragging:
            return
        self.carousel_dragging = False
        if self.photo_paths:
            nearest = int(round(self.carousel_position))
            self._select_photo(nearest, animate=True)

    def _redraw_carousel(self):
        self.carousel_redraw_job = None
        canvas = self.carousel_canvas
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 2 or height <= 2:
            return

        canvas.delete("all")
        self.carousel_photo_refs.clear()
        self.carousel_items.clear()

        if not self.photo_paths:
            canvas.create_text(width / 2, height / 2 - 8, text="No photos in this folder",
                               fill=MUTED_TEXT, font=("Arial", 11))
            canvas.create_text(width / 2, height / 2 + 14, text="Add images or choose another folder",
                               fill="#4F5663", font=("Arial", 9))
            return

        centre_x = width / 2
        centre_y = height / 2
        max_visible_distance = 4.5
        spacing = max(72.0, min(125.0, width * 0.14))
        base_width = 145
        base_height = 92

        visible = []
        for index in range(len(self.photo_paths)):
            distance = index - self.carousel_position
            if abs(distance) <= max_visible_distance:
                visible.append((index, distance))
        visible.sort(key=lambda item: abs(item[1]), reverse=True)

        for index, distance in visible:
            abs_distance = abs(distance)
            t = max(0.0, min(1.0, abs_distance / max_visible_distance))
            smooth = t * t * (3.0 - 2.0 * t)
            scale = 1.0 - 0.48 * smooth
            opacity = 1.0 - 0.82 * smooth

            thumb_w = max(38, int(base_width * scale))
            thumb_h = max(28, int(base_height * scale))
            x = centre_x + distance * spacing
            y = centre_y

            if x + thumb_w / 2 < 0 or x - thumb_w / 2 > width:
                continue

            image = self._get_cached_carousel_image(self.photo_paths[index], thumb_w, thumb_h, opacity)
            if image is None:
                continue
            photo = ImageTk.PhotoImage(image)
            self.carousel_photo_refs.append(photo)
            canvas.create_image(x, y, image=photo, anchor="center")

            border = None
            border_width = 0
            if index == self.selected_photo_index:
                border = ACCENT
                border_width = 3
            elif index == self.hovered_photo_index:
                border = HOVER_BORDER
                border_width = 2
            if border:
                pad = 4
                canvas.create_rectangle(
                    x - thumb_w / 2 - pad, y - thumb_h / 2 - pad,
                    x + thumb_w / 2 + pad, y + thumb_h / 2 + pad,
                    outline=border, width=border_width
                )

            self.carousel_items[index] = (x, y, thumb_w, thumb_h, opacity)

        # Small centre marker, not a full-height line.
        canvas.create_line(centre_x - 7, height - 5, centre_x + 7, height - 5,
                           fill=ACCENT, width=2)

    def _get_cached_carousel_image(self, path: Path, width: int, height: int, opacity: float):
        # Cache one reasonably sized source thumbnail per file. The old GUI
        # reopened every file from disk on every animation frame, which caused
        # the laggy carousel.
        if not hasattr(self, "carousel_source_cache"):
            self.carousel_source_cache = {}

        key = str(path)
        cached = self.carousel_source_cache.get(key)
        try:
            mtime = path.stat().st_mtime_ns
        except OSError:
            return None

        if cached is None or cached[0] != mtime:
            try:
                with Image.open(path) as source:
                    image = ImageOps.exif_transpose(source).convert("RGB")
                    image.thumbnail((220, 150), Image.Resampling.LANCZOS)
                    cached_image = image.copy()
                self.carousel_source_cache[key] = (mtime, cached_image)
                cached = (mtime, cached_image)
            except (OSError, ValueError):
                return None

        source = cached[1]
        resized = source.copy()
        resized.thumbnail((max(1, width), max(1, height)), Image.Resampling.LANCZOS)
        canvas_image = Image.new("RGBA", (width, height), (12, 15, 20, 0))
        x = (width - resized.width) // 2
        y = (height - resized.height) // 2
        canvas_image.paste(resized.convert("RGBA"), (x, y))
        if opacity < 0.999:
            alpha = canvas_image.getchannel("A").point(lambda value: int(value * opacity))
            canvas_image.putalpha(alpha)
        return canvas_image

    def _update_selected_photo_label(self):
        if not self.photo_paths:
            self.selected_photo_label.configure(text="No photos")
            return
        path = self.photo_paths[self.selected_photo_index]
        self.selected_photo_label.configure(
            text=f"Photo {self.selected_photo_index + 1} of {len(self.photo_paths)}  •  {path.name}"
        )

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------

    def _build_preset_panel(self, parent):
        card = self._card(parent)
        card.grid(row=0, column=0, sticky="nsew")
        card.grid_rowconfigure(3, weight=1)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="PRESETS", text_color=MUTED_TEXT,
                     font=self._font(10, "bold")).grid(row=0, column=0, sticky="w", padx=18, pady=(15, 3))
        ctk.CTkLabel(card, text="Choose your look", text_color=TEXT,
                     font=self._font(18, "bold")).grid(row=1, column=0, sticky="w", padx=18)

        categories = get_preset_categories()
        category_values = [display_name(x) for x in categories]
        self.category_map = dict(zip(category_values, categories))

        self.category_menu = ctk.CTkOptionMenu(
            card, values=category_values or ["No categories"], height=38, corner_radius=9,
            fg_color="#252B38", button_color="#303746", button_hover_color="#394253",
            dropdown_fg_color=PANEL, dropdown_hover_color="#252B38", dropdown_text_color=TEXT,
            text_color=TEXT, command=self._category_changed,
        )
        self.category_menu.grid(row=2, column=0, sticky="ew", padx=18, pady=(12, 12))

        self.preset_scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.preset_scroll.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 8))
        self.preset_scroll.grid_columnconfigure(0, weight=1)

        self._populate_preset_cards(categories[0] if categories else "")
        if category_values:
            self.category_menu.set(category_values[0])
        self._setup_preset_trackpad_scrolling()

    def _setup_preset_trackpad_scrolling(self):
        """Install reliable macOS trackpad/mouse-wheel handlers.

        Tkinter's normal bind_all() runs very late in the bind-tag chain and
        can be swallowed by widget/class bindings.  We give the carousel and
        preset scroll area their own bind tags, placed before the normal Tk
        class bindings, so trackpad events reliably reach Luma first.
        """
        self.preset_scroll.bind("<Enter>", lambda _event: self._set_preset_mouse_over(True))
        self.preset_scroll.bind("<Leave>", lambda _event: self._set_preset_mouse_over(False))

        self._install_scroll_bindtag(self.carousel_canvas, "LumaCarouselScroll", self._carousel_mousewheel)

        preset_canvas = getattr(self.preset_scroll, "_parent_canvas", None)
        if preset_canvas is not None:
            self._install_scroll_bindtag(preset_canvas, "LumaPresetScroll", self._preset_mousewheel)

        # Keyboard navigation works even when the canvas itself does not have
        # keyboard focus.  The buttons also call the same movement function.
        self.root.bind_all("<Left>", self._keyboard_carousel_left, add="+")
        self.root.bind_all("<Right>", self._keyboard_carousel_right, add="+")

    def _install_scroll_bindtag(self, widget, tag_name, callback):
        tags = list(widget.bindtags())
        if tag_name not in tags:
            # Put our tag immediately after the widget-specific tag and before
            # Tk's class binding. This prevents class handlers from swallowing
            # macOS trackpad events first.
            tags.insert(1, tag_name)
            widget.bindtags(tuple(tags))
        widget.bind_class(tag_name, "<MouseWheel>", callback)
        widget.bind_class(tag_name, "<Shift-MouseWheel>", callback)
        widget.bind_class(tag_name, "<Button-4>", callback)
        widget.bind_class(tag_name, "<Button-5>", callback)

    def _set_preset_mouse_over(self, value):
        self.preset_mouse_over = value

    def _pointer_over_widget(self, widget):
        try:
            x = self.root.winfo_pointerx()
            y = self.root.winfo_pointery()
            wx = widget.winfo_rootx()
            wy = widget.winfo_rooty()
            return wx <= x < wx + widget.winfo_width() and wy <= y < wy + widget.winfo_height()
        except tk.TclError:
            return False

    def _combined_mousewheel(self, event):
        # Kept as a fallback for any platform/widget that bypasses the custom
        # bind tags. Determine the target from the actual pointer position.
        if self._pointer_over_widget(self.carousel_canvas):
            return self._carousel_mousewheel(event)
        preset_canvas = getattr(self.preset_scroll, "_parent_canvas", None)
        if preset_canvas is not None and self._pointer_over_widget(preset_canvas):
            return self._preset_mousewheel(event)
        return None

    def _keyboard_carousel_left(self, _event=None):
        self._move_carousel(-1)
        return "break"

    def _keyboard_carousel_right(self, _event=None):
        self._move_carousel(1)
        return "break"

    def _preset_mousewheel(self, event):
        canvas = getattr(self.preset_scroll, "_parent_canvas", None)
        if canvas is None:
            return "break"

        if getattr(event, "num", None) == 4:
            steps = -3
        elif getattr(event, "num", None) == 5:
            steps = 3
        else:
            delta = getattr(event, "delta", 0)
            if delta == 0:
                return "break"
            # macOS trackpads can produce tiny deltas. Keep the movement
            # responsive without turning one mouse-wheel notch into a huge jump.
            steps = -max(1, round(abs(delta) / 35)) if delta > 0 else max(1, round(abs(delta) / 35))

        canvas.yview_scroll(steps, "units")
        return "break"

    def _populate_preset_cards(self, category, selected_name=None):
        for child in self.preset_scroll.winfo_children():
            child.destroy()

        self.preset_map = {}
        presets = get_presets_for_category(category)
        if not presets:
            ctk.CTkLabel(self.preset_scroll, text="No presets available", text_color=MUTED_TEXT,
                         font=self._font(12)).grid(row=0, column=0, padx=8, pady=20)
            self.selected_preset_name = None
            return

        selected = selected_name if selected_name in presets else presets[0]
        for preset_name in presets:
            self.preset_map[display_name(preset_name)] = preset_name
            self._add_preset_card(self.preset_scroll, preset_name, preset_name == selected)

        self.selected_preset_name = selected
        self._generate_preview()

    def _add_preset_card(self, parent, preset_name, selected=False):
        card = ctk.CTkFrame(
            parent,
            fg_color="#252B38" if selected else "#1B1F28",
            corner_radius=10,
            border_width=1,
            border_color=ACCENT if selected else BORDER,
            cursor="hand2",
        )
        card.pack(fill="x", padx=2, pady=5)

        var = tk.BooleanVar(value=selected)
        checkbox = ctk.CTkCheckBox(
            card, text="", variable=var, onvalue=True, offvalue=False,
            checkbox_width=19, checkbox_height=19, corner_radius=5,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, border_color="#596274",
            command=lambda name=preset_name, v=var: self._preset_checkbox_changed(name, v),
        )
        checkbox.pack(side="left", padx=(12, 7), pady=10)

        content = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        content.pack(side="left", fill="both", expand=True, pady=7, padx=(0, 10))
        title = ctk.CTkLabel(content, text=display_name(preset_name), text_color=TEXT,
                             font=self._font(12, "bold"), anchor="w", cursor="hand2")
        title.pack(fill="x")
        preset = get_preset_by_name(preset_name)
        description = f"{display_name(preset.category)} preset" if preset else "Apply this Luma look to your photos."
        description_label = ctk.CTkLabel(content, text=description, text_color=SECONDARY_TEXT,
                                         font=self._font(10), anchor="w", cursor="hand2")
        description_label.pack(fill="x", pady=(2, 0))

        for widget in (card, content, title, description_label):
            widget.bind("<Button-1>", lambda _event, name=preset_name: self._select_preset(name))

    def _select_preset(self, preset_name):
        category = self.category_map.get(self.category_menu.get(), "")
        if preset_name not in get_presets_for_category(category):
            return
        self.selected_preset_name = preset_name
        self._populate_preset_cards(category, selected_name=preset_name)

    def _preset_checkbox_changed(self, preset_name, variable):
        if variable.get():
            self._select_preset(preset_name)
        else:
            variable.set(True)

    # ------------------------------------------------------------------
    # Fixed before/after comparison
    # ------------------------------------------------------------------

    def _build_comparison_panel(self, parent):
        card = self._card(parent)
        card.grid(row=1, column=0, sticky="nsew")
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        heading = ctk.CTkFrame(card, fg_color="transparent")
        heading.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 8))
        heading.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(heading, text="BEFORE / AFTER", text_color=MUTED_TEXT,
                     font=self._font(10, "bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(heading, text="Drag divider", text_color=SECONDARY_TEXT,
                     font=self._font(10)).grid(row=0, column=1, sticky="e")

        self.preview_canvas = tk.Canvas(card, bg="#0C0F14", highlightthickness=0, bd=0,
                                        height=430, cursor="sb_h_double_arrow")
        self.preview_canvas.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.preview_canvas.bind("<Configure>", self._schedule_preview_redraw)
        self.preview_canvas.bind("<Button-1>", self._start_preview_drag)
        self.preview_canvas.bind("<B1-Motion>", self._drag_preview_divider)
        self.preview_canvas.bind("<ButtonRelease-1>", self._end_preview_drag)

    def _schedule_preview_redraw(self, _event=None):
        if self.preview_resize_job is not None:
            try:
                self.root.after_cancel(self.preview_resize_job)
            except Exception:
                pass
        self.preview_resize_job = self.root.after(30, self._redraw_preview)

    def _start_preview_drag(self, event):
        if self.preview_canvas.winfo_width() <= 1:
            return
        self.preview_dragging = True
        self._set_preview_divider_from_x(event.x)

    def _drag_preview_divider(self, event):
        if self.preview_dragging:
            self._set_preview_divider_from_x(event.x)

    def _end_preview_drag(self, _event):
        self.preview_dragging = False

    def _set_preview_divider_from_x(self, x):
        width = max(1, self.preview_canvas.winfo_width())
        # Hard clamp to the actual canvas bounds. The divider can never drag
        # beyond the image/preview and therefore can never drag the image with it.
        self.preview_divider = max(0.0, min(1.0, x / width))
        self._redraw_preview()

    def _redraw_preview(self):
        self.preview_resize_job = None
        canvas = self.preview_canvas
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 2 or height <= 2:
            return

        canvas.delete("all")

        if self.preview_before_image is None and self.preview_after_image is None:
            canvas.create_text(
                width / 2,
                height / 2,
                text="Select a photo to preview it",
                fill=MUTED_TEXT,
                font=("Arial", 11),
            )
            return

        # Fit BOTH versions to one shared rectangle. The divider changes only
        # which pixels are visible; it never changes either image's position.
        reference = self.preview_before_image or self.preview_after_image
        fitted_reference, target_size = self._fit_preview_image(reference, width, height)

        if self.preview_before_image is not None:
            if self.preview_before_image.size == fitted_reference.size:
                before = fitted_reference
            else:
                before = self.preview_before_image.copy()
                before = before.resize(target_size, Image.Resampling.LANCZOS)
        else:
            before = None

        if self.preview_after_image is not None:
            if self.preview_after_image.size == fitted_reference.size:
                after = fitted_reference
            else:
                after = self.preview_after_image.copy()
                after = after.resize(target_size, Image.Resampling.LANCZOS)
        else:
            after = None

        image_x, image_y = self._preview_position(target_size, width, height)
        divider_x = int(width * self.preview_divider)

        # Build one complete canvas image. Both before and after are pasted at
        # exactly the same coordinates, so moving the divider cannot drag the
        # before image sideways.
        composite = Image.new("RGB", (width, height), "#0C0F14")

        if before is not None:
            composite.paste(before.convert("RGB"), (image_x, image_y))

        if after is not None:
            after_layer = Image.new("RGB", (width, height), "#0C0F14")
            after_layer.paste(after.convert("RGB"), (image_x, image_y))

            mask = Image.new("L", (width, height), 0)
            mask.paste(255, (max(0, divider_x), 0, width, height))
            composite.paste(after_layer, (0, 0), mask)

        self.preview_canvas_photo = ImageTk.PhotoImage(composite)
        canvas.create_image(0, 0, image=self.preview_canvas_photo, anchor="nw")

        if after is not None:
            canvas.create_rectangle(
                divider_x - 1, 0, divider_x + 1, height,
                fill=ACCENT, outline="", tags="divider"
            )
            canvas.create_oval(
                divider_x - 12,
                height / 2 - 12,
                divider_x + 12,
                height / 2 + 12,
                fill=ACCENT,
                outline="",
                tags="divider",
            )
            canvas.create_text(
                divider_x,
                height / 2,
                text="↔",
                fill="#FFFFFF",
                font=("Arial", 10, "bold"),
                tags="divider",
            )

        canvas.create_rectangle(8, 8, 68, 29, fill="#11141A", outline="")
        canvas.create_text(
            38, 18, text="BEFORE", fill="#C4CBD8", font=("Arial", 8, "bold")
        )
        canvas.create_rectangle(width - 58, 8, width - 8, 29, fill="#11141A", outline="")
        canvas.create_text(
            width - 33, 18, text="AFTER", fill=ACCENT, font=("Arial", 8, "bold")
        )

    def _fit_preview_image(self, image, width, height):
        image = image.copy()
        image.thumbnail((max(1, width - 8), max(1, height - 8)), Image.Resampling.LANCZOS)
        return image, image.size

    @staticmethod
    def _preview_position(size, width, height):
        return ((width - size[0]) // 2, (height - size[1]) // 2)

    # ------------------------------------------------------------------
    # Status / processing controls
    # ------------------------------------------------------------------

    def _build_status_bar(self, parent):
        bottom = ctk.CTkFrame(parent, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        bottom.grid_columnconfigure(1, weight=1)

        self.photo_count_label = ctk.CTkLabel(bottom, text="0 photos", text_color=SECONDARY_TEXT,
                                               font=self._font(11, "bold"))
        self.photo_count_label.grid(row=0, column=0, sticky="w")
        self.status_label = ctk.CTkLabel(bottom, text="Ready", text_color=SECONDARY_TEXT,
                                         font=self._font(11))
        self.status_label.grid(row=0, column=1, sticky="w", padx=(18, 0))

        self.progress = ctk.CTkProgressBar(bottom, height=7, corner_radius=4,
                                           progress_color=ACCENT, fg_color="#252B38")
        self.progress.grid(row=0, column=2, sticky="ew", padx=18)
        self.progress.configure(width=180)
        self.progress.set(0)

        self.output_button = ctk.CTkButton(
            bottom, text="OPEN OUTPUT", width=125, height=40, corner_radius=10,
            fg_color="#252B38", hover_color="#303746", border_width=1,
            border_color=BORDER, text_color=TEXT, command=self.open_output_folder,
        )
        self.output_button.grid(row=0, column=3, sticky="e", padx=(0, 10))

        self.edit_button = ctk.CTkButton(
            bottom, text="EDIT PHOTOS", width=165, height=44, corner_radius=11,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, font=self._font(12, "bold"),
            command=self.process_photos,
        )
        self.edit_button.grid(row=0, column=4, sticky="e")

    # ------------------------------------------------------------------
    # Folder memory and syncing
    # ------------------------------------------------------------------

    @property
    def settings_file(self) -> Path:
        return get_settings_folder() / "settings.json"

    def _load_saved_input_folder(self) -> Path:
        try:
            if not self.settings_file.exists():
                return self.default_input_folder
            with self.settings_file.open("r", encoding="utf-8") as file:
                settings = json.load(file)
            saved_folder = settings.get("input_folder")
            return Path(saved_folder).expanduser() if saved_folder else self.default_input_folder
        except (OSError, json.JSONDecodeError, TypeError):
            return self.default_input_folder

    def _save_input_folder(self):
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with self.settings_file.open("w", encoding="utf-8") as file:
                json.dump({"input_folder": str(self.input_folder)}, file, indent=4)
        except OSError:
            pass

    def _update_input_folder_display(self):
        self.input_folder_name_label.configure(text=self.input_folder.name)
        self.input_folder_path_label.configure(text=self._shorten_path(self.input_folder))

    def _schedule_folder_sync(self):
        self.root.after(750, self._watch_input_folder)

    def _watch_input_folder(self):
        try:
            actual_paths = self._find_images_in_folder(self.input_folder)
            signature_parts = []
            for path in actual_paths:
                try:
                    stat = path.stat()
                    signature_parts.append((str(path.resolve()), stat.st_mtime_ns, stat.st_size))
                except OSError:
                    signature_parts.append((str(path.resolve()), 0, 0))
            signature = tuple(signature_parts)
            if signature != self.folder_signature and not self.processing:
                self._sync_input_folder(silent=True)
        except Exception:
            pass
        finally:
            self._schedule_folder_sync()

    def _sync_input_folder(self, silent=False):
        if self.processing or self.sync_running:
            return
        self.sync_running = True
        try:
            folder = self.input_folder.resolve()
            folder_paths = [path.resolve() for path in self._find_images_in_folder(folder)]
            old_paths = list(self.photo_paths)
            old_set = set(old_paths)
            new_set = set(folder_paths)

            # The input folder is the source of truth for images in that folder.
            # Keep any manually added photos from elsewhere, but mirror this folder.
            kept = []
            for path in old_paths:
                try:
                    resolved = path.resolve()
                    inside = resolved.is_relative_to(folder)
                except (OSError, ValueError):
                    inside = False
                    resolved = path
                if inside:
                    if resolved in new_set:
                        kept.append(resolved)
                elif path.exists():
                    kept.append(path)

            for path in folder_paths:
                if path not in kept:
                    kept.append(path)

            self.photo_paths = kept
            changed = old_set != set(kept)

            if self.example_image_path is not None and not self.example_image_path.exists():
                self.example_image_path = None

            if self.example_image_path not in self.photo_paths:
                if self.photo_paths:
                    # If the current selection disappeared, choose the first
                    # folder image rather than an arbitrary replacement.
                    self.selected_photo_index = 0
                    self.example_image_path = self.photo_paths[0]
                else:
                    self.selected_photo_index = 0

            if self.photo_paths:
                if self.example_image_path in self.photo_paths:
                    self.selected_photo_index = self.photo_paths.index(self.example_image_path)
                else:
                    self.selected_photo_index = 0
                    self.example_image_path = self.photo_paths[0]
                self.carousel_position = float(self.selected_photo_index)
                self.carousel_target = float(self.selected_photo_index)
                self._show_before_preview()
                if changed:
                    self._generate_preview()
            else:
                self.current_preview_token += 1
                self.preview_before_image = None
                self.preview_after_image = None
                self._redraw_preview()

            signature_parts = []
            for path in folder_paths:
                try:
                    stat = path.stat()
                    signature_parts.append((str(path), stat.st_mtime_ns, stat.st_size))
                except OSError:
                    signature_parts.append((str(path), 0, 0))
            self.folder_signature = tuple(signature_parts)
            self._update_photo_count()
            self._redraw_carousel()
            if not silent and changed:
                self.status_label.configure(text="Input folder synced", text_color=SUCCESS)
        finally:
            self.sync_running = False

    # ------------------------------------------------------------------
    # Drag and drop / importing
    # ------------------------------------------------------------------

    def _setup_drag_and_drop(self):
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self._handle_drop)

    def _handle_drop(self, event):
        paths = self.root.tk.splitlist(event.data)
        collected = []
        for raw_path in paths:
            path = Path(raw_path)
            if path.is_dir():
                collected.extend(self._find_images_in_folder(path))
            elif path.is_file():
                collected.append(path)
        self._add_photo_paths(collected)

    def choose_folder(self):
        folder = filedialog.askdirectory(title="Choose photo folder")
        if not folder:
            return
        self.input_folder = Path(folder).expanduser().resolve()
        self.input_folder.mkdir(parents=True, exist_ok=True)
        self._save_input_folder()
        self._update_input_folder_display()
        self.photo_paths.clear()
        self.example_image_path = None
        self.selected_photo_index = 0
        self.carousel_position = 0.0
        self.carousel_target = 0.0
        self.current_preview_token += 1
        self.folder_signature = ()
        self.preview_before_image = None
        self.preview_after_image = None
        self._redraw_preview()
        self.load_input_folder()
        self.status_label.configure(text=f"Watching {self.input_folder.name}", text_color=SUCCESS)

    def choose_photos(self):
        paths = filedialog.askopenfilenames(
            title="Add photos",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp"), ("JPEG", "*.jpg *.jpeg"),
                       ("PNG", "*.png"), ("WebP", "*.webp")],
        )
        if paths:
            self._add_photo_paths([Path(path) for path in paths])

    def load_input_folder(self):
        self._sync_input_folder(silent=True)

    def _find_images_in_folder(self, folder: Path) -> list[Path]:
        if not folder.exists():
            return []
        return sorted(
            path for path in folder.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )

    def _add_photo_paths(self, paths: list[Path], show_status: bool = True):
        added = []
        for path in paths:
            try:
                path = path.resolve()
            except OSError:
                continue
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS or path in self.photo_paths:
                continue
            self.photo_paths.append(path)
            added.append(path)

        if not added:
            return

        if self.example_image_path is None:
            self.selected_photo_index = 0
            self.example_image_path = self.photo_paths[0]
            self.carousel_position = 0.0
            self.carousel_target = 0.0

        self._update_photo_count()
        if show_status:
            count = len(added)
            self.status_label.configure(text=f"Added {count} photo" + ("s" if count != 1 else ""),
                                        text_color=SUCCESS)
        self._show_before_preview()
        self._generate_preview()
        self._redraw_carousel()

    def _update_photo_count(self):
        count = len(self.photo_paths)
        self.photo_count_label.configure(text=f"{count} photo" + ("s" if count != 1 else ""))
        self._update_selected_photo_label()

    def clear_photos(self):
        if self.processing:
            return
        self.photo_paths.clear()
        self.example_image_path = None
        self.selected_photo_index = 0
        self.carousel_position = 0.0
        self.carousel_target = 0.0
        self.hovered_photo_index = None
        self.current_preview_token += 1
        self.preview_before_image = None
        self.preview_after_image = None
        self._redraw_preview()
        self._redraw_carousel()
        self._update_photo_count()
        self.status_label.configure(text="Ready — folder is still being watched", text_color=SECONDARY_TEXT)

    # ------------------------------------------------------------------
    # Preview generation
    # ------------------------------------------------------------------

    def _category_changed(self, display_category: str):
        category = self.category_map.get(display_category)
        if category:
            self._populate_preset_cards(category)

    def _generate_preview(self):
        if self.example_image_path is None or not self.selected_preset_name:
            return
        preset = get_preset_by_name(self.selected_preset_name)
        if preset is None:
            return

        self.current_preview_token += 1
        token = self.current_preview_token
        input_path = self.example_image_path
        self.preview_after_image = None
        self._redraw_preview()

        def worker():
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    output_path = Path(temp_dir) / "preview.jpg"
                    process_image(input_path, output_path, preset.settings)
                    with Image.open(output_path) as output_image:
                        preview = output_image.convert("RGB")
                        preview.load()
                self.root.after(0, lambda: self._finish_preview(token, preview))
            except Exception as error:
                self.root.after(0, lambda: self._preview_error(token, error))

        threading.Thread(target=worker, daemon=True).start()

    def _show_before_preview(self):
        if self.example_image_path is None:
            self.preview_before_image = None
            self._redraw_preview()
            return
        try:
            with Image.open(self.example_image_path) as image:
                self.preview_before_image = ImageOps.exif_transpose(image).convert("RGB").copy()
            self._redraw_preview()
        except Exception as error:
            self.preview_before_image = None
            self._redraw_preview()
            self.status_label.configure(text=f"Could not load preview: {error}", text_color=ERROR)

    def _finish_preview(self, token: int, image: Image.Image):
        if token == self.current_preview_token:
            self.preview_after_image = image.copy()
            self._redraw_preview()

    def _preview_error(self, token: int, error: Exception):
        if token != self.current_preview_token:
            return
        self.preview_after_image = None
        self._redraw_preview()
        self.status_label.configure(text=f"Preview error: {error}", text_color=ERROR)

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def process_photos(self):
        if self.processing:
            return
        if not self.photo_paths:
            messagebox.showinfo("No photos", "Add some photos before editing them.")
            return
        if not self.selected_preset_name:
            messagebox.showerror("No preset", "Please choose a preset.")
            return
        preset = get_preset_by_name(self.selected_preset_name)
        if preset is None:
            messagebox.showerror("Preset error", "The selected preset could not be found.")
            return

        self.processing = True
        self.progress.set(0)
        self.edit_button.configure(state="disabled", text="PROCESSING...")
        self.clear_button.configure(state="disabled")
        self.change_folder_button.configure(state="disabled")
        self.status_label.configure(text="Preparing photos...", text_color=SECONDARY_TEXT)
        threading.Thread(target=self._process_worker, args=(list(self.photo_paths), preset), daemon=True).start()

    def _process_worker(self, photos: list[Path], preset):
        total = len(photos)
        successful = 0
        failed = 0
        output_folder = self._create_output_folder(total, preset.name)

        for index, input_path in enumerate(photos, start=1):
            try:
                output_path = self._get_unique_output_path(output_folder, input_path.name)
                process_image(input_path, output_path, preset.settings)
                successful += 1
            except Exception:
                failed += 1
            progress = index / total
            self.root.after(0, lambda value=progress, current=index, total_count=total:
                            self._update_progress(value, current, total_count))

        self.root.after(0, lambda: self._processing_finished(output_folder, successful, failed))

    def _update_progress(self, value: float, current: int, total: int):
        self.progress.set(value)
        self.status_label.configure(text=f"Editing {current} of {total}...")

    def _processing_finished(self, output_folder: Path, successful: int, failed: int):
        self.processing = False
        self.last_output_folder = output_folder
        self.edit_button.configure(state="normal", text="EDIT PHOTOS")
        self.clear_button.configure(state="normal")
        self.change_folder_button.configure(state="normal")
        self.progress.set(1)

        if failed == 0:
            status = f"Finished — {successful} photo" + ("s" if successful != 1 else "") + " edited successfully."
            self.status_label.configure(text=status, text_color=SUCCESS)
        else:
            self.status_label.configure(text=f"Finished — {successful} succeeded, {failed} failed.", text_color=ERROR)

        result = messagebox.askyesno(
            "Luma finished",
            f"{successful} photo" + ("s" if successful != 1 else "") +
            " edited successfully.\n\n" +
            (f"{failed} photo" + ("s" if failed != 1 else "") + " failed.\n\n" if failed else "") +
            "Open the output folder?",
        )
        if result:
            self.open_output_folder()

    # ------------------------------------------------------------------
    # Output handling
    # ------------------------------------------------------------------

    def _create_output_folder(self, count: int, preset_name: str) -> Path:
        timestamp = datetime.now().strftime("%H-%M_%d-%m-%y")
        folder_name = f"{count}_{preset_name}_images_{timestamp}"
        output_folder = self.output_folder / folder_name
        counter = 2
        while output_folder.exists():
            output_folder = self.output_folder / f"{folder_name}_{counter}"
            counter += 1
        output_folder.mkdir(parents=True, exist_ok=True)
        return output_folder

    def _get_unique_output_path(self, output_folder: Path, filename: str) -> Path:
        output_path = output_folder / filename
        if not output_path.exists():
            return output_path
        original = Path(filename)
        counter = 2
        while True:
            output_path = output_folder / f"{original.stem}_{counter}{original.suffix}"
            if not output_path.exists():
                return output_path
            counter += 1

    def open_output_folder(self):
        folder = self.last_output_folder if self.last_output_folder and self.last_output_folder.exists() else self.output_folder
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            elif sys.platform == "win32":
                os.startfile(str(folder))
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
        except Exception as error:
            messagebox.showerror("Could not open folder", str(error))

    @staticmethod
    def _shorten_path(path: Path) -> str:
        text = str(path)
        return text if len(text) <= 55 else "..." + text[-52:]


def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    LumaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
