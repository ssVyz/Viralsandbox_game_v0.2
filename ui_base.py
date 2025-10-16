"""
Base UI Classes and Utilities

Provides abstract base classes and shared UI utilities for all game modules.
"""

import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod
from typing import Any

from constants import (
    TEXT_WIDGET_CONFIG,
    CONSOLE_WIDGET_CONFIG,
)


class GameModule(ABC):
    """Abstract base class for all game modules."""

    def __init__(self, parent: tk.Widget, controller: Any):
        self.parent = parent
        self.controller = controller
        self.frame = ttk.Frame(parent)
        self.setup_ui()

    @abstractmethod
    def setup_ui(self):
        """Setup the UI for this module. Must be implemented by subclasses."""
        pass

    def show(self):
        """Show this module."""
        self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        """Hide this module."""
        self.frame.pack_forget()

    def destroy(self):
        """Clean up this module."""
        self.frame.destroy()


class UIUtilities:
    """Shared UI utility functions."""

    @staticmethod
    def style_text_widget(text_widget: tk.Text):
        """Apply consistent styling to text widgets for better readability."""
        text_widget.config(**TEXT_WIDGET_CONFIG)

        # Configure text tags for better formatting
        text_widget.tag_configure("header", font=("Segoe UI", 12, "bold"), foreground="#1a202c")
        text_widget.tag_configure("subheader", font=("Segoe UI", 11, "bold"), foreground="#2d3748")
        text_widget.tag_configure("emphasis", font=("Segoe UI", 11, "italic"), foreground="#4a5568")

    @staticmethod
    def style_console_widget(text_widget: tk.Text):
        """Apply console-specific styling to text widgets."""
        text_widget.config(**CONSOLE_WIDGET_CONFIG)

    @staticmethod
    def center_dialog(dialog: tk.Toplevel, width: int, height: int):
        """Center a dialog window on screen."""
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    @staticmethod
    def create_labeled_entry(
            parent: tk.Widget,
            label_text: str,
            variable: tk.Variable,
            row: int,
            label_column: int = 0,
            entry_column: int = 1,
            width: int = 30,
            **grid_kwargs
    ) -> ttk.Entry:
        """Create a labeled entry widget with grid layout."""
        ttk.Label(parent, text=label_text).grid(
            row=row, column=label_column, sticky=tk.W, padx=(0, 5)
        )
        entry = ttk.Entry(parent, textvariable=variable, width=width)
        entry.grid(row=row, column=entry_column, sticky=tk.W, **grid_kwargs)
        return entry

    @staticmethod
    def create_labeled_combobox(
            parent: tk.Widget,
            label_text: str,
            variable: tk.Variable,
            values: list,
            row: int,
            label_column: int = 0,
            combo_column: int = 1,
            width: int = 20,
            **grid_kwargs
    ) -> ttk.Combobox:
        """Create a labeled combobox widget with grid layout."""
        ttk.Label(parent, text=label_text).grid(
            row=row, column=label_column, sticky=tk.W, padx=(0, 5)
        )
        combo = ttk.Combobox(parent, textvariable=variable, width=width, state="readonly")
        combo['values'] = values
        combo.grid(row=row, column=combo_column, sticky=tk.W, **grid_kwargs)
        return combo

    @staticmethod
    def create_scrollable_listbox(
            parent: tk.Widget,
            width: int = 35,
            height: int = 20,
            selectmode: str = tk.SINGLE
    ) -> tuple[tk.Listbox, ttk.Scrollbar]:
        """Create a listbox with scrollbar."""
        frame = ttk.Frame(parent)

        listbox = tk.Listbox(frame, width=width, height=height, selectmode=selectmode)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)

        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        frame.pack(fill=tk.BOTH, expand=True)

        return listbox, scrollbar

    @staticmethod
    def create_button_row(
            parent: tk.Widget,
            buttons: list[tuple[str, callable]],
            pack_kwargs: dict = None
    ) -> list[ttk.Button]:
        """
        Create a row of buttons.

        Args:
            parent: Parent widget
            buttons: List of (text, command) tuples
            pack_kwargs: Additional pack() kwargs for the frame

        Returns:
            List of created button widgets
        """
        pack_kwargs = pack_kwargs or {}
        frame = ttk.Frame(parent)
        frame.pack(**pack_kwargs)

        created_buttons = []
        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(frame, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=(0, 5) if i < len(buttons) - 1 else 0)
            created_buttons.append(btn)

        return created_buttons

    @staticmethod
    def bind_listbox_selection(
            listbox: tk.Listbox,
            on_select_callback: callable,
            on_click_callback: callable = None
    ):
        """Bind standard selection events to a listbox."""
        listbox.bind('<<ListboxSelect>>', on_select_callback)

        if on_click_callback:
            listbox.bind('<Button-1>', lambda e: listbox.after(10, on_click_callback))
            listbox.bind('<ButtonRelease-1>', lambda e: listbox.after(10, on_click_callback))
            listbox.bind('<Double-Button-1>', lambda e: on_click_callback())


class CustomStyles:
    """Custom ttk styles for the application."""

    @staticmethod
    def setup_styles():
        """Setup custom ttk styles."""
        style = ttk.Style()

        # Accent button style for primary actions
        style.configure(
            "Accent.TButton",
            font=("Arial", 11, "bold"),
            padding=(10, 8)
        )

        # Card frame style
        style.configure(
            "Card.TFrame",
            relief="solid",
            borderwidth=1
        )

    @staticmethod
    def apply_to_widget(widget: tk.Widget, style_name: str):
        """Apply a custom style to a widget."""
        if hasattr(widget, 'configure'):
            widget.configure(style=style_name)