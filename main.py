"""
Main Application Entry Point

Coordinates all game modules and manages application flow.
"""

import tkinter as tk
from tkinter import messagebox
import random
from typing import Dict, Optional
from tkinter import ttk

from constants import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_MIN_HEIGHT,
    DEFAULT_STARTING_EP,
    INITIAL_DECK_SIZE,
    GENE_OFFER_DIALOG_WIDTH,
    GENE_OFFER_DIALOG_HEIGHT,
)
from data_models import GeneDatabaseManager
from game_state import GameState
from ui_base import CustomStyles, UIUtilities


class VirusSandboxController:
    """Main application controller."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Virus Sandbox")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # Setup custom styles
        CustomStyles.setup_styles()

        # Initialize modules (will be populated in setup_modules)
        self.modules: Dict[str, any] = {}
        self.current_module: Optional[str] = None
        self.current_database_manager: Optional[GeneDatabaseManager] = None

        # Persistent game state
        self.game_state: Optional[GameState] = None

        self.setup_modules()
        self.switch_to_module("menu")

    def setup_modules(self):
        """Initialize all game modules."""
        # Import UI modules here to avoid circular imports
        # These will be available after Phase 3 is delivered
        try:
            from ui_menu_builder import MenuModule, BuilderModule
            from ui_play import PlayModule
            from ui_editor import EditorModule

            self.modules["menu"] = MenuModule(self.root, self)
            self.modules["builder"] = BuilderModule(self.root, self)
            self.modules["play"] = PlayModule(self.root, self)
            self.modules["editor"] = EditorModule(self.root, self)
        except ImportError:
            # Fallback for when Phase 3 modules aren't ready yet
            print("Warning: UI modules not yet available. Phase 3 needed.")

    def switch_to_module(self, module_name: str):
        """Switch to a different module and handle post-Play gene offer timing."""
        prev = self.current_module
        if self.current_module:
            self.modules[self.current_module].hide()

        if module_name not in self.modules:
            raise ValueError(f"Unknown module: {module_name}")

        self.current_module = module_name
        self.modules[module_name].show()

        # When returning FROM Play TO Builder, show pending gene offer
        if prev == "play" and module_name == "builder" and self.game_state:
            self.game_state.reset_round_install_counter()
            if self.game_state.offer_pending:
                try:
                    self._show_gene_offer_dialog()
                finally:
                    self.game_state.offer_pending = False

    def start_new_game_with_database(self, database_manager: GeneDatabaseManager):
        """Start new game with a loaded database."""
        self.current_database_manager = database_manager

        # Initialize game state
        self.game_state = GameState()
        self.game_state.set_database_manager(database_manager)
        self.game_state.ep = DEFAULT_STARTING_EP

        # Reset milestone data for new game
        self.game_state.reset_for_new_game()
        self.game_state.reset_starting_entity_count()

        # Seed deck with random genes
        all_genes = database_manager.get_all_genes()
        initial_deck_size = min(INITIAL_DECK_SIZE, len(all_genes))
        self.game_state.deck = random.sample(all_genes, initial_deck_size)

        # Wire modules
        self.modules["builder"].set_database_manager(database_manager)
        self.modules["builder"].set_game_state(self.game_state)

        self.modules["play"].set_database_manager(database_manager)
        self.modules["play"].set_game_state(self.game_state)

        # Wire editor with database manager
        self.modules["editor"].db_manager = database_manager
        self.modules["editor"].update_database_display()
        self.modules["editor"].update_entity_list()
        self.modules["editor"].update_gene_list()
        self.modules["editor"].update_milestone_list()

        self.switch_to_module("builder")

    def start_simulation(self, virus_blueprint: dict):
        """Start simulation with given virus blueprint."""
        if self.game_state and self.game_state.cycles_used >= self.game_state.cycle_limit:
            messagebox.showinfo("No Rounds Left", "You've used all available build→play rounds.")
            return

        # Count this Play run
        if self.game_state:
            self.game_state.cycles_used += 1
            self.game_state.offer_pending = False

        self.modules["play"].set_virus_blueprint(virus_blueprint)
        self.modules["play"].set_game_state(self.game_state)
        self.switch_to_module("play")

    def skip_round(self):
        """Skip the current round without playing - consumes a round but shows gene offer."""
        if not self.game_state:
            messagebox.showwarning("No Game State", "Game state not initialized.")
            return

        # Check round availability
        if self.game_state.cycles_used >= self.game_state.cycle_limit:
            messagebox.showwarning(
                "No Rounds Left",
                f"You have used all {self.game_state.cycle_limit} available rounds.\n"
                "This game session is complete."
            )
            return

        # Count this as a used round
        self.game_state.cycles_used += 1
        self.game_state.reset_round_install_counter()

        # Show gene offer dialog directly
        try:
            self._show_gene_offer_dialog()
        except Exception as e:
            messagebox.showerror("Gene Offer Error", f"Error showing gene offer: {e}")

        # Update builder UI
        builder = self.modules.get("builder")
        if builder:
            try:
                builder.update_virus_display()
            except Exception:
                pass

    def _show_gene_offer_dialog(self):
        """Offer one of up to 5 random genes to add to the deck."""
        if not (self.current_database_manager and self.game_state):
            return

        # Build exclusion set
        exclude = set(self.game_state.deck) | set(self.game_state.installed_genes)

        all_genes = list(self.current_database_manager.get_all_genes())
        pool = [g for g in all_genes if g not in exclude]
        if not pool:
            messagebox.showinfo("Gene Offer", "No new genes are available.")
            return

        k = min(self.game_state.offer_size, len(pool))
        offers = random.sample(pool, k)

        # Create modal dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Evolutionary Opportunity")
        dialog.transient(self.root)
        dialog.grab_set()

        UIUtilities.center_dialog(dialog, GENE_OFFER_DIALOG_WIDTH, GENE_OFFER_DIALOG_HEIGHT)

        # Header
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Label(header_frame, text="Evolutionary Opportunity", font=("Arial", 14, "bold")).pack()
        ttk.Label(
            header_frame,
            text="Select ONE new gene to add to your deck:",
            font=("Arial", 11)
        ).pack(pady=(10, 0))

        # Gene selection area
        selection_frame = ttk.Frame(dialog)
        selection_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        listbox = tk.Listbox(selection_frame, height=min(10, len(offers)), font=("Arial", 10))
        for name in offers:
            cost = 0
            gene = self.current_database_manager.get_gene(name)
            if gene:
                cost = gene.get("cost", 0)
            listbox.insert(tk.END, f"{name} ({cost} EP)")
        listbox.pack(fill=tk.BOTH, expand=True)

        # Starting count bonus info
        bonus_frame = ttk.Frame(dialog)
        bonus_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        current_count = self.game_state.get_starting_entity_count()
        if current_count > 10:
            bonus_text = f"Current starting entities: {current_count} (bonus: +{current_count - 10})"
            ttk.Label(
                bonus_frame,
                text=bonus_text,
                font=("Arial", 10, "italic"),
                foreground="blue"
            ).pack()

        selection_holder = {"choice": None}

        def choose_and_close():
            sel = listbox.curselection()
            if sel:
                display = listbox.get(sel[0])
                gene_name = display.split(" (")[0]
                selection_holder["choice"] = gene_name
            dialog.destroy()

        def skip_and_get_bonus():
            """Skip gene selection and get starting entity bonus."""
            self.game_state.increase_starting_entity_count(2)
            dialog.destroy()

        # Button area
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        ttk.Button(button_frame, text="Add Selected Gene", command=choose_and_close).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        skip_text = "Skip (+2 starting entities)"
        ttk.Button(button_frame, text=skip_text, command=skip_and_get_bonus).pack(side=tk.LEFT)

        # Focus and keyboard handling
        dialog.focus_set()
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        dialog.bind('<Return>', lambda e: choose_and_close())

        # Wait for dialog to close
        self.root.wait_window(dialog)

        picked = selection_holder["choice"]
        if picked:
            if self.game_state.add_to_deck(picked):
                messagebox.showinfo("Gene Added", f"Added to deck: {picked}")
            else:
                messagebox.showinfo("No Change", f"{picked} was already in your deck.")
        else:
            # Show bonus confirmation if they skipped
            new_count = self.game_state.get_starting_entity_count()
            if new_count > current_count:
                messagebox.showinfo(
                    "Starting Bonus",
                    f"You now start with {new_count} entities instead of 10!\n"
                    f"(Bonus: +{new_count - 10} entities)"
                )

        # Refresh Builder UI
        builder = self.modules.get("builder")
        if builder:
            try:
                builder.update_gene_list()
                builder.update_virus_display()
            except Exception:
                pass

    def handle_database_change(self):
        """Handle database changes that might affect milestones."""
        if self.game_state:
            self.game_state.refresh_milestone_definitions()

    def validate_current_milestones(self) -> tuple[bool, str]:
        """Validate that current milestone definitions are still valid."""
        if not (self.game_state and self.current_database_manager):
            return True, "No milestones to validate"

        try:
            milestones = self.current_database_manager.get_milestones()
            invalid_milestones = []

            for milestone_id, milestone_data in milestones.items():
                is_valid, error_msg = self.current_database_manager.validate_milestone_data(milestone_data)
                if not is_valid:
                    invalid_milestones.append(f"{milestone_id}: {error_msg}")

            if invalid_milestones:
                return False, "Invalid milestones found:\n" + "\n".join(invalid_milestones)

            return True, "All milestones are valid"

        except Exception as e:
            return False, f"Error validating milestones: {e}"

    def show_milestone_validation_errors(self) -> bool:
        """Show milestone validation errors to user."""
        is_valid, message = self.validate_current_milestones()
        if not is_valid:
            messagebox.showerror("Milestone Validation Error", message)
            return False
        return True

    def quit_application(self):
        """Exit the application."""
        # Check for unsaved changes in editor
        if (hasattr(self.modules.get("editor", {}), 'db_manager') and
                self.modules["editor"].db_manager.is_modified):
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes in the gene editor. Save before exiting?"
            )
            if result is True:
                try:
                    self.modules["editor"].save_database()
                except:
                    pass
            elif result is None:
                return

        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.root.quit()

    def run(self):
        """Start the application."""
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
        self.root.mainloop()


def main():
    """Application entry point."""
    app = VirusSandboxController()
    app.run()


if __name__ == "__main__":
    main()