"""
Menu and Builder UI Modules

Menu: Main menu with game options
Builder: Virus building interface with gene selection
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
from typing import Optional, Dict

from constants import (
    FONT_TITLE,
    FONT_SUBTITLE,
    FONT_HEADER,
    FONT_BODY,
    FONT_SMALL,
    FONT_ITALIC_SMALL,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_DANGER,
    COLOR_INFO,
    BUILDER_GENE_LIST_HEIGHT,
    BUILDER_DETAILS_TEXT_HEIGHT,
    DEFAULT_SAMPLE_FILENAME,
    FILE_TYPE_JSON,
)
from data_models import GeneDatabaseManager, GeneDatabase
from game_state import GameState
from simulation import VirusBuilder
from ui_base import GameModule, UIUtilities


class MenuModule(GameModule):
    """Main menu module."""

    def setup_ui(self):
        # Title
        title_label = ttk.Label(
            self.frame,
            text="Virus Sandbox",
            font=FONT_TITLE
        )
        title_label.pack(pady=50)

        # Subtitle
        subtitle_label = ttk.Label(
            self.frame,
            text="Create and simulate your own virtual viruses",
            font=FONT_SUBTITLE
        )
        subtitle_label.pack(pady=(0, 50))

        # Menu buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.pack()

        buttons = [
            ("Start New Game", self.start_new_game, 10),
            ("Continue Game", self.continue_game, 5),
            ("Create Sample Database", self.create_sample_database, 5),
            ("Gene Database Editor", self.open_editor, 5),
            ("Exit", self.controller.quit_application, 10),
        ]

        # Create buttons
        start_btn = ttk.Button(
            button_frame,
            text="Start New Game",
            command=self.start_new_game,
            width=20
        )
        start_btn.pack(pady=10)

        continue_btn = ttk.Button(
            button_frame,
            text="Continue Game",
            command=self.continue_game,
            width=20,
            state='disabled'
        )
        continue_btn.pack(pady=5)

        sample_btn = ttk.Button(
            button_frame,
            text="Create Sample Database",
            command=self.create_sample_database,
            width=20
        )
        sample_btn.pack(pady=5)

        editor_btn = ttk.Button(
            button_frame,
            text="Gene Database Editor",
            command=self.open_editor,
            width=20
        )
        editor_btn.pack(pady=5)

        exit_btn = ttk.Button(
            button_frame,
            text="Exit",
            command=self.controller.quit_application,
            width=20
        )
        exit_btn.pack(pady=10)

    def start_new_game(self):
        """Start a new game - first select database, then go to builder."""
        file_path = filedialog.askopenfilename(
            title="Select Gene Database",
            filetypes=FILE_TYPE_JSON,
            initialdir=os.getcwd()
        )

        if file_path:
            try:
                db_manager = GeneDatabaseManager()
                db_manager.load_database(file_path)
                self.controller.start_new_game_with_database(db_manager)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load database:\n{e}")

    def continue_game(self):
        """Continue existing game - placeholder."""
        messagebox.showinfo("Not Implemented", "Continue game functionality will be added later")

    def create_sample_database(self):
        """Create and save a sample database."""
        file_path = filedialog.asksaveasfilename(
            title="Save Sample Database As",
            filetypes=FILE_TYPE_JSON,
            defaultextension=".json",
            initialdir=os.getcwd(),
            initialvalue=DEFAULT_SAMPLE_FILENAME
        )

        if file_path:
            try:
                db_manager = GeneDatabaseManager()
                db_manager.create_sample_database()
                db_manager.save_database(file_path)
                messagebox.showinfo("Success", f"Sample database created: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create sample database:\n{e}")

    def open_editor(self):
        """Open gene editor."""
        self.controller.switch_to_module("editor")


class BuilderModule(GameModule):
    """Virus builder module."""

    def __init__(self, parent, controller):
        self.db_manager: Optional[GeneDatabaseManager] = None
        self.game_state: Optional[GameState] = None
        self.gene_db: Optional[GeneDatabase] = None
        self.virus_builder: Optional[VirusBuilder] = None
        self.current_display_mode = "virus"
        self.current_selected_gene: Optional[str] = None
        super().__init__(parent, controller)

    def set_game_state(self, game_state: GameState):
        """Give the builder access to EP + deck."""
        self.game_state = game_state

        if self.virus_builder:
            self.virus_builder.set_game_state(game_state)
        self.update_virus_display()
        self.update_starter_dropdown()

    def set_database_manager(self, db_manager: GeneDatabaseManager):
        """Called by the controller when a DB is loaded."""
        self.db_manager = db_manager
        self.gene_db = GeneDatabase(db_manager)
        self.virus_builder = VirusBuilder(self.gene_db, self.game_state)

        self.update_gene_list()
        self.update_virus_display()
        self.update_starter_dropdown()

    def setup_ui(self):
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(header_frame, text="Virus Builder", font=FONT_HEADER).pack(side=tk.LEFT)

        # Main content area
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top section - Gene lists
        gene_lists_frame = ttk.Frame(main_frame)
        gene_lists_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        # Left panel - Available genes
        available_frame = ttk.LabelFrame(
            gene_lists_frame,
            text="Available Genes (from your Deck)",
            padding=10
        )
        available_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Search/filter
        search_frame = ttk.Frame(available_frame)
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="Filter:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.update_gene_list())

        # Gene list
        self.available_genes_list = tk.Listbox(
            available_frame,
            selectmode=tk.SINGLE,
            height=BUILDER_GENE_LIST_HEIGHT
        )
        self.available_genes_list.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        UIUtilities.bind_listbox_selection(
            self.available_genes_list,
            self.on_available_gene_select,
            self.handle_available_gene_click
        )

        # Add button
        ttk.Button(
            available_frame,
            text="Add Selected Gene",
            command=self.add_gene
        ).pack(fill=tk.X)

        # Right panel - Selected genes and controls
        selected_frame = ttk.LabelFrame(gene_lists_frame, text="Selected Genes", padding=10)
        selected_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Selected genes list
        self.selected_genes_list = tk.Listbox(
            selected_frame,
            selectmode=tk.SINGLE,
            height=BUILDER_GENE_LIST_HEIGHT
        )
        self.selected_genes_list.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        UIUtilities.bind_listbox_selection(
            self.selected_genes_list,
            self.on_selected_gene_select,
            self.handle_selected_gene_click
        )

        # Remove button
        button_row = ttk.Frame(selected_frame)
        button_row.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(
            button_row,
            text="Remove Selected Gene",
            command=self.remove_gene
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        # Simulation controls
        controls_frame = ttk.LabelFrame(selected_frame, text="Simulation Controls", padding=10)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Starter entity selection
        starter_row = ttk.Frame(controls_frame)
        starter_row.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(starter_row, text="Starting Entity:", font=FONT_SMALL).pack(side=tk.LEFT)
        self.starter_var = tk.StringVar()
        self.starter_dropdown = ttk.Combobox(
            starter_row,
            textvariable=self.starter_var,
            width=25,
            state="readonly"
        )
        self.starter_dropdown.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        self.starter_dropdown.bind('<<ComboboxSelected>>', self.on_starter_selection_changed)

        # Validation indicator
        self.starter_status_label = ttk.Label(
            starter_row,
            text="",
            font=("Arial", 9),
            foreground="red"
        )
        self.starter_status_label.pack(side=tk.LEFT, padx=(5, 0))

        # Rounds remaining counter
        rounds_row = ttk.Frame(controls_frame)
        rounds_row.pack(fill=tk.X, pady=(0, 10))

        self.rounds_label = ttk.Label(
            rounds_row,
            text="Rounds Remaining: --/--",
            font=("Arial", 11, "bold"),
            foreground=COLOR_DANGER
        )
        self.rounds_label.pack(side=tk.LEFT)

        # Help text for rounds
        rounds_help = ttk.Label(
            rounds_row,
            text="(Build → Play cycles)",
            font=FONT_ITALIC_SMALL,
            foreground="gray"
        )
        rounds_help.pack(side=tk.LEFT, padx=(10, 0))

        # EP + Skip Round + Start Simulation
        sim_row = ttk.Frame(controls_frame)
        sim_row.pack(fill=tk.X)

        self.ep_label = ttk.Label(sim_row, text="EP: 0", font=("Arial", 11, "bold"))
        self.ep_label.pack(side=tk.LEFT)

        # Skip Round button
        self.skip_round_button = ttk.Button(
            sim_row,
            text="Skip Round",
            command=self.skip_round
        )
        self.skip_round_button.pack(side=tk.RIGHT, padx=(0, 5))

        self.start_sim_button = ttk.Button(
            sim_row,
            text="Start Simulation",
            command=self.start_simulation
        )
        self.start_sim_button.pack(side=tk.RIGHT)

        # Bottom section - Details panel
        details_frame = ttk.LabelFrame(main_frame, text="Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True)

        # Control buttons for details panel
        details_controls = ttk.Frame(details_frame)
        details_controls.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(details_controls, text="View:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        ttk.Button(
            details_controls,
            text="Show Virus Properties",
            command=self.show_virus_properties
        ).pack(side=tk.LEFT, padx=(10, 5))

        # Status indicator
        self.details_status_label = ttk.Label(
            details_controls,
            text="Showing: Virus Properties",
            font=FONT_ITALIC_SMALL,
            foreground="blue"
        )
        self.details_status_label.pack(side=tk.LEFT, padx=(10, 0))

        # Text area for properties/details
        text_frame = ttk.Frame(details_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.details_text = tk.Text(text_frame, state='disabled', wrap=tk.WORD)
        UIUtilities.style_text_widget(self.details_text)

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.config(yscrollcommand=scrollbar.set)

        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def show(self):
        super().show()
        self.update_gene_list()
        self.update_virus_display()
        self.update_starter_dropdown()

    # =================== GENE SELECTION HANDLERS ===================

    def on_available_gene_select(self, event):
        """Handle selection in available genes list."""
        selection = self.available_genes_list.curselection()
        if not selection:
            return
        self.handle_gene_selection_from_available(selection[0])

    def handle_available_gene_click(self):
        """Handle available gene click with delay."""
        selection = self.available_genes_list.curselection()
        if selection:
            self.handle_gene_selection_from_available(selection[0])

    def handle_gene_selection_from_available(self, index: int):
        """Handle gene selection from available genes list."""
        try:
            display = self.available_genes_list.get(index)
            gene_name = display.rsplit(" (", 1)[0]
            self.show_gene_details(gene_name)
            self.selected_genes_list.selection_clear(0, tk.END)
        except (tk.TclError, IndexError):
            pass

    def on_selected_gene_select(self, event):
        """Handle selection in selected genes list."""
        selection = self.selected_genes_list.curselection()
        if not selection:
            return
        self.handle_gene_selection_from_selected(selection[0])

    def handle_selected_gene_click(self):
        """Handle selected gene click with delay."""
        selection = self.selected_genes_list.curselection()
        if selection:
            self.handle_gene_selection_from_selected(selection[0])

    def handle_gene_selection_from_selected(self, index: int):
        """Handle gene selection from selected genes list."""
        try:
            gene_name = self.selected_genes_list.get(index)
            self.show_gene_details(gene_name)
            self.available_genes_list.selection_clear(0, tk.END)
        except (tk.TclError, IndexError):
            pass

    def show_gene_details(self, gene_name: str):
        """Show details for a specific gene."""
        if not self.db_manager:
            return

        gene = self.db_manager.get_gene(gene_name)
        if not gene:
            return

        self.current_display_mode = "gene"
        self.current_selected_gene = gene_name
        self.details_status_label.config(text=f"Showing: {gene_name}")

        details_text = self.format_gene_details(gene)

        self.details_text.config(state='normal')
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, details_text)
        self.details_text.config(state='disabled')

    def show_virus_properties(self):
        """Show virus properties (default view)."""
        self.current_display_mode = "virus"
        self.current_selected_gene = None
        self.details_status_label.config(text="Showing: Virus Properties")

        self.available_genes_list.selection_clear(0, tk.END)
        self.selected_genes_list.selection_clear(0, tk.END)

        self.update_virus_display()

    def format_gene_details(self, gene: Dict) -> str:
        """Format gene details for display."""
        details = []

        # Basic info
        details.append(f"Gene: {gene['name']}")
        details.append(f"Cost: {gene.get('cost', 0)} EP")

        if gene.get('is_polymerase', False):
            details.append("Type: POLYMERASE GENE")

        details.append("")

        # Description
        description = gene.get('description', 'No description available')
        details.append("Description:")
        details.append(f"  {description}")
        details.append("")

        # Prerequisites
        prereqs = gene.get('requires', [])
        if prereqs:
            details.append("Prerequisites:")
            for req in prereqs:
                details.append(f"  • {req}")
            details.append("")

        # Effects
        effects = gene.get('effects', [])
        if effects:
            details.append("Effects:")
            for i, effect in enumerate(effects, 1):
                effect_desc = self.format_effect_for_details(effect)
                details.append(f"  {i}. {effect_desc}")
                details.append("")
        else:
            details.append("Effects: None")
            details.append("")

        return "\n".join(details)

    def format_effect_for_details(self, effect: Dict) -> str:
        """Format a single effect for detailed display."""
        effect_type = effect.get("type", "unknown")

        if effect_type == "add_transition":
            rule = effect.get("rule", {})
            rule_name = rule.get("name", "Unknown")
            probability = rule.get("probability", 0) * 100
            rule_type = rule.get("rule_type", "per_entity")

            inputs = rule.get("inputs", [])
            outputs = rule.get("outputs", [])

            # Format inputs
            input_desc = []
            consumed_status = None
            for inp in inputs:
                consumed = inp.get("consumed", True)
                if consumed_status is None:
                    consumed_status = consumed
                input_desc.append(f"{inp['count']}x {inp['entity']}")

            if input_desc and consumed_status is not None:
                consumed_note = " (all consumed)" if consumed_status else " (not consumed)"
                input_desc[-1] += consumed_note

            # Format outputs
            output_desc = []
            for out in outputs:
                output_desc.append(f"{out['count']}x {out['entity']}")

            # Build display
            details = [f"Transition: {rule_name}"]
            details.append(f"  Probability: {probability:.1f}% {rule_type}")

            if input_desc:
                if len(input_desc) == 1:
                    details.append(f"  Input: {input_desc[0]}")
                else:
                    details.append(f"  Inputs:")
                    for inp in input_desc:
                        details.append(f"    - {inp}")
            else:
                details.append(f"  Inputs: None")

            if output_desc:
                if len(output_desc) == 1:
                    details.append(f"  Output: {output_desc[0]}")
                else:
                    details.append(f"  Outputs:")
                    for out in output_desc:
                        details.append(f"    - {out}")
            else:
                details.append(f"  Outputs: None")

            interferon_amount = float(rule.get("interferon_amount", 0) or 0)
            if interferon_amount:
                details.append(f"  Interferon: +{interferon_amount:.2f} per application")

            return "\n".join(details)

        elif effect_type == "modify_transition":
            rule_name = effect.get("rule_name", "Unknown")
            modification = effect.get("modification", {})
            multiplier = modification.get("probability_multiplier", 1.0)

            return f"Modify Transition: {rule_name}\n  Probability multiplier: {multiplier}x"

        else:
            return f"Unknown effect type: {effect_type}"

    # =================== STARTER ENTITY MANAGEMENT ===================

    def update_starter_dropdown(self):
        """Update the starter entity dropdown with available options."""
        if not self.game_state or not self.db_manager:
            self.starter_dropdown['values'] = []
            self.starter_var.set("")
            self.starter_status_label.config(text="No database loaded", foreground="red")
            return

        available_starters = self.game_state.get_available_starter_entities()

        if not available_starters:
            self.starter_dropdown['values'] = []
            self.starter_var.set("")
            self.starter_status_label.config(text="No starter entities defined", foreground="red")
            return

        self.starter_dropdown['values'] = available_starters

        current_starter = self.game_state.get_selected_starter_entity()
        if current_starter in available_starters:
            self.starter_var.set(current_starter)
            self.starter_status_label.config(text="✓", foreground="green")
        else:
            self.game_state.set_starter_entity(available_starters[0])
            self.starter_var.set(available_starters[0])
            self.starter_status_label.config(text="✓", foreground="green")

    def on_starter_selection_changed(self, event=None):
        """Handle starter entity selection change."""
        if not self.game_state:
            return

        selected_entity = self.starter_var.get()
        if self.game_state.set_starter_entity(selected_entity):
            self.starter_status_label.config(text="✓", foreground="green")
            if self.current_display_mode == "virus":
                self.update_virus_display()
        else:
            self.starter_status_label.config(text="Invalid selection", foreground="red")

    def validate_starter_selection(self) -> tuple[bool, str]:
        """Validate current starter selection before simulation."""
        if not self.game_state:
            return False, "No game state"
        return self.game_state.validate_starter_entity()

    # =================== ROUNDS COUNTER MANAGEMENT ===================

    def update_rounds_display(self):
        """Update the rounds remaining display and button states."""
        if not self.game_state:
            self.rounds_label.config(text="Rounds Remaining: --/--", foreground="gray")
            self.start_sim_button.config(state='disabled', text="Start Simulation")
            self.skip_round_button.config(state='disabled')
            return

        cycles_used = self.game_state.cycles_used
        cycle_limit = self.game_state.cycle_limit
        remaining = cycle_limit - cycles_used

        if remaining <= 0:
            self.rounds_label.config(
                text=f"Rounds Remaining: 0/{cycle_limit}",
                foreground=COLOR_DANGER
            )
            self.start_sim_button.config(state='disabled', text="No Rounds Left")
            self.skip_round_button.config(state='disabled')
        elif remaining <= 2:
            self.rounds_label.config(
                text=f"Rounds Remaining: {remaining}/{cycle_limit}",
                foreground=COLOR_DANGER
            )
            self.start_sim_button.config(state='normal', text="Start Simulation")
            self.skip_round_button.config(state='normal')
        elif remaining <= 5:
            self.rounds_label.config(
                text=f"Rounds Remaining: {remaining}/{cycle_limit}",
                foreground=COLOR_WARNING
            )
            self.start_sim_button.config(state='normal', text="Start Simulation")
            self.skip_round_button.config(state='normal')
        else:
            self.rounds_label.config(
                text=f"Rounds Remaining: {remaining}/{cycle_limit}",
                foreground=COLOR_SUCCESS
            )
            self.start_sim_button.config(state='normal', text="Start Simulation")
            self.skip_round_button.config(state='normal')

    def update_virus_display(self):
        """Refresh selected genes, capabilities, EP label, and rounds counter."""
        # Selected genes list
        self.selected_genes_list.delete(0, tk.END)
        if self.virus_builder:
            for gene in self.virus_builder.selected_genes:
                gene_name = gene["name"] if isinstance(gene, dict) else str(gene)
                self.selected_genes_list.insert(tk.END, gene_name)

        # Update details display based on current mode
        if self.current_display_mode == "virus":
            self.update_virus_capabilities_display()
        elif self.current_display_mode == "gene" and self.current_selected_gene:
            self.show_gene_details(self.current_selected_gene)

        # EP label
        current_ep = self.game_state.ep if self.game_state else 0
        if self.game_state:
            starting_count = self.game_state.get_starting_entity_count()
            if starting_count > 10:
                bonus = starting_count - 10
                self.ep_label.config(text=f"EP: {current_ep} | Start: {starting_count} (+{bonus})")
            else:
                self.ep_label.config(text=f"EP: {current_ep}")
        else:
            self.ep_label.config(text=f"EP: {current_ep}")

        # Update rounds counter
        self.update_rounds_display()

    def update_virus_capabilities_display(self):
        """Update the virus capabilities display."""
        caps = self.virus_builder.get_virus_capabilities() if self.virus_builder else {
            "starting_entities": {},
            "possible_entities": [],
            "transition_rules": []
        }

        self.details_text.config(state='normal')
        self.details_text.delete(1.0, tk.END)

        details = []

        # Starting entities
        if caps["starting_entities"]:
            details.append("=== STARTING ENTITIES ===")
            for entity, count in caps["starting_entities"].items():
                details.append(f"  {count}x {entity}")
            details.append("")

        # All possible entities
        if caps["possible_entities"]:
            details.append("=== ALL POSSIBLE ENTITIES ===")
            for entity in sorted(caps["possible_entities"]):
                details.append(f"  • {entity}")
            details.append("")

        # All transition rules
        if caps["transition_rules"]:
            details.append("=== VIRUS TRANSITIONS ===")
            for i, rule in enumerate(caps["transition_rules"], 1):
                rule_name = rule.get("name", f"Rule {i}")
                probability = rule.get("probability", 0) * 100
                rule_type = rule.get("rule_type", "per_entity")

                details.append(f"{i}. {rule_name}")
                details.append(f"   Probability: {probability:.1f}% {rule_type}")

                # Inputs
                inputs = rule.get("inputs", [])
                if inputs:
                    if len(inputs) == 1:
                        inp = inputs[0]
                        consumed = " (consumed)" if inp.get("consumed", True) else " (not consumed)"
                        details.append(f"   Input: {inp['count']}x {inp['entity']}{consumed}")
                    else:
                        consumed_status = inputs[0].get("consumed", True) if inputs else True
                        consumed_note = " (all consumed)" if consumed_status else " (none consumed)"
                        details.append(f"   Inputs{consumed_note}:")
                        for inp in inputs:
                            details.append(f"     - {inp['count']}x {inp['entity']}")

                # Outputs
                outputs = rule.get("outputs", [])
                if outputs:
                    if len(outputs) == 1:
                        out = outputs[0]
                        details.append(f"   Output: {out['count']}x {out['entity']}")
                    else:
                        details.append(f"   Outputs:")
                        for out in outputs:
                            details.append(f"     - {out['count']}x {out['entity']}")

                interferon_amount = float(rule.get("interferon_amount", 0) or 0)
                if interferon_amount:
                    details.append(f"   Interferon: +{interferon_amount:.2f} per application")

                details.append("")
        else:
            details.append("=== VIRUS TRANSITIONS ===")
            details.append("No special transitions defined.")
            details.append("(Only natural degradation will occur)")
            details.append("")

        # Selected genes
        if self.virus_builder and self.virus_builder.selected_genes:
            details.append("=== SELECTED GENES ===")
            for gene in self.virus_builder.selected_genes:
                gene_name = gene["name"] if isinstance(gene, dict) else str(gene)
                if gene.get("is_polymerase", False):
                    details.append(f"  • {gene_name} (POLYMERASE)")
                else:
                    details.append(f"  • {gene_name}")
        else:
            details.append("=== SELECTED GENES ===")
            details.append("No genes selected (basic virus only)")

        self.details_text.insert(1.0, "\n".join(details))
        self.details_text.config(state='disabled')

    # =================== CORE INTERACTIONS ===================

    def update_gene_list(self):
        """Populate Available Genes limited to the player's deck."""
        if not self.gene_db:
            return

        filter_text = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""

        if self.game_state and self.game_state.deck:
            candidate_names = list(self.game_state.deck)
        else:
            candidate_names = []

        available = []
        for name in sorted(candidate_names):
            if filter_text and filter_text not in name.lower():
                continue
            gene = self.db_manager.get_gene(name) if self.db_manager else None
            if not gene:
                continue
            available.append(name)

        self.available_genes_list.delete(0, tk.END)
        for name in available:
            cost = 0
            if self.db_manager:
                g = self.db_manager.get_gene(name)
                if g:
                    cost = g.get("cost", 0)
            self.available_genes_list.insert(tk.END, f"{name} ({cost})")

    def add_gene(self):
        """Add the selected gene."""
        if not self.virus_builder or not self.db_manager:
            return

        sel = self.available_genes_list.curselection()
        if not sel:
            messagebox.showinfo("Add Gene", "Please select a gene from your deck.")
            self.update_virus_display()
            return

        display = self.available_genes_list.get(sel[0])
        gene_name = display.rsplit(" (", 1)[0]

        if not self.game_state:
            messagebox.showwarning("No Game State", "Game state not initialized.")
            self.update_virus_display()
            return

        if not self.game_state.can_install_gene_this_round():
            messagebox.showinfo("Install limit", "You can only install one gene per round.")
            self.update_virus_display()
            return

        # Validate with the builder
        ok, reason = self.virus_builder.can_add_gene(gene_name)

        if not ok:
            if reason == "polymerase_limit":
                current_polymerase = self.virus_builder.get_selected_polymerase_gene()
                if current_polymerase:
                    messagebox.showerror(
                        "Polymerase Gene Limit",
                        "Only one polymerase gene can be installed at a time.\n\n"
                        f"Currently installed: {current_polymerase}\n"
                        f"Trying to add: {gene_name}\n\n"
                        "Remove the existing polymerase gene first."
                    )
                else:
                    messagebox.showerror("Cannot Add Gene", f"Unable to add '{gene_name}'.")
            elif reason == "already_installed":
                messagebox.showinfo("Already Installed", f"'{gene_name}' is already installed.")
            elif reason == "missing_prerequisites":
                messagebox.showerror("Missing Prerequisites", f"'{gene_name}' requires other genes first.")
            elif reason == "unknown_gene":
                messagebox.showerror("Unknown Gene", f"'{gene_name}' was not found.")
            else:
                messagebox.showerror("Cannot Add Gene", f"Unable to add '{gene_name}'.")
            self.update_virus_display()
            return

        # Check and spend EP
        cost = self.game_state.get_gene_cost(gene_name)
        if not messagebox.askyesno("Confirm Purchase", f"Spend {cost} EP to add '{gene_name}'?"):
            self.update_virus_display()
            return

        if not self.game_state.can_afford_insert(gene_name):
            messagebox.showwarning("Not enough EP", f"You need {cost} EP for {gene_name}.")
            self.update_virus_display()
            return

        if not self.game_state.spend_for_insert(gene_name):
            messagebox.showwarning("EP Error", "Could not spend EP for this gene.")
            self.update_virus_display()
            return

        self.game_state.record_gene_install()

        success = self.virus_builder.add_gene(gene_name)
        if not success:
            messagebox.showerror(
                "Unexpected Error",
                f"Adding '{gene_name}' failed after EP was spent."
            )
            self.update_virus_display()
            return

        if gene_name not in self.game_state.installed_genes:
            self.game_state.installed_genes.append(gene_name)

        self.update_virus_display()

    def remove_gene(self):
        """Remove the selected gene."""
        if not self.virus_builder:
            return

        sel = self.selected_genes_list.curselection()
        if not sel:
            messagebox.showinfo("Remove Gene", "Please select a gene to remove.")
            return

        gene_name = self.selected_genes_list.get(sel[0])

        if not self.game_state:
            messagebox.showwarning("No Game State", "Game state not initialized.")
            return

        cost = self.game_state.get_remove_cost(gene_name)

        if not self.game_state.can_afford_remove(gene_name):
            messagebox.showwarning(
                "Not enough EP",
                f"Removing '{gene_name}' costs {cost} EP, but you only have {self.game_state.ep} EP."
            )
            return

        if not messagebox.askyesno("Confirm Removal", f"Spend {cost} EP to remove '{gene_name}'?"):
            return

        if not self.game_state.spend_for_remove(gene_name):
            messagebox.showwarning("EP Error", "Could not spend EP to remove this gene.")
            return

        self.virus_builder.remove_gene(gene_name)

        if gene_name in self.game_state.installed_genes:
            self.game_state.installed_genes.remove(gene_name)

        self.update_virus_display()

    # =================== SKIP ROUND FUNCTIONALITY ===================

    def skip_round(self):
        """Skip the current round without playing a simulation."""
        if not self.game_state:
            messagebox.showwarning("No Game State", "Game state not initialized.")
            return

        if self.game_state.cycles_used >= self.game_state.cycle_limit:
            messagebox.showwarning(
                "No Rounds Left",
                f"You have used all {self.game_state.cycle_limit} available rounds.\n"
                "This game session is complete."
            )
            return

        remaining_rounds = self.game_state.cycle_limit - self.game_state.cycles_used
        if not messagebox.askyesno(
                "Skip Round",
                f"Skip this round without playing a simulation?\n\n"
                f"This will consume 1 of your {remaining_rounds} remaining rounds, "
                f"but you'll still get a gene offer."
        ):
            return

        self.controller.skip_round()

    # =================== START SIMULATION ===================

    def start_simulation(self):
        """Build a blueprint and start Play."""
        if not self.virus_builder:
            messagebox.showwarning("No Virus", "Please add genes to build your virus.")
            return

        if self.game_state and self.game_state.cycles_used >= self.game_state.cycle_limit:
            messagebox.showwarning(
                "No Rounds Left",
                f"You have used all {self.game_state.cycle_limit} available rounds.\n"
                "This game session is complete."
            )
            return

        # Validate starter entity
        is_valid, error_msg = self.validate_starter_selection()
        if not is_valid:
            messagebox.showerror("Invalid Starter Entity", f"Cannot start simulation:\n{error_msg}")
            return

        blueprint = self.virus_builder.get_virus_capabilities()

        if not blueprint.get("starting_entities"):
            messagebox.showerror("No Starting Entities", "Virus blueprint has no starting entities defined.")
            return

        self.controller.start_simulation(blueprint)