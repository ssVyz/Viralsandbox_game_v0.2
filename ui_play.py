"""
Play Module - Virus Simulation Display

Handles simulation execution, visualization, and result display.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import time
from typing import Optional, Dict, List

from constants import (
    FONT_HEADER,
    FONT_BODY,
    FONT_SMALL,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_DANGER,
    COLOR_INFO,
    GRAPH_HEIGHT,
    GRAPH_MAX_HISTORY,
    GRAPH_MARGIN_LEFT,
    GRAPH_MARGIN_RIGHT,
    GRAPH_MARGIN_TOP,
    GRAPH_MARGIN_BOTTOM,
    GRAPH_GRID_LINES_Y,
    GRAPH_GRID_LINES_X,
    COLOR_GRAPH_VIRION,
    COLOR_GRAPH_RNA,
    COLOR_GRAPH_DNA,
    COLOR_GRAPH_PROTEIN,
    COLOR_BORDER,
    DRAMATIC_DISPLAY_DELAY,
    VICTORY_ENTITY_THRESHOLD,
    VICTORY_DIALOG_WIDTH,
    VICTORY_DIALOG_HEIGHT,
    INTERFERON_THRESHOLD_HIGH,
    INTERFERON_THRESHOLD_MEDIUM,
    INTERFERON_THRESHOLD_LOW,
)
from simulation import ViralSimulation
from game_state import GameState
from ui_base import GameModule, UIUtilities, CustomStyles


class PlayModule(GameModule):
    """Virus simulation play module with dramatic turn display and line graph."""

    def __init__(self, parent, controller):
        self.simulation: Optional[ViralSimulation] = None
        self.db_manager = None
        self.game_state: Optional[GameState] = None
        self.game_won = False
        self.simulation_active = False
        self.virus_blueprint: Optional[Dict] = None

        # Entity type tracking for line graph
        self.entity_type_history = {
            "virion": [],
            "RNA": [],
            "DNA": [],
            "protein": []
        }
        self.turn_numbers: List[int] = []
        self.max_history_length = GRAPH_MAX_HISTORY

        super().__init__(parent, controller)

    def set_game_state(self, game_state: GameState):
        """Set game state reference."""
        self.game_state = game_state

    def set_database_manager(self, db_manager):
        """Set database manager reference."""
        self.db_manager = db_manager

    def setup_ui(self):
        # Header
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=tk.X, padx=15, pady=10)

        title_label = ttk.Label(header_frame, text="Virus Simulation", font=("Arial", 18, "bold"))
        title_label.pack(side=tk.LEFT)

        # Back to builder button
        self.exit_btn = ttk.Button(
            header_frame,
            text="<-- Return to Builder",
            command=self.exit_to_builder,
            style="Accent.TButton"
        )
        self.exit_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Status bar with turn counter
        status_frame = ttk.Frame(self.frame, style="Card.TFrame")
        status_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        status_info_frame = ttk.Frame(status_frame)
        status_info_frame.pack(pady=10)

        self.turn_label = ttk.Label(
            status_info_frame,
            text="Turn: 0",
            font=("Arial", 16, "bold"),
            foreground=COLOR_INFO
        )
        self.turn_label.pack(side=tk.LEFT, padx=(0, 30))

        # Interferon level indicator
        self.interferon_label = ttk.Label(
            status_info_frame,
            text="Interferon: 0.0/100",
            font=("Arial", 14, "bold"),
            foreground=COLOR_DANGER
        )
        self.interferon_label.pack(side=tk.LEFT)

        # Main content area
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        # Left panel - Simulation console
        console_frame = ttk.LabelFrame(main_frame, text="Simulation Log", padding=15)
        console_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.console_text = scrolledtext.ScrolledText(
            console_frame,
            state='disabled',
            wrap=tk.WORD
        )
        UIUtilities.style_console_widget(self.console_text)
        self.console_text.pack(fill=tk.BOTH, expand=True)

        # Right panel - Controls and stats
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Simulation controls
        controls_frame = ttk.LabelFrame(right_panel, text="Simulation Controls", padding=15)
        controls_frame.pack(fill=tk.X, pady=(0, 15))

        # Primary action buttons
        primary_buttons_frame = ttk.Frame(controls_frame)
        primary_buttons_frame.pack(fill=tk.X, pady=(0, 15))

        self.next_turn_btn = ttk.Button(
            primary_buttons_frame,
            text="> Next Turn",
            command=self.next_turn,
            style="Accent.TButton"
        )
        self.next_turn_btn.pack(fill=tk.X, pady=(0, 8))

        # Multi-turn advancement
        multi_turn_frame = ttk.LabelFrame(controls_frame, text="Fast Forward", padding=10)
        multi_turn_frame.pack(fill=tk.X, pady=(0, 15))

        fast_row1 = ttk.Frame(multi_turn_frame)
        fast_row1.pack(fill=tk.X, pady=(0, 5))

        self.advance_3_btn = ttk.Button(
            fast_row1,
            text=">> +3 Turns",
            command=lambda: self.advance_multiple_turns(3),
            width=12
        )
        self.advance_3_btn.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

        self.advance_10_btn = ttk.Button(
            fast_row1,
            text=">> +10 Turns",
            command=lambda: self.advance_multiple_turns(10),
            width=12
        )
        self.advance_10_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        warning_label = ttk.Label(
            multi_turn_frame,
            text="Warning: Multi-turn advancement cannot be undone",
            font=("Arial", 8),
            foreground=COLOR_DANGER
        )
        warning_label.pack(pady=(5, 0))

        # Entity type line graph
        graph_frame = ttk.LabelFrame(
            right_panel,
            text="Entity Populations (Last 50 Turns)",
            padding=15
        )
        graph_frame.pack(fill=tk.X, pady=(0, 15))

        # Current count labels
        self.entity_labels = {}
        labels_frame = ttk.Frame(graph_frame)
        labels_frame.pack(fill=tk.X, pady=(0, 10))

        self.entity_configs = [
            ("virion", "Virions", COLOR_GRAPH_VIRION),
            ("RNA", "RNA", COLOR_GRAPH_RNA),
            ("DNA", "DNA", COLOR_GRAPH_DNA),
            ("protein", "Proteins", COLOR_GRAPH_PROTEIN)
        ]

        for i, (entity_type, display_name, color) in enumerate(self.entity_configs):
            label_frame = ttk.Frame(labels_frame)
            if i < 2:
                label_frame.grid(row=0, column=i, sticky=tk.W, padx=(0, 20))
            else:
                label_frame.grid(row=1, column=i - 2, sticky=tk.W, padx=(0, 20))

            color_canvas = tk.Canvas(label_frame, width=12, height=12, highlightthickness=0)
            color_canvas.pack(side=tk.LEFT, padx=(0, 5))
            color_canvas.create_rectangle(0, 0, 12, 12, fill=color, outline="")

            self.entity_labels[entity_type] = ttk.Label(
                label_frame,
                text=f"{display_name}: 0",
                font=("Arial", 10, "bold")
            )
            self.entity_labels[entity_type].pack(side=tk.LEFT)

        # Line graph canvas
        self.graph_canvas = tk.Canvas(
            graph_frame,
            height=GRAPH_HEIGHT,
            bg="white",
            relief=tk.SUNKEN,
            borderwidth=1
        )
        self.graph_canvas.pack(fill=tk.X, pady=(10, 0))

        # Genes dialog button
        genes_frame = ttk.LabelFrame(right_panel, text="Virus Configuration", padding=15)
        genes_frame.pack(fill=tk.X, pady=(0, 15))

        self.show_genes_btn = ttk.Button(
            genes_frame,
            text="Show Installed Genes",
            command=self.show_genes_dialog
        )
        self.show_genes_btn.pack(fill=tk.X)

    def reset_entity_type_history(self):
        """Reset historical data for entity type graph."""
        self.entity_type_history = {"virion": [], "RNA": [], "DNA": [], "protein": []}
        self.turn_numbers = []

    def update_entity_type_graph(self, entities: Dict[str, int], turn_number: int):
        """Update the entity type line graph with current entity counts."""
        if not self.db_manager:
            return

        # Count entities by type
        type_counts = {"virion": 0, "RNA": 0, "DNA": 0, "protein": 0}

        for entity_name, count in entities.items():
            entity_data = self.db_manager.get_entity(entity_name)
            if entity_data:
                entity_class = entity_data.get("entity_class", "unknown")
                if entity_class in type_counts:
                    type_counts[entity_class] += count

        # Add current data to history
        self.turn_numbers.append(turn_number)
        for entity_type in self.entity_type_history:
            self.entity_type_history[entity_type].append(type_counts[entity_type])

        # Maintain sliding window
        if len(self.turn_numbers) > self.max_history_length:
            self.turn_numbers = self.turn_numbers[-self.max_history_length:]
            for entity_type in self.entity_type_history:
                self.entity_type_history[entity_type] = \
                    self.entity_type_history[entity_type][-self.max_history_length:]

        # Update current count labels
        for entity_type, display_name, color in self.entity_configs:
            current_count = type_counts[entity_type]
            self.entity_labels[entity_type].config(text=f"{display_name}: {current_count}")

        self.draw_line_graph()

    def draw_line_graph(self):
        """Draw the line graph showing entity population history."""
        canvas = self.graph_canvas
        canvas.delete("all")

        canvas.update_idletasks()
        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width <= 1 or height <= 1:
            return

        graph_width = width - GRAPH_MARGIN_LEFT - GRAPH_MARGIN_RIGHT
        graph_height = height - GRAPH_MARGIN_TOP - GRAPH_MARGIN_BOTTOM

        if graph_width <= 0 or graph_height <= 0:
            return

        if not self.turn_numbers:
            canvas.create_text(width // 2, height // 2, text="No data yet", fill="gray", font=("Arial", 12))
            return

        min_turn = min(self.turn_numbers)
        max_turn = max(self.turn_numbers)

        max_value = 0
        for entity_type in self.entity_type_history:
            if self.entity_type_history[entity_type]:
                max_value = max(max_value, max(self.entity_type_history[entity_type]))

        if max_value == 0:
            max_value = 10

        # Draw grid
        self._draw_grid(canvas, GRAPH_MARGIN_LEFT, GRAPH_MARGIN_TOP, graph_width, graph_height)

        # Draw axes
        canvas.create_line(
            GRAPH_MARGIN_LEFT, GRAPH_MARGIN_TOP,
            GRAPH_MARGIN_LEFT, GRAPH_MARGIN_TOP + graph_height,
            fill="black", width=2
        )
        canvas.create_line(
            GRAPH_MARGIN_LEFT, GRAPH_MARGIN_TOP + graph_height,
            GRAPH_MARGIN_LEFT + graph_width, GRAPH_MARGIN_TOP + graph_height,
            fill="black", width=2
        )

        # Draw axis labels
        self._draw_axis_labels(
            canvas, GRAPH_MARGIN_LEFT, GRAPH_MARGIN_TOP,
            graph_width, graph_height, min_turn, max_turn, max_value
        )

        # Draw lines for each entity type
        for entity_type, display_name, color in self.entity_configs:
            if entity_type in self.entity_type_history and self.entity_type_history[entity_type]:
                self._draw_entity_line(
                    canvas, entity_type, color,
                    GRAPH_MARGIN_LEFT, GRAPH_MARGIN_TOP,
                    graph_width, graph_height, min_turn, max_turn, max_value
                )

    def _draw_grid(self, canvas, margin_left, margin_top, graph_width, graph_height):
        """Draw background grid lines."""
        num_y_lines = GRAPH_GRID_LINES_Y
        for i in range(num_y_lines + 1):
            y = margin_top + (i * graph_height / num_y_lines)
            canvas.create_line(
                margin_left, y,
                margin_left + graph_width, y,
                fill=COLOR_BORDER, width=1
            )

        num_x_lines = min(GRAPH_GRID_LINES_X, len(self.turn_numbers))
        if num_x_lines > 1:
            for i in range(num_x_lines + 1):
                x = margin_left + (i * graph_width / num_x_lines)
                canvas.create_line(
                    x, margin_top,
                    x, margin_top + graph_height,
                    fill=COLOR_BORDER, width=1
                )

    def _draw_axis_labels(
        self, canvas, margin_left, margin_top,
        graph_width, graph_height, min_turn, max_turn, max_value
    ):
        """Draw axis labels and tick marks."""
        num_y_labels = GRAPH_GRID_LINES_Y
        for i in range(num_y_labels + 1):
            y = margin_top + graph_height - (i * graph_height / num_y_labels)
            value = int(i * max_value / num_y_labels)
            canvas.create_text(
                margin_left - 5, y,
                text=str(value),
                anchor=tk.E,
                font=("Arial", 8),
                fill="black"
            )

        if len(self.turn_numbers) > 1:
            labels_to_show = []
            if len(self.turn_numbers) <= 10:
                labels_to_show = list(range(len(self.turn_numbers)))
            else:
                labels_to_show = [
                    0,
                    len(self.turn_numbers) // 4,
                    len(self.turn_numbers) // 2,
                    3 * len(self.turn_numbers) // 4,
                    len(self.turn_numbers) - 1
                ]

            for i in labels_to_show:
                if i < len(self.turn_numbers):
                    turn_num = self.turn_numbers[i]
                    x = margin_left + (i * graph_width / (len(self.turn_numbers) - 1))
                    canvas.create_text(
                        x, margin_top + graph_height + 15,
                        text=str(turn_num),
                        anchor=tk.N,
                        font=("Arial", 8),
                        fill="black"
                    )

        # Axis titles
        canvas.create_text(
            margin_left + graph_width // 2,
            margin_top + graph_height + 25,
            text="Turn",
            anchor=tk.N,
            font=("Arial", 10, "bold")
        )
        canvas.create_text(
            15, margin_top + graph_height // 2,
            text="Count",
            anchor=tk.CENTER,
            font=("Arial", 10, "bold"),
            angle=90
        )

    def _draw_entity_line(
        self, canvas, entity_type, color,
        margin_left, margin_top, graph_width, graph_height,
        min_turn, max_turn, max_value
    ):
        """Draw line and dots for a specific entity type."""
        history = self.entity_type_history[entity_type]
        if len(history) < 2:
            return

        points = []
        for i, count in enumerate(history):
            x = margin_left + (i * graph_width / (len(history) - 1))
            y = margin_top + graph_height - (count * graph_height / max_value)
            points.extend([x, y])

        if len(points) >= 4:
            canvas.create_line(points, fill=color, width=2, smooth=False)

        for i in range(0, len(points), 2):
            x, y = points[i], points[i + 1]
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline="white", width=1)

    def show_genes_dialog(self):
        """Show dialog with installed genes for this simulation."""
        if not hasattr(self, 'virus_blueprint'):
            messagebox.showinfo("No Genes", "No virus configuration available.")
            return

        genes = self.virus_blueprint.get("genes", [])
        if not genes:
            messagebox.showinfo("No Genes", "This virus has no installed genes (basic capsid only).")
            return

        dialog = tk.Toplevel(self.frame)
        dialog.title("Installed Genes")
        dialog.transient(self.frame)
        dialog.grab_set()

        UIUtilities.center_dialog(dialog, 500, 400)

        # Header
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(header_frame, text="Installed Genes", font=("Arial", 14, "bold")).pack()
        ttk.Label(
            header_frame,
            text=f"This virus has {len(genes)} installed genes:",
            font=("Arial", 11)
        ).pack(pady=(10, 0))

        # Gene list
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        gene_listbox = tk.Listbox(listbox_frame, font=("Arial", 10))
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=gene_listbox.yview)
        gene_listbox.config(yscrollcommand=scrollbar.set)

        gene_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for gene_name in genes:
            if self.db_manager:
                gene_data = self.db_manager.get_gene(gene_name)
                if gene_data:
                    cost = gene_data.get('cost', 0)
                    is_polymerase = gene_data.get('is_polymerase', False)

                    if is_polymerase:
                        display_text = f"{gene_name} ({cost} EP, Polymerase)"
                    else:
                        display_text = f"{gene_name} ({cost} EP)"

                    gene_listbox.insert(tk.END, display_text)
                else:
                    gene_listbox.insert(tk.END, f"{gene_name} (Unknown gene)")
            else:
                gene_listbox.insert(tk.END, gene_name)

        # Close button
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack()

        dialog.focus_set()
        dialog.bind('<Escape>', lambda e: dialog.destroy())

    def update_entities_display(self, entities: Dict[str, int]):
        """Update entity display using the line graph."""
        turn_number = self.simulation.turn_count if self.simulation else 0
        self.update_entity_type_graph(entities, turn_number)

    def exit_to_builder(self):
        """Mark offer pending, check milestones, reset graph, return to Builder."""
        if self.game_won:
            messagebox.showinfo(
                "Game Complete",
                "This simulation session is complete! You achieved the victory condition.\n\n"
                "To play again, return to the main menu and start a new game."
            )
            return

        self.reset_entity_type_history()

        if self.game_state:
            self.game_state.offer_pending = True
            self._check_and_show_milestone_achievements_blocking()

        self.controller.switch_to_module("builder")

    def advance_multiple_turns(self, num_turns: int):
        """Advance simulation by multiple turns - shows full output instantly."""
        if not self.simulation_active or not self.simulation or self.game_won:
            return

        self.set_control_buttons_state('disabled')

        try:
            for turn_num in range(num_turns):
                if not self.simulation_active or self.simulation.is_simulation_over() or self.game_won:
                    break

                self._process_single_turn_fast()

                if self._check_victory_condition():
                    break

                self.frame.update_idletasks()

            if self.game_won:
                self.show_victory_dialog()
            elif self.simulation.is_simulation_over():
                self.add_console_message("\n" + "=" * 50)
                self.add_console_message("EXTINCTION EVENT")
                self.add_console_message("=" * 50)
                self.add_console_message("No entities remaining - Your virus has gone extinct!")
                self.add_console_message("The simulation has ended.")
                self.add_console_message("")
                self.add_console_message("You can review the simulation results above.")
                self.add_console_message("When ready, confirm to return to the Builder.")

                self.simulation_active = False
                self.show_extinction_dialog()
            else:
                self.set_control_buttons_state('normal')

        except Exception as e:
            self.add_console_message(f"\nError during multi-turn advancement: {e}")
            self.set_control_buttons_state('normal')

    def _process_single_turn_fast(self):
        """Process a single turn quickly (for multi-turn advancement)."""
        turn_log = self.simulation.process_turn()

        entities_created_this_turn = self._extract_entities_created(turn_log)

        self.turn_label.config(text=f"Turn: {self.simulation.turn_count}")
        self.update_interferon_display()

        if self.game_state:
            self.game_state.update_turn_count(self.simulation.turn_count)
            self.game_state.update_entity_counts(self.simulation.entities, entities_created_this_turn)

        for message in turn_log:
            self.add_console_message(message)

        self.update_entities_display(self.simulation.entities)

    def _process_single_turn_dramatic(self):
        """Process a single turn with dramatic timing."""
        turn_log = self.simulation.process_turn()

        entities_created_this_turn = self._extract_entities_created(turn_log)

        self.turn_label.config(text=f"Turn: {self.simulation.turn_count}")
        self.update_interferon_display()

        if self.game_state:
            self.game_state.update_turn_count(self.simulation.turn_count)
            self.game_state.update_entity_counts(self.simulation.entities, entities_created_this_turn)

        self._display_turn_log_dramatically(turn_log)

        self.update_entities_display(self.simulation.entities)

    def _display_turn_log_dramatically(self, turn_log: List[str]):
        """Display turn log with dramatic pauses between sections."""
        if not turn_log:
            return

        sections = self._parse_turn_log_into_sections(turn_log)

        for i, section in enumerate(sections):
            for message in section:
                self.add_console_message(message)

            if i < len(sections) - 1:
                self.frame.update_idletasks()
                self.frame.after(100)
                time.sleep(DRAMATIC_DISPLAY_DELAY)

    def _parse_turn_log_into_sections(self, turn_log: List[str]) -> List[List[str]]:
        """Parse turn log into logical sections for dramatic display."""
        sections = []
        current_section = []

        in_events = False
        in_population_end = False
        current_event = []

        for line in turn_log:
            line_content = line.strip()

            if "TURN" in line_content and ("=" in line_content or "-" in line_content):
                if current_section:
                    sections.append(current_section)
                current_section = [line]
                in_events = False
                in_population_end = False
            elif line_content.startswith("TURN ") and not in_events and not in_population_end:
                current_section.append(line)
            elif "Events this turn:" in line_content:
                if current_section:
                    sections.append(current_section)
                current_section = [line]
                in_events = True
                in_population_end = False
            elif in_events and line_content.startswith("[") and "]" in line_content:
                if current_event:
                    sections.append(current_event)
                current_event = [line]
            elif in_events and current_event and (
                line_content.startswith("Consumed:") or
                line_content.startswith("Produced:") or
                line_content.startswith("Degraded:") or
                line_content.startswith("- ") or
                line_content.startswith("+ ") or
                line_content.startswith("  ") or
                "No events occurred" in line_content
            ):
                current_event.append(line)
            elif "Population at end:" in line_content:
                if current_event:
                    sections.append(current_event)
                    current_event = []
                elif in_events and current_section:
                    sections.append(current_section)
                current_section = [line]
                in_events = False
                in_population_end = True
            elif in_population_end:
                current_section.append(line)
            else:
                if current_event:
                    current_event.append(line)
                else:
                    current_section.append(line)

        if current_event:
            sections.append(current_event)
        if current_section:
            sections.append(current_section)

        return sections

    def set_control_buttons_state(self, state: str):
        """Enable or disable all control buttons."""
        buttons = [self.next_turn_btn, self.advance_3_btn, self.advance_10_btn]
        for button in buttons:
            button.config(state=state)

    def set_virus_blueprint(self, virus_blueprint: Dict):
        """Set the virus blueprint and initialize simulation."""
        self.virus_blueprint = virus_blueprint
        self.initialize_simulation()

    def initialize_simulation(self):
        """Initialize the simulation with virus blueprint."""
        if not hasattr(self, 'virus_blueprint'):
            self.virus_blueprint = {
                "starting_entities": {"unenveloped virion (extracellular)": 10},
                "possible_entities": ["unenveloped virion (extracellular)"],
                "transition_rules": [],
                "genes": []
            }

        self.simulation = ViralSimulation(self.virus_blueprint)
        if hasattr(self.simulation, 'db_manager'):
            self.simulation.db_manager = self.db_manager
        else:
            self.simulation.db_manager = self.db_manager
        self.simulation_active = True
        self.game_won = False

        self.reset_entity_type_history()

        self.set_control_buttons_state('normal')

        if self.game_state:
            self.game_state.reset_milestone_progress()

        self.console_text.config(state='normal')
        self.console_text.delete(1.0, tk.END)
        self.console_text.config(state='disabled')

        self.turn_label.config(text=f"Turn: {self.simulation.turn_count}")
        self.update_interferon_display()
        self.update_entities_display(self.simulation.entities)

        self.add_console_message("=" * 70)
        self.add_console_message("  VIRUS SIMULATION INITIALIZED")
        self.add_console_message("=" * 70)
        self.add_console_message("Initial infection beginning...")

        if self.virus_blueprint.get("genes"):
            self.add_console_message(f"Virus genes: {', '.join(self.virus_blueprint['genes'])}")
        else:
            self.add_console_message("Virus has no genes - only basic structure")

        total_entities = sum(self.simulation.entities.values())
        self.add_console_message(f"Starting population: {total_entities} entities")
        self.add_console_message("")

        if self.game_state:
            self.game_state.update_turn_count(0)
            self.game_state.update_entity_counts(self.simulation.entities)

    def update_interferon_display(self):
        """Update the interferon level indicator."""
        if not self.simulation:
            self.interferon_label.config(text="Interferon: --/100", foreground="#6b7280")
            return

        interferon_level = self.simulation.get_interferon_level()

        if interferon_level >= INTERFERON_THRESHOLD_HIGH:
            color = COLOR_DANGER
            intensity = "HIGH"
        elif interferon_level >= INTERFERON_THRESHOLD_MEDIUM:
            color = COLOR_WARNING
        elif interferon_level >= INTERFERON_THRESHOLD_LOW:
            color = "#ca8a04"
        elif interferon_level > 0.0:
            color = COLOR_SUCCESS
        else:
            color = "#6b7280"
            intensity = "NONE"

        if interferon_level >= INTERFERON_THRESHOLD_HIGH:
            display_text = f"Interferon: {interferon_level:.1f}/100 ({intensity})"
        else:
            display_text = f"Interferon: {interferon_level:.1f}/100"

        self.interferon_label.config(text=display_text, foreground=color)

    def next_turn(self):
        """Process next turn of simulation with dramatic display."""
        if not self.simulation_active or not self.simulation or self.game_won:
            return

        self._process_single_turn_dramatic()

        if self._check_victory_condition():
            self.show_victory_dialog()
            return

        if self.simulation.is_simulation_over():
            self.add_console_message("\n" + "=" * 50)
            self.add_console_message("EXTINCTION EVENT")
            self.add_console_message("=" * 50)
            self.add_console_message("No entities remaining - Your virus has gone extinct!")
            self.add_console_message("The simulation has ended.")
            self.add_console_message("")
            self.add_console_message("You can review the simulation results above.")
            self.add_console_message("When ready, confirm to return to the Builder.")

            self.simulation_active = False
            self.set_control_buttons_state('disabled')

            self.show_extinction_dialog()

    def _check_victory_condition(self) -> bool:
        """Check if victory condition has been reached."""
        if not self.simulation or self.game_won:
            return False

        total_entities = sum(self.simulation.entities.values())
        if total_entities >= VICTORY_ENTITY_THRESHOLD:
            self.game_won = True
            self.simulation_active = False
            self.set_control_buttons_state('disabled')
            self.exit_btn.config(state='disabled')
            return True
        return False

    def show_victory_dialog(self):
        """Show congratulatory dialog when victory condition is reached."""
        self.add_console_message("\n" + "=" * 50)
        self.add_console_message("RUNAWAY REACTION ACHIEVED!")
        self.add_console_message("=" * 50)
        self.add_console_message(f"You have reached {VICTORY_ENTITY_THRESHOLD} entities!")
        self.add_console_message("Congratulations! Your virus has succeeded!")
        self.add_console_message("")

        dialog = tk.Toplevel(self.frame)
        dialog.title("VICTORY!")
        dialog.transient(self.frame)
        dialog.grab_set()

        UIUtilities.center_dialog(dialog, VICTORY_DIALOG_WIDTH, VICTORY_DIALOG_HEIGHT)

        # Header
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(
            header_frame,
            text="🎉 VICTORY! 🎉",
            font=("Arial", 18, "bold"),
            foreground="green"
        ).pack()

        # Victory message
        message_frame = ttk.Frame(dialog)
        message_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        victory_text = (
            "Congratulations!\n\n"
            f"You have created a runaway reaction and reached {VICTORY_ENTITY_THRESHOLD} entities!\n\n"
            f"Your virus achieved this in just {self.simulation.turn_count} turns!\n\n"
            "This represents a complete biological victory."
        )

        ttk.Label(
            message_frame,
            text=victory_text,
            font=("Arial", 11),
            justify=tk.CENTER,
            wraplength=450
        ).pack()

        # Statistics
        if self.game_state and (self.game_state.cumulative_entity_counts or self.game_state.peak_entity_counts):
            stats_frame = ttk.LabelFrame(message_frame, text="Final Production Statistics", padding=10)
            stats_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

            text_frame = ttk.Frame(stats_frame)
            text_frame.pack(fill=tk.BOTH, expand=True)

            stats_text = tk.Text(
                text_frame,
                height=6,
                width=50,
                state='disabled',
                font=("Consolas", 9),
                wrap=tk.WORD
            )
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=stats_text.yview)
            stats_text.config(yscrollcommand=scrollbar.set)

            stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            stats_text.config(state='normal')

            all_classes = set(self.game_state.cumulative_entity_counts.keys()) | \
                          set(self.game_state.peak_entity_counts.keys())

            if all_classes:
                stats_text.insert(tk.END, "Produced in total this round: (peak)\n")
                stats_text.insert(tk.END, "-" * 35 + "\n")

                sorted_classes = sorted(
                    all_classes,
                    key=lambda x: (-self.game_state.cumulative_entity_counts.get(x, 0), x)
                )

                for entity_class in sorted_classes:
                    total = self.game_state.cumulative_entity_counts.get(entity_class, 0)
                    peak = self.game_state.peak_entity_counts.get(entity_class, 0)

                    if total > 0 or peak > 0:
                        stats_text.insert(tk.END, f"{entity_class:12} {total:4d} ({peak:2d})\n")

            stats_text.config(state='disabled')

        # Game over notice
        ending_frame = ttk.Frame(message_frame)
        ending_frame.pack(fill=tk.X, pady=(15, 0))

        ending_text = "This simulation session is now complete."
        ttk.Label(
            ending_frame,
            text=ending_text,
            font=("Arial", 10, "bold"),
            justify=tk.CENTER,
            wraplength=450,
            foreground="blue"
        ).pack()

        # Close button
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Button(button_frame, text="Close Simulation", command=lambda: self._close_victory_dialog(dialog)).pack()

        dialog.focus_set()
        dialog.bind('<Escape>', lambda e: self._close_victory_dialog(dialog))

    def _close_victory_dialog(self, dialog):
        """Close victory dialog and end the session."""
        dialog.destroy()
        self.add_console_message("")
        self.add_console_message("Simulation session completed with VICTORY!")
        self.add_console_message("All controls have been disabled.")
        self.add_console_message("")
        self.add_console_message("To play again, return to the main menu and start a new game.")

    def show_extinction_dialog(self):
        """Show confirmation dialog when virus goes extinct."""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Simulation Complete")
        dialog.transient(self.frame)
        dialog.grab_set()

        UIUtilities.center_dialog(dialog, 500, 400)

        # Header
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(
            header_frame,
            text="Virus Extinction",
            font=("Arial", 16, "bold"),
            foreground="red"
        ).pack()

        # Message
        message_frame = ttk.Frame(dialog)
        message_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        message_text = (
            f"Your virus has gone extinct!\n\n"
            f"The simulation ran for {self.simulation.turn_count} turns before "
            "all viral entities were eliminated.\n"
        )

        ttk.Label(
            message_frame,
            text=message_text,
            font=("Arial", 11),
            justify=tk.CENTER,
            wraplength=450
        ).pack()

        # Statistics (same as victory)
        if self.game_state and (self.game_state.cumulative_entity_counts or self.game_state.peak_entity_counts):
            stats_frame = ttk.LabelFrame(message_frame, text="Entity Production Statistics", padding=10)
            stats_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

            text_frame = ttk.Frame(stats_frame)
            text_frame.pack(fill=tk.BOTH, expand=True)

            stats_text = tk.Text(
                text_frame,
                height=8,
                width=50,
                state='disabled',
                font=("Consolas", 9),
                wrap=tk.WORD
            )
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=stats_text.yview)
            stats_text.config(yscrollcommand=scrollbar.set)

            stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            stats_text.config(state='normal')

            all_classes = set(self.game_state.cumulative_entity_counts.keys()) | \
                          set(self.game_state.peak_entity_counts.keys())

            if all_classes:
                stats_text.insert(tk.END, "Produced in total this round: (peak)\n")
                stats_text.insert(tk.END, "-" * 35 + "\n")

                sorted_classes = sorted(
                    all_classes,
                    key=lambda x: (-self.game_state.cumulative_entity_counts.get(x, 0), x)
                )

                for entity_class in sorted_classes:
                    total = self.game_state.cumulative_entity_counts.get(entity_class, 0)
                    peak = self.game_state.peak_entity_counts.get(entity_class, 0)

                    if total > 0 or peak > 0:
                        stats_text.insert(tk.END, f"{entity_class:12} {total:4d} ({peak:2d})\n")
            else:
                stats_text.insert(tk.END, "No entities were produced during this simulation.")

            stats_text.config(state='disabled')

        # Closing message
        closing_frame = ttk.Frame(message_frame)
        closing_frame.pack(fill=tk.X, pady=(15, 0))

        closing_text = "Review the simulation log, then return to the Builder to try again."
        ttk.Label(
            closing_frame,
            text=closing_text,
            font=FONT_SMALL,
            justify=tk.CENTER,
            wraplength=450
        ).pack()

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Button(button_frame, text="Review Results", command=dialog.destroy).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Return to Builder", command=lambda: self.confirm_return_to_builder(dialog)).pack(side=tk.RIGHT)

        dialog.focus_set()
        dialog.bind('<Escape>', lambda e: dialog.destroy())

    def confirm_return_to_builder(self, dialog):
        """Confirm return to builder and close dialog."""
        dialog.destroy()
        self.exit_to_builder()

    def add_console_message(self, message: str):
        """Add message to console log."""
        self.console_text.config(state='normal')
        self.console_text.insert(tk.END, message + "\n")
        self.console_text.see(tk.END)
        self.console_text.config(state='disabled')

    def _extract_entities_created(self, turn_log: List[str]) -> Dict[str, int]:
        """Extract entities created this turn from the simulation log."""
        entities_created: Dict[str, int] = {}

        for raw in turn_log:
            line = raw.strip()

            if line.startswith("Produced:"):
                content = line[len("Produced:"):].strip()
                if content:
                    parts = content.split(" ", 1)
                    if len(parts) == 2:
                        count_str, entity_name = parts
                        try:
                            count = int(count_str)
                            entities_created[entity_name] = entities_created.get(entity_name, 0) + count
                        except ValueError:
                            pass
                continue

            l = raw.lstrip()
            if l.startswith("+"):
                content = l[1:].strip()
                parts = content.split(" ", 1)
                if len(parts) == 2:
                    count_str, entity_name = parts
                    try:
                        count = int(count_str)
                        entities_created[entity_name] = entities_created.get(entity_name, 0) + count
                    except ValueError:
                        pass

        return entities_created

    def _check_and_show_milestone_achievements_blocking(self):
        """Check for milestone achievements and show notification dialog."""
        if not self.game_state:
            return

        progress_data = self.game_state.get_milestone_progress()
        newly_achieved = progress_data.get("newly_achieved_this_run", [])
        open_milestones = progress_data.get("open", [])

        if not newly_achieved and not open_milestones:
            return

        self._show_milestone_dialog_blocking(newly_achieved, open_milestones, progress_data)

        if newly_achieved:
            self.game_state.award_milestone_achievements()

    def _show_milestone_dialog_blocking(
        self,
        newly_achieved: List[Dict],
        open_milestones: List[Dict],
        progress_data: Dict
    ):
        """Show a dialog listing milestone achievements and open milestones."""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Milestone Progress")
        dialog.transient(self.frame)
        dialog.grab_set()

        UIUtilities.center_dialog(dialog, 600, 500)

        # Header
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)

        if newly_achieved:
            ttk.Label(header_frame, text="Milestones Achieved!", font=("Arial", 16, "bold")).pack()
            total_ep = sum(m["reward_ep"] for m in newly_achieved)
            ttk.Label(
                header_frame,
                text=f"You earned {total_ep} Evolution Points!",
                font=("Arial", 12),
                foreground="green"
            ).pack(pady=(5, 0))
        else:
            ttk.Label(header_frame, text="Milestone Progress", font=("Arial", 16, "bold")).pack()
            ttk.Label(
                header_frame,
                text="Keep working towards your goals!",
                font=("Arial", 12),
                foreground="blue"
            ).pack(pady=(5, 0))

        # Create notebook for tabs
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        # Achievements tab
        if newly_achieved:
            achievements_frame = ttk.Frame(notebook)
            notebook.add(achievements_frame, text=f"Achieved ({len(newly_achieved)})")

            achievements_text = scrolledtext.ScrolledText(
                achievements_frame,
                height=15,
                wrap=tk.WORD,
                state='disabled'
            )
            achievements_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            achievements_text.config(state='normal')
            for milestone in newly_achieved:
                name = milestone["name"]
                desc = milestone["description"]
                reward = milestone["reward_ep"]

                achievements_text.insert(tk.END, f"[ACHIEVED] {name}\n")
                achievements_text.insert(tk.END, f"   {desc}\n")
                achievements_text.insert(tk.END, f"   Reward: +{reward} EP\n\n")
            achievements_text.config(state='disabled')

        # Open milestones tab
        if open_milestones:
            open_frame = ttk.Frame(notebook)
            notebook.add(open_frame, text=f"In Progress ({len(open_milestones)})")

            open_text = scrolledtext.ScrolledText(open_frame, height=15, wrap=tk.WORD, state='disabled')
            open_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            open_text.config(state='normal')
            for milestone in open_milestones:
                name = milestone["name"]
                desc = milestone["description"]
                reward = milestone["reward_ep"]
                progress_desc = milestone.get("progress_description", "No progress")

                open_text.insert(tk.END, f"[IN PROGRESS] {name}\n")
                open_text.insert(tk.END, f"   {desc}\n")
                open_text.insert(tk.END, f"   Progress: {progress_desc}\n")
                open_text.insert(tk.END, f"   Reward: {reward} EP\n\n")
            open_text.config(state='disabled')

        # Progress summary
        if self.game_state:
            achieved_count = len(progress_data.get("achieved", []))
            total_count = achieved_count + len(open_milestones)
            total_ep = progress_data.get("total_ep_earned", 0)

            summary_text = f"Overall Progress: {achieved_count}/{total_count} milestones completed ({total_ep} EP earned)"
            ttk.Label(dialog, text=summary_text, font=("Arial", 10, "italic")).pack(pady=(0, 10))

        # Close button
        ttk.Button(dialog, text="Continue", command=dialog.destroy).pack(pady=(0, 20))

        dialog.focus_set()
        dialog.bind('<Escape>', lambda e: dialog.destroy())

        # Wait for dialog to close
        self.frame.wait_window(dialog)