"""
Editor Module - Gene Database Editor

Provides full editing capabilities for entities, genes, and milestones.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
from typing import Optional, Dict, List

from constants import (
    FONT_HEADER,
    FONT_SMALL,
    FONT_ITALIC_SMALL,
    EDITOR_LISTBOX_WIDTH,
    EDITOR_LISTBOX_HEIGHT,
    EDITOR_DESC_TEXT_HEIGHT,
    EDITOR_DESC_TEXT_WIDTH,
    EDITOR_GENE_DESC_WIDTH,
    EFFECT_EDITOR_MAX_INPUTS,
    EFFECT_EDITOR_MAX_OUTPUTS,
    VALID_LOCATIONS,
    VALID_ENTITY_CLASSES,
    VALID_RULE_TYPES,
    VALID_MILESTONE_TYPES,
    MIN_DEGRADATION_RATE,
    MAX_DEGRADATION_RATE,
    INTERFERON_MIN,
    INTERFERON_MAX,
    FILE_TYPE_JSON,
    EFFECT_EDITOR_DIALOG_WIDTH,
    EFFECT_EDITOR_DIALOG_HEIGHT,
)
from data_models import GeneDatabaseManager
from ui_base import GameModule, UIUtilities


class EditorModule(GameModule):
    """Gene database editor module with tabs for entities, genes, and milestones."""

    def __init__(self, parent, controller):
        self.db_manager = GeneDatabaseManager()
        self.current_entity_name: Optional[str] = None
        self.current_gene_name: Optional[str] = None
        self.current_milestone_id: Optional[str] = None
        super().__init__(parent, controller)

    def setup_ui(self):
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(header_frame, text="Gene Database Editor", font=FONT_HEADER).pack(side=tk.LEFT)

        # File operations
        file_frame = ttk.Frame(header_frame)
        file_frame.pack(side=tk.RIGHT)

        buttons = [
            ("New Database", self.new_database),
            ("Open", self.open_database),
            ("Save", self.save_database),
            ("Save As", self.save_as_database),
            ("← Menu", lambda: self.controller.switch_to_module("menu")),
        ]

        for text, command in buttons:
            ttk.Button(file_frame, text=text, command=command).pack(side=tk.LEFT, padx=2)

        # Database info frame
        info_frame = ttk.LabelFrame(self.frame, text="Database Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X)

        # Database name and version
        ttk.Label(info_grid, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.db_name_var = tk.StringVar()
        self.db_name_entry = ttk.Entry(info_grid, textvariable=self.db_name_var, width=30)
        self.db_name_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(info_grid, text="Version:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.db_version_var = tk.StringVar()
        self.db_version_entry = ttk.Entry(info_grid, textvariable=self.db_version_var, width=10)
        self.db_version_entry.grid(row=0, column=3, sticky=tk.W)

        # Description
        ttk.Label(info_grid, text="Description:").grid(row=1, column=0, sticky=tk.NW, padx=(0, 5), pady=(10, 0))
        self.db_desc_text = tk.Text(info_grid, height=2, width=60)
        self.db_desc_text.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=(10, 0))

        # Status
        self.status_label = ttk.Label(info_frame, text="No database loaded", font=FONT_SMALL)
        self.status_label.pack(anchor=tk.W, pady=(10, 0))

        # Main content area with tabs
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Entities tab
        self.entities_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.entities_frame, text="Entities")
        self.setup_entities_tab()

        # Genes tab
        self.genes_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.genes_frame, text="Genes")
        self.setup_genes_tab()

        # Milestones tab
        self.milestones_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.milestones_frame, text="Milestones")
        self.setup_milestones_tab()

        # Initialize displays
        self.update_database_display()
        self.update_entity_list()
        self.update_gene_list()
        self.update_milestone_list()
        self.clear_entity_form()
        self.clear_gene_form()
        self.clear_milestone_form()

    def setup_entities_tab(self):
        """Setup the entities tab."""
        main_frame = ttk.Frame(self.entities_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Entity list
        left_frame = ttk.LabelFrame(main_frame, text="Entities", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        entity_list_frame = ttk.Frame(left_frame)
        entity_list_frame.pack(fill=tk.BOTH, expand=True)

        self.entity_listbox = tk.Listbox(entity_list_frame, width=EDITOR_LISTBOX_WIDTH, height=EDITOR_LISTBOX_HEIGHT)
        self.entity_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        UIUtilities.bind_listbox_selection(
            self.entity_listbox,
            self.on_entity_select,
            self.handle_entity_selection
        )

        entity_scrollbar = ttk.Scrollbar(entity_list_frame, orient=tk.VERTICAL, command=self.entity_listbox.yview)
        entity_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.entity_listbox.config(yscrollcommand=entity_scrollbar.set)

        # Entity management buttons
        entity_btn_frame = ttk.Frame(left_frame)
        entity_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(entity_btn_frame, text="New Entity", command=self.new_entity).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(entity_btn_frame, text="Clone Entity", command=self.clone_entity).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(left_frame, text="Click entity to edit →", font=FONT_ITALIC_SMALL).pack(pady=(5, 0))

        # Right panel - Entity editor
        self.entity_editor_frame = ttk.LabelFrame(main_frame, text="Entity Editor", padding=10)
        self.entity_editor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.entity_status_label = ttk.Label(
            self.entity_editor_frame,
            text="No entity selected",
            font=FONT_SMALL
        )
        self.entity_status_label.pack(anchor=tk.W, pady=(0, 10))

        # Entity properties
        props_frame = ttk.LabelFrame(self.entity_editor_frame, text="Entity Properties", padding=10)
        props_frame.pack(fill=tk.X, pady=(0, 10))

        props_grid = ttk.Frame(props_frame)
        props_grid.pack(fill=tk.X)

        # Entity name
        ttk.Label(props_grid, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.entity_name_var = tk.StringVar()
        self.entity_name_entry = ttk.Entry(props_grid, textvariable=self.entity_name_var, width=40)
        self.entity_name_entry.grid(row=0, column=1, columnspan=3, sticky=tk.W, pady=(0, 5))

        # Description
        ttk.Label(props_grid, text="Description:").grid(row=1, column=0, sticky=tk.NW, padx=(0, 5))
        self.entity_desc_text = tk.Text(props_grid, height=EDITOR_DESC_TEXT_HEIGHT, width=50)
        self.entity_desc_text.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=(0, 5))

        # Degradation rate
        ttk.Label(props_grid, text="Base Degradation Rate:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.degradation_var = tk.DoubleVar(value=0.05)
        degradation_frame = ttk.Frame(props_grid)
        degradation_frame.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))

        ttk.Entry(degradation_frame, textvariable=self.degradation_var, width=10).pack(side=tk.LEFT)
        ttk.Label(degradation_frame, text="(0.0 - 1.0)", font=FONT_ITALIC_SMALL).pack(side=tk.LEFT, padx=(5, 0))

        # Location
        ttk.Label(props_grid, text="Location:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.location_var = tk.StringVar()
        location_combo = ttk.Combobox(props_grid, textvariable=self.location_var, width=20)
        location_combo['values'] = VALID_LOCATIONS
        location_combo.grid(row=3, column=1, sticky=tk.W, pady=(5, 0))

        # Entity class
        ttk.Label(props_grid, text="Entity Class:").grid(row=3, column=2, sticky=tk.W, padx=(20, 5), pady=(5, 0))
        self.entity_class_var = tk.StringVar()
        class_combo = ttk.Combobox(props_grid, textvariable=self.entity_class_var, width=15)
        class_combo['values'] = VALID_ENTITY_CLASSES
        class_combo.grid(row=3, column=3, sticky=tk.W, pady=(5, 0))

        # Starter entity checkbox
        ttk.Label(props_grid, text="Starter Entity:").grid(row=4, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.is_starter_var = tk.BooleanVar()
        starter_checkbox = ttk.Checkbutton(
            props_grid,
            text="Can be used as starting entity",
            variable=self.is_starter_var
        )
        starter_checkbox.grid(row=4, column=1, columnspan=2, sticky=tk.W, pady=(10, 0))

        # Buttons
        button_frame = ttk.Frame(self.entity_editor_frame)
        button_frame.pack(pady=10)

        buttons = [
            ("Save", self.save_entity),
            ("Save as New", self.save_entity_as_new),
            ("Clear", self.clear_entity_form),
            ("Delete", self.delete_entity),
        ]

        for text, command in buttons:
            ttk.Button(button_frame, text=text, command=command).pack(side=tk.LEFT, padx=(0, 5))

    def setup_genes_tab(self):
        """Setup the genes tab."""
        main_frame = ttk.Frame(self.genes_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Gene list
        left_frame = ttk.LabelFrame(main_frame, text="Genes", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        gene_list_frame = ttk.Frame(left_frame)
        gene_list_frame.pack(fill=tk.BOTH, expand=True)

        self.gene_listbox = tk.Listbox(gene_list_frame, width=EDITOR_LISTBOX_WIDTH, height=EDITOR_LISTBOX_HEIGHT)
        self.gene_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        UIUtilities.bind_listbox_selection(
            self.gene_listbox,
            self.on_gene_select,
            self.handle_gene_selection
        )

        gene_scrollbar = ttk.Scrollbar(gene_list_frame, orient=tk.VERTICAL, command=self.gene_listbox.yview)
        gene_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.gene_listbox.config(yscrollcommand=gene_scrollbar.set)

        # Gene management buttons
        gene_btn_frame = ttk.Frame(left_frame)
        gene_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(gene_btn_frame, text="New Gene", command=self.new_gene).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gene_btn_frame, text="Clone Gene", command=self.clone_gene).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(left_frame, text="Click gene to edit →", font=FONT_ITALIC_SMALL).pack(pady=(5, 0))

        # Right panel - Gene editor
        self.gene_editor_frame = ttk.LabelFrame(main_frame, text="Gene Editor", padding=10)
        self.gene_editor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.gene_status_label = ttk.Label(self.gene_editor_frame, text="No gene selected", font=FONT_SMALL)
        self.gene_status_label.pack(anchor=tk.W, pady=(0, 10))

        # Gene properties
        props_frame = ttk.LabelFrame(self.gene_editor_frame, text="Gene Properties", padding=10)
        props_frame.pack(fill=tk.X, pady=(0, 10))

        props_grid = ttk.Frame(props_frame)
        props_grid.pack(fill=tk.X)

        # Gene name
        ttk.Label(props_grid, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.gene_name_var = tk.StringVar()
        self.gene_name_entry = ttk.Entry(props_grid, textvariable=self.gene_name_var, width=30)
        self.gene_name_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        # Gene cost
        ttk.Label(props_grid, text="Cost:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.gene_cost_var = tk.IntVar()
        self.gene_cost_entry = ttk.Entry(props_grid, textvariable=self.gene_cost_var, width=10)
        self.gene_cost_entry.grid(row=0, column=3, sticky=tk.W)

        # Gene description
        ttk.Label(props_grid, text="Description:").grid(row=1, column=0, sticky=tk.NW, padx=(0, 5), pady=(10, 0))
        self.gene_desc_text = tk.Text(props_grid, height=EDITOR_DESC_TEXT_HEIGHT, width=EDITOR_GENE_DESC_WIDTH)
        self.gene_desc_text.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=(10, 0))

        # Prerequisites
        ttk.Label(props_grid, text="Prerequisites:").grid(row=2, column=0, sticky=tk.NW, padx=(0, 5), pady=(10, 0))
        prereq_frame = ttk.Frame(props_grid)
        prereq_frame.grid(row=2, column=1, columnspan=3, sticky=tk.W, pady=(10, 0))

        self.prereq_listbox = tk.Listbox(prereq_frame, height=3, width=40)
        self.prereq_listbox.pack(side=tk.LEFT)

        prereq_btn_frame = ttk.Frame(prereq_frame)
        prereq_btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))

        ttk.Button(prereq_btn_frame, text="Add", command=self.add_prerequisite).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(prereq_btn_frame, text="Remove", command=self.remove_prerequisite).pack(fill=tk.X)

        # Polymerase gene checkbox
        ttk.Label(props_grid, text="Polymerase Gene:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.is_polymerase_var = tk.BooleanVar()
        polymerase_checkbox = ttk.Checkbutton(
            props_grid,
            text="This is a polymerase gene (limit: 1 per virus)",
            variable=self.is_polymerase_var
        )
        polymerase_checkbox.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=(10, 0))

        # Effects section
        effects_frame = ttk.LabelFrame(self.gene_editor_frame, text="Gene Effects", padding=10)
        effects_frame.pack(fill=tk.BOTH, expand=True)

        effects_list_frame = ttk.Frame(effects_frame)
        effects_list_frame.pack(fill=tk.X, pady=(0, 10))

        self.effects_listbox = tk.Listbox(effects_list_frame, height=6)
        self.effects_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.effects_listbox.bind('<<ListboxSelection>>', self.on_effect_select)

        effects_btn_frame = ttk.Frame(effects_list_frame)
        effects_btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        ttk.Button(effects_btn_frame, text="Add Effect", command=self.add_effect).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(effects_btn_frame, text="Edit Effect", command=self.edit_effect).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(effects_btn_frame, text="Remove Effect", command=self.remove_effect).pack(fill=tk.X)

        # Gene buttons
        gene_button_frame = ttk.Frame(self.gene_editor_frame)
        gene_button_frame.pack(pady=10)

        buttons = [
            ("Save", self.save_gene),
            ("Save as New", self.save_gene_as_new),
            ("Clear", self.clear_gene_form),
            ("Delete", self.delete_gene),
        ]

        for text, command in buttons:
            ttk.Button(gene_button_frame, text=text, command=command).pack(side=tk.LEFT, padx=(0, 5))

    def setup_milestones_tab(self):
        """Setup the milestones tab."""
        main_frame = ttk.Frame(self.milestones_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Milestone list
        left_frame = ttk.LabelFrame(main_frame, text="Milestones", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

        milestone_list_frame = ttk.Frame(left_frame)
        milestone_list_frame.pack(fill=tk.BOTH, expand=True)

        self.milestone_listbox = tk.Listbox(milestone_list_frame, width=EDITOR_LISTBOX_WIDTH, height=EDITOR_LISTBOX_HEIGHT)
        self.milestone_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        UIUtilities.bind_listbox_selection(
            self.milestone_listbox,
            self.on_milestone_select,
            self.handle_milestone_selection
        )

        milestone_scrollbar = ttk.Scrollbar(milestone_list_frame, orient=tk.VERTICAL, command=self.milestone_listbox.yview)
        milestone_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.milestone_listbox.config(yscrollcommand=milestone_scrollbar.set)

        # Milestone management buttons
        milestone_btn_frame = ttk.Frame(left_frame)
        milestone_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(milestone_btn_frame, text="New Milestone", command=self.new_milestone).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(milestone_btn_frame, text="Clone Milestone", command=self.clone_milestone).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(left_frame, text="Click milestone to edit →", font=FONT_ITALIC_SMALL).pack(pady=(5, 0))

        # Right panel - Milestone editor
        self.milestone_editor_frame = ttk.LabelFrame(main_frame, text="Milestone Editor", padding=10)
        self.milestone_editor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.milestone_status_label = ttk.Label(self.milestone_editor_frame, text="No milestone selected", font=FONT_SMALL)
        self.milestone_status_label.pack(anchor=tk.W, pady=(0, 10))

        # Milestone properties
        props_frame = ttk.LabelFrame(self.milestone_editor_frame, text="Milestone Properties", padding=10)
        props_frame.pack(fill=tk.X, pady=(0, 10))

        props_grid = ttk.Frame(props_frame)
        props_grid.pack(fill=tk.X)

        # Milestone ID and Name
        ttk.Label(props_grid, text="ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.milestone_id_var = tk.StringVar()
        self.milestone_id_entry = ttk.Entry(props_grid, textvariable=self.milestone_id_var, width=20)
        self.milestone_id_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(props_grid, text="Name:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.milestone_name_var = tk.StringVar()
        self.milestone_name_entry = ttk.Entry(props_grid, textvariable=self.milestone_name_var, width=25)
        self.milestone_name_entry.grid(row=0, column=3, sticky=tk.W)

        # Description
        ttk.Label(props_grid, text="Description:").grid(row=1, column=0, sticky=tk.NW, padx=(0, 5), pady=(10, 0))
        self.milestone_desc_text = tk.Text(props_grid, height=EDITOR_DESC_TEXT_HEIGHT, width=EDITOR_DESC_TEXT_WIDTH)
        self.milestone_desc_text.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=(10, 0))

        # Milestone type
        ttk.Label(props_grid, text="Type:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        self.milestone_type_var = tk.StringVar()
        self.milestone_type_combo = ttk.Combobox(props_grid, textvariable=self.milestone_type_var, width=25, state="readonly")
        self.milestone_type_combo['values'] = VALID_MILESTONE_TYPES
        self.milestone_type_combo.grid(row=2, column=1, sticky=tk.W, pady=(10, 0))
        self.milestone_type_combo.bind('<<ComboboxSelected>>', self.on_milestone_type_change)

        # Target and Reward
        ttk.Label(props_grid, text="Target:").grid(row=2, column=2, sticky=tk.W, padx=(20, 5), pady=(10, 0))
        self.milestone_target_var = tk.IntVar(value=5)
        self.milestone_target_entry = ttk.Entry(props_grid, textvariable=self.milestone_target_var, width=10)
        self.milestone_target_entry.grid(row=2, column=3, sticky=tk.W, pady=(10, 0))

        ttk.Label(props_grid, text="Reward EP:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.milestone_reward_var = tk.IntVar(value=25)
        self.milestone_reward_entry = ttk.Entry(props_grid, textvariable=self.milestone_reward_var, width=10)
        self.milestone_reward_entry.grid(row=3, column=1, sticky=tk.W, pady=(5, 0))

        # Entity class
        ttk.Label(props_grid, text="Entity Class:").grid(row=3, column=2, sticky=tk.W, padx=(20, 5), pady=(5, 0))
        self.milestone_entity_class_var = tk.StringVar()
        self.milestone_entity_class_combo = ttk.Combobox(
            props_grid,
            textvariable=self.milestone_entity_class_var,
            width=15,
            state="readonly"
        )
        self.milestone_entity_class_combo.grid(row=3, column=3, sticky=tk.W, pady=(5, 0))

        # Help text
        self.milestone_help_frame = ttk.Frame(props_grid)
        self.milestone_help_frame.grid(row=4, column=0, columnspan=4, sticky=tk.W, pady=(10, 0))

        self.milestone_help_label = ttk.Label(
            self.milestone_help_frame,
            text="Select a milestone type to see specific instructions",
            font=FONT_ITALIC_SMALL,
            foreground="gray"
        )
        self.milestone_help_label.pack(anchor=tk.W)

        # Buttons
        button_frame = ttk.Frame(self.milestone_editor_frame)
        button_frame.pack(pady=10)

        buttons = [
            ("Save", self.save_milestone),
            ("Save as New", self.save_milestone_as_new),
            ("Clear", self.clear_milestone_form),
            ("Delete", self.delete_milestone),
        ]

        for text, command in buttons:
            ttk.Button(button_frame, text=text, command=command).pack(side=tk.LEFT, padx=(0, 5))

    # =================== ENTITY HANDLERS ===================

    def on_entity_select(self, event):
        """Handle entity selection."""
        selection = self.entity_listbox.curselection()
        if selection:
            self.handle_entity_selection()

    def handle_entity_selection(self):
        """Handle entity selection."""
        selection = self.entity_listbox.curselection()
        if not selection:
            return

        display_text = self.entity_listbox.get(selection[0])
        if " (" in display_text and display_text.endswith(")"):
            last_paren = display_text.rfind(" (")
            entity_name = display_text[:last_paren]
        else:
            entity_name = display_text

        self.load_entity_data(entity_name)

    def load_entity_data(self, entity_name: str):
        """Load entity data into form."""
        entity = self.db_manager.get_entity(entity_name)
        if not entity:
            return

        self.current_entity_name = entity_name
        self.entity_status_label.config(text=f"Selected: {entity_name}")

        self.entity_name_var.set(entity.get("name", ""))
        self.entity_desc_text.delete(1.0, tk.END)
        self.entity_desc_text.insert(1.0, entity.get("description", ""))
        self.degradation_var.set(entity.get("base_degradation_rate", 0.05))
        self.location_var.set(entity.get("location", ""))
        self.entity_class_var.set(entity.get("entity_class", ""))
        self.is_starter_var.set(entity.get("is_starter", False))

    def save_entity(self):
        """Save current entity."""
        entity_data = {
            "name": self.entity_name_var.get().strip(),
            "description": self.entity_desc_text.get(1.0, tk.END).strip(),
            "base_degradation_rate": self.degradation_var.get(),
            "location": self.location_var.get(),
            "entity_class": self.entity_class_var.get(),
            "is_starter": self.is_starter_var.get()
        }

        if not entity_data["name"]:
            messagebox.showerror("Error", "Entity name cannot be empty")
            return

        if entity_data["base_degradation_rate"] < MIN_DEGRADATION_RATE or \
           entity_data["base_degradation_rate"] > MAX_DEGRADATION_RATE:
            messagebox.showerror("Error", "Degradation rate must be between 0.0 and 1.0")
            return

        old_name = getattr(self, 'current_entity_name', None)
        new_name = entity_data["name"]

        if old_name and old_name != new_name:
            self.db_manager.delete_entity(old_name)

        self.db_manager.add_entity(entity_data)
        self.current_entity_name = new_name

        self.update_entity_list()
        self.update_milestone_list()
        self.update_database_display()
        self.entity_status_label.config(text=f"Selected: {new_name} (Saved)")

        messagebox.showinfo("Success", f"Entity '{new_name}' saved")

    def save_entity_as_new(self):
        """Save as new entity."""
        self.current_entity_name = None
        self.entity_status_label.config(text="Creating new entity")
        self.save_entity()

    def clear_entity_form(self):
        """Clear the entity form."""
        self.current_entity_name = None
        self.entity_status_label.config(text="No entity selected")
        self.entity_name_var.set("")
        self.entity_desc_text.delete(1.0, tk.END)
        self.degradation_var.set(0.05)
        self.location_var.set("")
        self.entity_class_var.set("")
        self.is_starter_var.set(False)

    def new_entity(self):
        """Create a new entity."""
        self.clear_entity_form()
        self.entity_name_var.set("New Entity")
        self.degradation_var.set(0.05)
        self.location_var.set("unknown")
        self.entity_class_var.set("unknown")
        self.is_starter_var.set(False)
        self.entity_status_label.config(text="Creating new entity")

    def clone_entity(self):
        """Clone the selected entity."""
        if not hasattr(self, 'current_entity_name') or not self.current_entity_name:
            messagebox.showwarning("No Entity", "Please select an entity to clone")
            return

        current_name = self.entity_name_var.get()
        self.entity_name_var.set(f"{current_name} (Copy)")
        self.current_entity_name = None
        self.entity_status_label.config(text="Cloning entity")

    def delete_entity(self):
        """Delete the selected entity."""
        if not hasattr(self, 'current_entity_name') or not self.current_entity_name:
            messagebox.showwarning("No Selection", "Please select an entity to delete")
            return

        entity_name = self.current_entity_name

        if messagebox.askyesno("Confirm Delete", f"Delete entity '{entity_name}'?"):
            self.db_manager.delete_entity(entity_name)
            self.update_entity_list()
            self.update_milestone_list()
            self.update_database_display()
            self.clear_entity_form()

    def update_entity_list(self):
        """Update the entity list."""
        self.entity_listbox.delete(0, tk.END)

        for entity_name in sorted(self.db_manager.get_all_entity_names()):
            entity = self.db_manager.get_entity(entity_name)
            degradation = entity.get("base_degradation_rate", 0.05)
            is_starter = entity.get("is_starter", False)

            if is_starter:
                display_text = f"{entity_name} ({degradation:.2f}, starter)"
            else:
                display_text = f"{entity_name} ({degradation:.2f})"

            self.entity_listbox.insert(tk.END, display_text)

    # =================== GENE HANDLERS ===================

    def on_gene_select(self, event):
        """Handle gene selection."""
        selection = self.gene_listbox.curselection()
        if selection:
            self.handle_gene_selection()

    def handle_gene_selection(self):
        """Handle gene selection."""
        selection = self.gene_listbox.curselection()
        if not selection:
            return

        display_text = self.gene_listbox.get(selection[0])
        gene_name = display_text.split(" (")[0]
        self.load_gene_data(gene_name)

    def load_gene_data(self, gene_name: str):
        """Load gene data into form."""
        gene = self.db_manager.get_gene(gene_name)
        if not gene:
            return

        self.current_gene_name = gene_name
        self.gene_status_label.config(text=f"Selected: {gene_name}")

        self.gene_name_var.set(gene.get("name", ""))
        self.gene_cost_var.set(gene.get("cost", 0))

        self.gene_desc_text.delete(1.0, tk.END)
        self.gene_desc_text.insert(1.0, gene.get("description", ""))

        self.prereq_listbox.delete(0, tk.END)
        for req in gene.get("requires", []):
            self.prereq_listbox.insert(tk.END, req)

        self.effects_listbox.delete(0, tk.END)
        for effect in gene.get("effects", []):
            effect_desc = self.format_effect_description(effect)
            self.effects_listbox.insert(tk.END, effect_desc)

        self.is_polymerase_var.set(gene.get("is_polymerase", False))

    def format_effect_description(self, effect: Dict) -> str:
        """Format effect for display in list."""
        effect_type = effect.get("type", "unknown")

        if effect_type == "enable_entity":
            return f"Enable: {effect.get('entity', 'Unknown')}"
        elif effect_type == "add_transition":
            rule = effect.get("rule", {})
            rule_name = rule.get("name", "Unknown")
            inputs = rule.get("inputs", [])
            outputs = rule.get("outputs", [])

            input_summary = f"{len(inputs)} input{'s' if len(inputs) != 1 else ''}" if inputs else ""
            output_summary = f"{len(outputs)} output{'s' if len(outputs) != 1 else ''}" if outputs else ""

            interferon_amount = rule.get("interferon_amount", 0.0)
            interferon_part = f", IFN: {interferon_amount:.2f}" if interferon_amount > 0 else ""

            if input_summary and output_summary:
                return f"Transition: {rule_name} ({input_summary} → {output_summary}{interferon_part})"
            elif input_summary:
                return f"Transition: {rule_name} ({input_summary}{interferon_part})"
            else:
                return f"Transition: {rule_name}{interferon_part}"

        elif effect_type == "modify_transition":
            rule_name = effect.get("rule_name", "Unknown")
            modification = effect.get("modification", {})

            prob_mult = modification.get("probability_multiplier", 1.0)
            ifn_mult = modification.get("interferon_multiplier", 1.0)

            mod_parts = []
            if prob_mult != 1.0:
                mod_parts.append(f"prob×{prob_mult:.1f}")
            if ifn_mult != 1.0:
                mod_parts.append(f"IFN×{ifn_mult:.2f}")

            if mod_parts:
                return f"Modify: {rule_name} ({', '.join(mod_parts)})"
            else:
                return f"Modify: {rule_name}"
        else:
            return f"Unknown: {effect_type}"

    def save_gene(self):
        """Save current gene."""
        gene_data = {
            "name": self.gene_name_var.get().strip(),
            "cost": self.gene_cost_var.get(),
            "description": self.gene_desc_text.get(1.0, tk.END).strip(),
            "effects": [],
            "is_polymerase": self.is_polymerase_var.get()
        }

        if not gene_data["name"]:
            messagebox.showerror("Error", "Gene name cannot be empty")
            return

        prereqs = []
        for i in range(self.prereq_listbox.size()):
            prereqs.append(self.prereq_listbox.get(i))
        if prereqs:
            gene_data["requires"] = prereqs

        if hasattr(self, 'current_gene_name') and self.current_gene_name:
            current_gene = self.db_manager.get_gene(self.current_gene_name)
            if current_gene:
                gene_data["effects"] = current_gene.get("effects", [])

        old_name = getattr(self, 'current_gene_name', None)
        new_name = gene_data["name"]

        if old_name and old_name != new_name:
            self.db_manager.delete_gene(old_name)

        self.db_manager.add_gene(gene_data)
        self.current_gene_name = new_name

        self.update_gene_list()
        self.update_database_display()
        self.gene_status_label.config(text=f"Selected: {new_name} (Saved)")

        messagebox.showinfo("Success", f"Gene '{new_name}' saved")

    def save_gene_as_new(self):
        """Save as new gene."""
        self.current_gene_name = None
        self.gene_status_label.config(text="Creating new gene")
        self.save_gene()

    def clear_gene_form(self):
        """Clear the gene form."""
        self.current_gene_name = None
        self.gene_status_label.config(text="No gene selected")
        self.gene_name_var.set("")
        self.gene_cost_var.set(0)
        self.gene_desc_text.delete(1.0, tk.END)
        self.prereq_listbox.delete(0, tk.END)
        self.effects_listbox.delete(0, tk.END)
        self.is_polymerase_var.set(False)

    def new_gene(self):
        """Create a new gene."""
        self.clear_gene_form()
        self.gene_name_var.set("New Gene")
        self.gene_cost_var.set(0)
        self.is_polymerase_var.set(False)
        self.gene_status_label.config(text="Creating new gene")

    def clone_gene(self):
        """Clone the selected gene."""
        if not hasattr(self, 'current_gene_name') or not self.current_gene_name:
            messagebox.showwarning("No Gene", "Please select a gene to clone")
            return

        current_name = self.gene_name_var.get()
        self.gene_name_var.set(f"{current_name} (Copy)")
        self.current_gene_name = None
        self.gene_status_label.config(text="Cloning gene")

    def delete_gene(self):
        """Delete the selected gene."""
        if not hasattr(self, 'current_gene_name') or not self.current_gene_name:
            messagebox.showwarning("No Selection", "Please select a gene to delete")
            return

        gene_name = self.current_gene_name

        if messagebox.askyesno("Confirm Delete", f"Delete gene '{gene_name}'?"):
            self.db_manager.delete_gene(gene_name)
            self.update_gene_list()
            self.update_database_display()
            self.clear_gene_form()

    def add_prerequisite(self):
        """Add prerequisite gene."""
        available_genes = [name for name in self.db_manager.get_all_genes()
                          if name != self.gene_name_var.get()]

        if not available_genes:
            messagebox.showinfo("No Genes", "No other genes available as prerequisites")
            return

        prereq = simpledialog.askstring(
            "Add Prerequisite",
            f"Available genes: {', '.join(available_genes)}\n\nEnter prerequisite gene name:"
        )
        if prereq and prereq in available_genes:
            current_prereqs = [self.prereq_listbox.get(i) for i in range(self.prereq_listbox.size())]
            if prereq not in current_prereqs:
                self.prereq_listbox.insert(tk.END, prereq)
            else:
                messagebox.showinfo("Already Added", f"'{prereq}' is already a prerequisite")
        elif prereq:
            messagebox.showerror("Invalid Gene", f"'{prereq}' is not a valid gene name")

    def remove_prerequisite(self):
        """Remove prerequisite gene."""
        selection = self.prereq_listbox.curselection()
        if selection:
            self.prereq_listbox.delete(selection[0])

    def add_effect(self):
        """Add new effect."""
        self.open_effect_editor(None)

    def edit_effect(self):
        """Edit selected effect."""
        selection = self.effects_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an effect to edit")
            return

        effect_index = selection[0]
        if hasattr(self, 'current_gene_name') and self.current_gene_name:
            gene = self.db_manager.get_gene(self.current_gene_name)
            if gene and effect_index < len(gene.get("effects", [])):
                effect = gene["effects"][effect_index]
                self.open_effect_editor(effect, effect_index)

    def remove_effect(self):
        """Remove selected effect."""
        selection = self.effects_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an effect to remove")
            return

        if not hasattr(self, 'current_gene_name') or not self.current_gene_name:
            messagebox.showwarning("No Gene", "No gene selected")
            return

        effect_index = selection[0]
        gene = self.db_manager.get_gene(self.current_gene_name)
        if gene and effect_index < len(gene.get("effects", [])):
            gene_effects = gene.get("effects", [])
            del gene_effects[effect_index]

            updated_gene = gene.copy()
            updated_gene["effects"] = gene_effects
            self.db_manager.add_gene(updated_gene)

            self.load_gene_data(self.current_gene_name)

    def on_effect_select(self, event):
        """Handle effect selection."""
        pass

    def open_effect_editor(self, effect: Optional[Dict] = None, effect_index: Optional[int] = None):
        """Open effect editor dialog."""
        dialog = EffectEditorDialog(self.frame, effect, self.db_manager.get_all_entity_names())
        self.frame.wait_window(dialog.dialog)

        if dialog.result and hasattr(self, 'current_gene_name') and self.current_gene_name:
            gene = self.db_manager.get_gene(self.current_gene_name)
            if not gene:
                return

            effects = gene.get("effects", [])

            if effect_index is not None:
                effects[effect_index] = dialog.result
            else:
                effects.append(dialog.result)

            updated_gene = gene.copy()
            updated_gene["effects"] = effects
            self.db_manager.add_gene(updated_gene)

            self.load_gene_data(self.current_gene_name)

    def update_gene_list(self):
        """Update the gene list."""
        self.gene_listbox.delete(0, tk.END)

        for gene_name in sorted(self.db_manager.get_all_genes()):
            gene = self.db_manager.get_gene(gene_name)
            cost = gene.get("cost", 0)
            is_polymerase = gene.get("is_polymerase", False)

            if is_polymerase:
                display_text = f"{gene_name} ({cost} EP, Polymerase)"
            else:
                display_text = f"{gene_name} ({cost} EP)"

            self.gene_listbox.insert(tk.END, display_text)

    # =================== MILESTONE HANDLERS ===================

    def on_milestone_select(self, event):
        """Handle milestone selection."""
        selection = self.milestone_listbox.curselection()
        if selection:
            self.handle_milestone_selection()

    def handle_milestone_selection(self):
        """Handle milestone selection."""
        selection = self.milestone_listbox.curselection()
        if not selection:
            return

        display_text = self.milestone_listbox.get(selection[0])
        milestone_id = display_text.split(" (")[0]
        self.load_milestone_data(milestone_id)

    def load_milestone_data(self, milestone_id: str):
        """Load milestone data into form."""
        milestone = self.db_manager.get_milestone(milestone_id)
        if not milestone:
            return

        self.current_milestone_id = milestone_id
        self.milestone_status_label.config(text=f"Selected: {milestone_id}")

        self.milestone_id_var.set(milestone.get("id", ""))
        self.milestone_name_var.set(milestone.get("name", ""))

        self.milestone_desc_text.delete(1.0, tk.END)
        self.milestone_desc_text.insert(1.0, milestone.get("description", ""))

        self.milestone_type_var.set(milestone.get("type", "survive_turns"))
        self.milestone_target_var.set(milestone.get("target", 5))
        self.milestone_reward_var.set(milestone.get("reward_ep", 25))
        self.milestone_entity_class_var.set(milestone.get("entity_class", ""))

        self.on_milestone_type_change()

    def on_milestone_type_change(self, event=None):
        """Handle milestone type change to update UI."""
        milestone_type = self.milestone_type_var.get()

        if milestone_type in ["peak_entity_count", "cumulative_entity_count"]:
            self.milestone_entity_class_combo.config(state="readonly")
            entity_classes = self.db_manager.get_entity_classes()
            self.milestone_entity_class_combo['values'] = entity_classes
            if entity_classes and not self.milestone_entity_class_var.get():
                self.milestone_entity_class_var.set(entity_classes[0])
        else:
            self.milestone_entity_class_combo.config(state="disabled")
            self.milestone_entity_class_var.set("")

        self.update_milestone_help_text(milestone_type)

    def update_milestone_help_text(self, milestone_type: str):
        """Update help text based on milestone type."""
        help_texts = {
            "survive_turns": "Player must survive for at least the target number of turns",
            "peak_entity_count": "Player must have at least the target number of entities of the chosen class simultaneously",
            "cumulative_entity_count": "Player must create at least the target total number of entities of the chosen class"
        }

        help_text = help_texts.get(milestone_type, "Select a milestone type to see instructions")
        self.milestone_help_label.config(text=help_text)

    def save_milestone(self):
        """Save current milestone."""
        milestone_data = {
            "id": self.milestone_id_var.get().strip(),
            "name": self.milestone_name_var.get().strip(),
            "description": self.milestone_desc_text.get(1.0, tk.END).strip(),
            "type": self.milestone_type_var.get(),
            "target": self.milestone_target_var.get(),
            "reward_ep": self.milestone_reward_var.get()
        }

        if milestone_data["type"] in ["peak_entity_count", "cumulative_entity_count"]:
            milestone_data["entity_class"] = self.milestone_entity_class_var.get()

        is_valid, error_msg = self.db_manager.validate_milestone_data(milestone_data)
        if not is_valid:
            messagebox.showerror("Validation Error", error_msg)
            return

        old_id = getattr(self, 'current_milestone_id', None)
        new_id = milestone_data["id"]

        if old_id and old_id != new_id:
            self.db_manager.delete_milestone(old_id)

        self.db_manager.add_milestone(milestone_data)
        self.current_milestone_id = new_id

        self.update_milestone_list()
        self.update_database_display()
        self.milestone_status_label.config(text=f"Selected: {new_id} (Saved)")

        if hasattr(self.controller, 'handle_database_change'):
            self.controller.handle_database_change()

        messagebox.showinfo("Success", f"Milestone '{new_id}' saved")

    def save_milestone_as_new(self):
        """Save as new milestone."""
        self.current_milestone_id = None
        self.milestone_status_label.config(text="Creating new milestone")
        self.save_milestone()

    def clear_milestone_form(self):
        """Clear the milestone form."""
        self.current_milestone_id = None
        self.milestone_status_label.config(text="No milestone selected")
        self.milestone_id_var.set("")
        self.milestone_name_var.set("")
        self.milestone_desc_text.delete(1.0, tk.END)
        self.milestone_type_var.set("survive_turns")
        self.milestone_target_var.set(5)
        self.milestone_reward_var.set(25)
        self.milestone_entity_class_var.set("")
        self.on_milestone_type_change()

    def new_milestone(self):
        """Create a new milestone."""
        self.clear_milestone_form()
        self.milestone_id_var.set("new_milestone")
        self.milestone_name_var.set("New Milestone")
        self.milestone_type_var.set("survive_turns")
        self.milestone_target_var.set(5)
        self.milestone_reward_var.set(25)
        self.milestone_status_label.config(text="Creating new milestone")
        self.on_milestone_type_change()

    def clone_milestone(self):
        """Clone the selected milestone."""
        if not hasattr(self, 'current_milestone_id') or not self.current_milestone_id:
            messagebox.showwarning("No Milestone", "Please select a milestone to clone")
            return

        current_id = self.milestone_id_var.get()
        self.milestone_id_var.set(f"{current_id}_copy")
        self.current_milestone_id = None
        self.milestone_status_label.config(text="Cloning milestone")

    def delete_milestone(self):
        """Delete the selected milestone."""
        if not hasattr(self, 'current_milestone_id') or not self.current_milestone_id:
            messagebox.showwarning("No Selection", "Please select a milestone to delete")
            return

        milestone_id = self.current_milestone_id

        if messagebox.askyesno("Confirm Delete", f"Delete milestone '{milestone_id}'?"):
            self.db_manager.delete_milestone(milestone_id)
            self.update_milestone_list()
            self.update_database_display()
            self.clear_milestone_form()

            if hasattr(self.controller, 'handle_database_change'):
                self.controller.handle_database_change()

    def update_milestone_list(self):
        """Update the milestone list."""
        self.milestone_listbox.delete(0, tk.END)

        for milestone_id in sorted(self.db_manager.get_all_milestones()):
            milestone = self.db_manager.get_milestone(milestone_id)
            reward = milestone.get("reward_ep", 0)
            milestone_type = milestone.get("type", "unknown")
            target = milestone.get("target", 0)

            if milestone_type == "survive_turns":
                display_text = f"{milestone_id} ({target} turns, {reward} EP)"
            elif milestone_type in ["peak_entity_count", "cumulative_entity_count"]:
                entity_class = milestone.get("entity_class", "unknown")
                type_short = "peak" if milestone_type == "peak_entity_count" else "total"
                display_text = f"{milestone_id} ({target} {entity_class} {type_short}, {reward} EP)"
            else:
                display_text = f"{milestone_id} ({reward} EP)"

            self.milestone_listbox.insert(tk.END, display_text)

    # =================== DATABASE OPERATIONS ===================

    def new_database(self):
        """Create a new database."""
        if self.db_manager.is_modified:
            result = messagebox.askyesnocancel("Unsaved Changes", "Save changes before creating new database?")
            if result is True:
                self.save_database()
            elif result is None:
                return

        self.db_manager = GeneDatabaseManager()
        self.update_database_display()
        self.update_entity_list()
        self.update_gene_list()
        self.update_milestone_list()
        self.clear_entity_form()
        self.clear_gene_form()
        self.clear_milestone_form()

    def open_database(self):
        """Open database file."""
        if self.db_manager.is_modified:
            result = messagebox.askyesnocancel("Unsaved Changes", "Save changes before opening?")
            if result is True:
                self.save_database()
            elif result is None:
                return

        file_path = filedialog.askopenfilename(
            title="Open Gene Database",
            filetypes=FILE_TYPE_JSON,
            initialdir=os.getcwd()
        )

        if file_path:
            try:
                self.db_manager.load_database(file_path)
                self.update_database_display()
                self.update_entity_list()
                self.update_gene_list()
                self.update_milestone_list()
                self.clear_entity_form()
                self.clear_gene_form()
                self.clear_milestone_form()

                if hasattr(self.controller, 'handle_database_change'):
                    self.controller.handle_database_change()

                messagebox.showinfo(
                    "Success",
                    f"Loaded database with {len(self.db_manager.get_all_genes())} genes, "
                    f"{len(self.db_manager.get_all_entity_names())} entities, and "
                    f"{len(self.db_manager.get_all_milestones())} milestones"
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load database:\n{e}")

    def save_database(self):
        """Save current database."""
        if not self.db_manager.file_path:
            self.save_as_database()
            return

        try:
            self.update_database_info_from_ui()
            self.db_manager.save_database()
            self.update_database_display()

            if hasattr(self.controller, 'handle_database_change'):
                self.controller.handle_database_change()

            messagebox.showinfo("Success", "Database saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save database:\n{e}")

    def save_as_database(self):
        """Save database as new file."""
        file_path = filedialog.asksaveasfilename(
            title="Save Gene Database As",
            filetypes=FILE_TYPE_JSON,
            defaultextension=".json",
            initialdir=os.getcwd()
        )

        if file_path:
            try:
                self.update_database_info_from_ui()
                self.db_manager.save_database(file_path)
                self.update_database_display()

                if hasattr(self.controller, 'handle_database_change'):
                    self.controller.handle_database_change()

                messagebox.showinfo("Success", f"Database saved as {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save database:\n{e}")

    def update_database_display(self):
        """Update database info display."""
        db_info = self.db_manager.database["database_info"]

        self.db_name_var.set(db_info.get("name", ""))
        self.db_version_var.set(db_info.get("version", ""))

        self.db_desc_text.delete(1.0, tk.END)
        self.db_desc_text.insert(1.0, db_info.get("description", ""))

        if self.db_manager.file_path:
            filename = os.path.basename(self.db_manager.file_path)
            gene_count = len(self.db_manager.get_all_genes())
            entity_count = len(self.db_manager.get_all_entity_names())
            starter_count = len(self.db_manager.get_starter_entities())
            milestone_count = len(self.db_manager.get_all_milestones())
            polymerase_count = len(self.db_manager.get_polymerase_genes())
            modified = " *" if self.db_manager.is_modified else ""
            self.status_label.config(
                text=f"File: {filename} | {gene_count} genes ({polymerase_count} polymerase), "
                     f"{entity_count} entities ({starter_count} starters), {milestone_count} milestones{modified}"
            )
        else:
            gene_count = len(self.db_manager.get_all_genes())
            entity_count = len(self.db_manager.get_all_entity_names())
            starter_count = len(self.db_manager.get_starter_entities())
            milestone_count = len(self.db_manager.get_all_milestones())
            polymerase_count = len(self.db_manager.get_polymerase_genes())
            modified = " *" if self.db_manager.is_modified else ""
            self.status_label.config(
                text=f"New database | {gene_count} genes ({polymerase_count} polymerase), "
                     f"{entity_count} entities ({starter_count} starters), {milestone_count} milestones{modified}"
            )

    def update_database_info_from_ui(self):
        """Update database info from UI fields."""
        db_info = self.db_manager.database["database_info"]
        db_info["name"] = self.db_name_var.get()
        db_info["version"] = self.db_version_var.get()
        db_info["description"] = self.db_desc_text.get(1.0, tk.END).strip()


class EffectEditorDialog:
    """Dialog for editing gene effects."""

    def __init__(self, parent, effect: Optional[Dict] = None, available_entities: Optional[List[str]] = None):
        self.result = None
        self.available_entities = available_entities or []

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Effect Editor")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        UIUtilities.center_dialog(self.dialog, EFFECT_EDITOR_DIALOG_WIDTH, EFFECT_EDITOR_DIALOG_HEIGHT)

        self.setup_ui(effect)

    def setup_ui(self, effect: Optional[Dict]):
        """Setup the effect editor UI."""
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(header_frame, text="Edit Gene Effect", font=("Arial", 14, "bold")).pack()

        # Effect type selection
        type_frame = ttk.LabelFrame(self.dialog, text="Effect Type", padding=10)
        type_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.effect_type_var = tk.StringVar()
        self.effect_type_var.trace('w', self.on_effect_type_change)

        effect_types = [
            ("add_transition", "Add Transition"),
            ("modify_transition", "Modify Transition")
        ]

        for i, (value, text) in enumerate(effect_types):
            ttk.Radiobutton(type_frame, text=text, variable=self.effect_type_var, value=value).grid(
                row=0, column=i, padx=10, sticky=tk.W
            )

        # Dynamic content area
        self.content_frame = ttk.Frame(self.dialog)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="OK", command=self.ok_clicked).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.cancel_clicked).pack(side=tk.RIGHT)

        # Initialize with effect data if provided
        if effect:
            self.load_effect(effect)
        else:
            self.effect_type_var.set("add_transition")

    def load_effect(self, effect: Dict):
        """Load existing effect data."""
        effect_type = effect.get("type", "add_transition")
        self.effect_type_var.set(effect_type)
        self.dialog.after(100, lambda: self.populate_fields(effect))

    def populate_fields(self, effect: Dict):
        """Populate fields with effect data."""
        effect_type = effect.get("type", "add_transition")

        if effect_type == "add_transition":
            rule = effect.get("rule", {})
            if hasattr(self, 'rule_name_var'):
                self.rule_name_var.set(rule.get("name", ""))
                self.probability_var.set(int(rule.get("probability", 0.5) * 100))
                self.rule_type_var.set(rule.get("rule_type", "per_entity"))

                # Load inputs
                inputs = rule.get("inputs", [])
                for i in range(EFFECT_EDITOR_MAX_INPUTS):
                    if i < len(inputs):
                        input_data = inputs[i]
                        self.input_entity_vars[i].set(input_data["entity"])
                        self.input_count_vars[i].set(input_data["count"])
                        if i == 0:
                            self.input_consumed_var.set(input_data.get("consumed", True))
                    else:
                        self.input_entity_vars[i].set("")
                        self.input_count_vars[i].set(1)

                # Load outputs
                outputs = rule.get("outputs", [])
                for i in range(EFFECT_EDITOR_MAX_OUTPUTS):
                    if i < len(outputs):
                        output_data = outputs[i]
                        self.output_entity_vars[i].set(output_data["entity"])
                        self.output_count_vars[i].set(output_data["count"])
                    else:
                        self.output_entity_vars[i].set("")
                        self.output_count_vars[i].set(1)

                # Load interferon data
                interferon_amount = rule.get("interferon_amount", 0.0)
                if interferon_amount > 0:
                    self.interferon_enabled_var.set(True)
                    self.interferon_amount_var.set(interferon_amount)
                else:
                    self.interferon_enabled_var.set(False)
                    self.interferon_amount_var.set(0.0)

        elif effect_type == "modify_transition":
            if hasattr(self, 'modify_rule_var'):
                self.modify_rule_var.set(effect.get("rule_name", ""))
                modification = effect.get("modification", {})

                prob_mult = modification.get("probability_multiplier", 1.0)
                self.probability_multiplier_var.set(prob_mult)

                interferon_mult = modification.get("interferon_multiplier", 1.0)
                self.interferon_multiplier_var.set(interferon_mult)

    def on_effect_type_change(self, *args):
        """Handle effect type change."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        effect_type = self.effect_type_var.get()

        if effect_type == "add_transition":
            self.setup_add_transition_ui()
        elif effect_type == "modify_transition":
            self.setup_modify_transition_ui()

    def setup_add_transition_ui(self):
        """Setup UI for add transition effect (simplified version without scrolling)."""
        frame = ttk.LabelFrame(self.content_frame, text="Add Transition Rule", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        current_row = 0

        # Rule name
        ttk.Label(frame, text="Rule Name:").grid(row=current_row, column=0, sticky=tk.W, padx=(0, 10))
        self.rule_name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.rule_name_var, width=30).grid(row=current_row, column=1, columnspan=2, sticky=tk.W)
        current_row += 1

        # Probability
        ttk.Label(frame, text="Probability:").grid(row=current_row, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.probability_var = tk.IntVar(value=50)
        prob_frame = ttk.Frame(frame)
        prob_frame.grid(row=current_row, column=1, columnspan=2, sticky=tk.W, pady=(10, 0))

        ttk.Scale(prob_frame, from_=0, to=100, variable=self.probability_var, orient=tk.HORIZONTAL, length=150).pack(side=tk.LEFT)
        prob_label = ttk.Label(prob_frame, text="50%")
        prob_label.pack(side=tk.LEFT, padx=(5, 0))

        def update_prob_label(*args):
            prob_label.config(text=f"{self.probability_var.get()}%")

        self.probability_var.trace('w', update_prob_label)
        current_row += 1

        # Rule type
        ttk.Label(frame, text="Rule Type:").grid(row=current_row, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.rule_type_var = tk.StringVar(value="per_entity")
        type_frame = ttk.Frame(frame)
        type_frame.grid(row=current_row, column=1, columnspan=2, sticky=tk.W, pady=(10, 0))

        ttk.Radiobutton(type_frame, text="Per Entity", variable=self.rule_type_var, value="per_entity").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(type_frame, text="Per Pair", variable=self.rule_type_var, value="per_pair").pack(side=tk.LEFT)
        current_row += 1

        # Inputs (simplified - 3 rows max)
        ttk.Label(frame, text="INPUTS:", font=("Arial", 10, "bold")).grid(row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        current_row += 1

        self.input_entity_vars = []
        self.input_count_vars = []

        for i in range(EFFECT_EDITOR_MAX_INPUTS):
            input_entity_var = tk.StringVar()
            self.input_entity_vars.append(input_entity_var)
            input_combo = ttk.Combobox(frame, textvariable=input_entity_var, values=self.available_entities, width=25)
            input_combo.grid(row=current_row, column=0, sticky=tk.W, padx=(0, 10), pady=2)

            input_count_var = tk.IntVar(value=1)
            self.input_count_vars.append(input_count_var)
            ttk.Entry(frame, textvariable=input_count_var, width=8).grid(row=current_row, column=1, sticky=tk.W, padx=(0, 10), pady=2)

            current_row += 1

        self.input_consumed_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="All inputs consumed", variable=self.input_consumed_var).grid(row=current_row, column=0, columnspan=2, sticky=tk.W, pady=(5, 10))
        current_row += 1

        # Outputs (simplified - 3 rows max)
        ttk.Label(frame, text="OUTPUTS:", font=("Arial", 10, "bold")).grid(row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        current_row += 1

        self.output_entity_vars = []
        self.output_count_vars = []

        for i in range(EFFECT_EDITOR_MAX_OUTPUTS):
            output_entity_var = tk.StringVar()
            self.output_entity_vars.append(output_entity_var)
            output_combo = ttk.Combobox(frame, textvariable=output_entity_var, values=self.available_entities, width=25)
            output_combo.grid(row=current_row, column=0, sticky=tk.W, padx=(0, 10), pady=2)

            output_count_var = tk.IntVar(value=1)
            self.output_count_vars.append(output_count_var)
            ttk.Entry(frame, textvariable=output_count_var, width=8).grid(row=current_row, column=1, sticky=tk.W, padx=(0, 10), pady=2)

            current_row += 1

        # Interferon
        ttk.Label(frame, text="INTERFERON:", font=("Arial", 10, "bold")).grid(row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        current_row += 1

        self.interferon_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Triggers interferon", variable=self.interferon_enabled_var).grid(row=current_row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        current_row += 1

        ttk.Label(frame, text="Amount:").grid(row=current_row, column=0, sticky=tk.W, padx=(0, 10))
        self.interferon_amount_var = tk.DoubleVar(value=1.0)
        ttk.Entry(frame, textvariable=self.interferon_amount_var, width=10).grid(row=current_row, column=1, sticky=tk.W)

    def setup_modify_transition_ui(self):
        """Setup UI for modify transition effect."""
        frame = ttk.LabelFrame(self.content_frame, text="Modify Transition Rule", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Rule to modify
        ttk.Label(frame, text="Rule Name to Modify:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.modify_rule_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.modify_rule_var, width=40).grid(row=0, column=1, columnspan=2, sticky=tk.W)

        # Probability multiplier
        ttk.Label(frame, text="Probability Multiplier:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(15, 0))
        self.probability_multiplier_var = tk.DoubleVar(value=1.0)
        ttk.Entry(frame, textvariable=self.probability_multiplier_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=(15, 0))

        ttk.Label(frame, text="(1.0 = no change, 1.5 = 50% increase)", font=FONT_ITALIC_SMALL).grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

        # Interferon multiplier
        ttk.Label(frame, text="Interferon Multiplier:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(15, 0))
        self.interferon_multiplier_var = tk.DoubleVar(value=1.0)
        ttk.Entry(frame, textvariable=self.interferon_multiplier_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=(15, 0))

        ttk.Label(frame, text="(1.0 = no change, 2.0 = double)", font=FONT_ITALIC_SMALL).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

    def ok_clicked(self):
        """Handle OK button click."""
        effect_type = self.effect_type_var.get()

        try:
            if effect_type == "add_transition":
                rule_name = self.rule_name_var.get().strip()
                if not rule_name:
                    messagebox.showerror("Error", "Rule name is required")
                    return

                # Build inputs
                inputs = []
                for i in range(EFFECT_EDITOR_MAX_INPUTS):
                    entity_name = self.input_entity_vars[i].get().strip()
                    if entity_name:
                        count = self.input_count_vars[i].get()
                        if count <= 0:
                            messagebox.showerror("Error", f"Input {i + 1} count must be greater than 0")
                            return
                        inputs.append({
                            "entity": entity_name,
                            "count": count,
                            "consumed": self.input_consumed_var.get()
                        })

                # Build outputs
                outputs = []
                for i in range(EFFECT_EDITOR_MAX_OUTPUTS):
                    entity_name = self.output_entity_vars[i].get().strip()
                    if entity_name:
                        count = self.output_count_vars[i].get()
                        if count <= 0:
                            messagebox.showerror("Error", f"Output {i + 1} count must be greater than 0")
                            return
                        outputs.append({
                            "entity": entity_name,
                            "count": count
                        })

                if not inputs:
                    messagebox.showerror("Error", "At least one input entity is required")
                    return

                rule_data = {
                    "name": rule_name,
                    "inputs": inputs,
                    "outputs": outputs,
                    "probability": self.probability_var.get() / 100.0,
                    "rule_type": self.rule_type_var.get()
                }

                if self.interferon_enabled_var.get():
                    interferon_amount = self.interferon_amount_var.get()
                    if interferon_amount < INTERFERON_MIN or interferon_amount > INTERFERON_MAX:
                        messagebox.showerror("Error", f"Interferon amount must be between {INTERFERON_MIN} and {INTERFERON_MAX}")
                        return

                    if interferon_amount > 0.0:
                        rule_data["interferon_amount"] = round(interferon_amount, 2)

                self.result = {
                    "type": effect_type,
                    "rule": rule_data
                }

            elif effect_type == "modify_transition":
                rule_name = self.modify_rule_var.get().strip()
                if not rule_name:
                    messagebox.showerror("Error", "Rule name is required")
                    return

                modification = {}

                prob_multiplier = self.probability_multiplier_var.get()
                if prob_multiplier != 1.0:
                    modification["probability_multiplier"] = prob_multiplier

                interferon_multiplier = self.interferon_multiplier_var.get()
                if interferon_multiplier != 1.0:
                    modification["interferon_multiplier"] = interferon_multiplier

                if not modification:
                    messagebox.showerror("Error", "At least one multiplier must be different from 1.0")
                    return

                self.result = {
                    "type": "modify_transition",
                    "rule_name": rule_name,
                    "modification": modification
                }

            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {e}")

    def cancel_clicked(self):
        """Handle Cancel button click."""
        self.result = None
        self.dialog.destroy()