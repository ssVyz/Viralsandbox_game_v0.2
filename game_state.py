"""
Game State Management

Central run-level state including EP, deck, cycles, and milestone tracking.
"""

from typing import Optional, List, Dict, Set
import random

from constants import (
    DEFAULT_STARTING_EP,
    DEFAULT_GENE_REMOVE_COST,
    DEFAULT_STARTING_ENTITY_COUNT,
    STARTING_ENTITY_COUNT_BONUS,
    DEFAULT_GENE_OFFER_SIZE,
    DEFAULT_CYCLE_LIMIT,
    MAX_GENE_INSTALLS_PER_ROUND,
    DEFAULT_BASE_ENTITY_NAME,
)


class GameState:
    """
    Central run-level state (EP, deck, cycles, milestones).

    - EP is a single decreasing counter
    - Inserting and removing genes both SPEND EP (no refunds)
    - Costs come from the DB per-gene "cost" field
    - Tracks build→play cycles and gene offers
    - Tracks milestone progress and achievements
    """

    def __init__(self, *, offer_size: int = DEFAULT_GENE_OFFER_SIZE, seed: Optional[int] = None):
        # Economy
        self.ep: int = DEFAULT_STARTING_EP

        # Deck-building
        self.deck: List[str] = []
        self.installed_genes: List[str] = []
        self.installs_this_round: int = 0

        # Starter entity selection and count
        self.selected_starter_entity: str = DEFAULT_BASE_ENTITY_NAME
        self.starting_entity_count: int = DEFAULT_STARTING_ENTITY_COUNT

        # Gene-offer settings
        self.offer_size: int = offer_size

        # Build→Play cycle control
        self.cycle_limit: int = DEFAULT_CYCLE_LIMIT
        self.cycles_used: int = 0
        self.offer_pending: bool = False

        # DB access
        self.db_manager = None

        # RNG
        self._rng = random.Random(seed)

        # Milestone achievements (persistent across play runs)
        self.achieved_milestones: Set[str] = set()

        # Milestone achievements for current play run only
        self.milestones_achieved_this_run: Set[str] = set()

        # Progress tracking for current play run
        self.current_turn: int = 0
        self.peak_entity_counts: Dict[str, int] = {}
        self.cumulative_entity_counts: Dict[str, int] = {}

        # Milestone definitions (loaded from database)
        self._milestone_definitions: Dict[str, Dict] = {}

    # =================== WIRING ===================

    def set_database_manager(self, db_manager):
        """Set database manager and initialize from it."""
        self.db_manager = db_manager
        self._auto_select_starter_entity()
        self._load_milestone_definitions()

    def _auto_select_starter_entity(self):
        """Automatically select the first available starter entity."""
        if not self.db_manager:
            return

        available_starters = self.db_manager.get_starter_entities()
        if available_starters:
            self.selected_starter_entity = available_starters[0]
        else:
            all_entities = self.db_manager.get_all_entity_names()
            if all_entities:
                self.selected_starter_entity = all_entities[0]

    def _load_milestone_definitions(self):
        """Load milestone definitions from database."""
        if not self.db_manager:
            self._milestone_definitions = {}
            return
        self._milestone_definitions = self.db_manager.get_milestones()

    # =================== STARTER ENTITY ===================

    def get_available_starter_entities(self) -> List[str]:
        """Get all entities that can be used as starters."""
        if not self.db_manager:
            return []
        return self.db_manager.get_starter_entities()

    def set_starter_entity(self, entity_name: str) -> bool:
        """Set the selected starter entity (with validation)."""
        if not self.db_manager:
            return False

        available_starters = self.get_available_starter_entities()
        if entity_name in available_starters:
            self.selected_starter_entity = entity_name
            return True
        return False

    def get_selected_starter_entity(self) -> str:
        """Get the currently selected starter entity."""
        return self.selected_starter_entity

    def validate_starter_entity(self) -> tuple[bool, str]:
        """Validate current starter entity selection."""
        if not self.db_manager:
            return False, "No database loaded"

        available_starters = self.get_available_starter_entities()
        if not available_starters:
            return False, "No starter entities defined in database"

        if self.selected_starter_entity not in available_starters:
            self._auto_select_starter_entity()
            if self.selected_starter_entity not in available_starters:
                return False, f"Selected starter '{self.selected_starter_entity}' is not available"

        return True, "Valid starter entity selected"

    # =================== COST HELPERS ===================

    def get_gene_cost(self, gene_name: str) -> int:
        """Get the EP cost to add a gene."""
        if not self.db_manager:
            return 0
        gene = self.db_manager.get_gene(gene_name)
        return int(gene.get("cost", 0)) if gene else 0

    def get_remove_cost(self, gene_name: str) -> int:
        """Get the EP cost to remove a gene."""
        return DEFAULT_GENE_REMOVE_COST

    # =================== EP MANAGEMENT ===================

    def can_afford_insert(self, gene_name: str) -> bool:
        """Check if player can afford to insert gene."""
        return self.ep >= self.get_gene_cost(gene_name)

    def spend_for_insert(self, gene_name: str) -> bool:
        """Spend EP to insert gene."""
        cost = self.get_gene_cost(gene_name)
        if self.ep >= cost:
            self.ep -= cost
            return True
        return False

    def can_afford_remove(self, gene_name: str) -> bool:
        """Check if player can afford to remove gene."""
        return self.ep >= self.get_remove_cost(gene_name)

    def spend_for_remove(self, gene_name: str) -> bool:
        """Spend EP to remove gene."""
        cost = self.get_remove_cost(gene_name)
        if self.ep >= cost:
            self.ep -= cost
            return True
        return False

    def award_ep(self, amount: int):
        """Award EP (used for milestone rewards)."""
        if amount > 0:
            self.ep += amount

    # =================== DECK MANAGEMENT ===================

    def add_to_deck(self, gene_name: str) -> bool:
        """Add gene to deck."""
        if gene_name not in self.deck:
            self.deck.append(gene_name)
            return True
        return False

    def in_deck(self, gene_name: str) -> bool:
        """Check if gene is in deck."""
        return gene_name in self.deck

    # =================== GENE OFFERS ===================

    def _all_gene_names(self) -> List[str]:
        """Get all available gene names from database."""
        if not self.db_manager:
            return []
        return list(self.db_manager.get_all_genes())

    def draw_gene_offers(
            self, n: Optional[int] = None, exclude: Optional[Set[str]] = None
    ) -> List[str]:
        """Draw random gene offers."""
        n = n or self.offer_size
        exclude = exclude or set()
        pool = set(self._all_gene_names()) - set(self.deck) - set(exclude)
        pool_list = sorted(pool)
        if not pool_list:
            return []
        k = min(n, len(pool_list))
        return self._rng.sample(pool_list, k)

    # =================== STARTING ENTITY COUNT ===================

    def increase_starting_entity_count(self, amount: int = STARTING_ENTITY_COUNT_BONUS):
        """Increase starting entity count (when skipping gene offers)."""
        self.starting_entity_count += amount

    def get_starting_entity_count(self) -> int:
        """Get current starting entity count."""
        return self.starting_entity_count

    def reset_starting_entity_count(self):
        """Reset starting entity count to default."""
        self.starting_entity_count = DEFAULT_STARTING_ENTITY_COUNT

    # =================== ROUND MANAGEMENT ===================

    def can_install_gene_this_round(self) -> bool:
        """Check if player can install another gene this round."""
        return self.installs_this_round < MAX_GENE_INSTALLS_PER_ROUND

    def record_gene_install(self):
        """Record that a gene was installed this round."""
        self.installs_this_round += 1

    def reset_round_install_counter(self):
        """Reset gene install counter for new round."""
        self.installs_this_round = 0

    # =================== MILESTONE SYSTEM ===================

    def reset_milestone_progress(self):
        """Reset milestone progress for a new play run."""
        self.milestones_achieved_this_run.clear()
        self.current_turn = 0
        self.peak_entity_counts.clear()
        self.cumulative_entity_counts.clear()

    def reset_for_new_game(self):
        """Reset all milestone data for a new game/playthrough."""
        self.achieved_milestones.clear()
        self.reset_milestone_progress()

    def update_turn_count(self, turn_number: int):
        """Update current turn number and check survival milestones."""
        self.current_turn = turn_number
        self._check_survival_milestones()

    def update_entity_counts(
            self,
            current_entities: Dict[str, int],
            entities_created_this_turn: Optional[Dict[str, int]] = None
    ):
        """Update entity count tracking and check milestones."""
        if not self.db_manager:
            return

        # Group current entities by class for peak tracking
        current_by_class = {}
        for entity_name, count in current_entities.items():
            entity_data = self.db_manager.get_entity(entity_name)
            if entity_data:
                entity_class = entity_data.get("entity_class", "unknown")
                current_by_class[entity_class] = current_by_class.get(entity_class, 0) + count

        # Update peak counts
        for entity_class, count in current_by_class.items():
            self.peak_entity_counts[entity_class] = max(
                self.peak_entity_counts.get(entity_class, 0),
                count
            )

        # Update cumulative counts if entities were created
        if entities_created_this_turn:
            for entity_name, count in entities_created_this_turn.items():
                entity_data = self.db_manager.get_entity(entity_name)
                if entity_data:
                    entity_class = entity_data.get("entity_class", "unknown")
                    self.cumulative_entity_counts[entity_class] = (
                            self.cumulative_entity_counts.get(entity_class, 0) + count
                    )

        self._check_entity_count_milestones()

    def _check_survival_milestones(self):
        """Check if any survival milestones have been achieved."""
        for milestone_id, milestone in self._milestone_definitions.items():
            if (milestone["type"] == "survive_turns"
                    and milestone_id not in self.achieved_milestones
                    and milestone_id not in self.milestones_achieved_this_run):
                if self.current_turn >= milestone["target"]:
                    self.milestones_achieved_this_run.add(milestone_id)
                    self.achieved_milestones.add(milestone_id)

    def _check_entity_count_milestones(self):
        """Check if any entity count milestones have been achieved."""
        for milestone_id, milestone in self._milestone_definitions.items():
            if (milestone_id in self.achieved_milestones
                    or milestone_id in self.milestones_achieved_this_run):
                continue

            milestone_type = milestone["type"]
            target = milestone["target"]
            entity_class = milestone.get("entity_class")

            if milestone_type == "peak_entity_count" and entity_class:
                current_peak = self.peak_entity_counts.get(entity_class, 0)
                if current_peak >= target:
                    self.milestones_achieved_this_run.add(milestone_id)
                    self.achieved_milestones.add(milestone_id)

            elif milestone_type == "cumulative_entity_count" and entity_class:
                current_cumulative = self.cumulative_entity_counts.get(entity_class, 0)
                if current_cumulative >= target:
                    self.milestones_achieved_this_run.add(milestone_id)
                    self.achieved_milestones.add(milestone_id)

    def get_milestone_progress(self) -> Dict:
        """Get comprehensive milestone progress data for UI display."""
        achieved = []
        open_milestones = []
        newly_achieved_this_run = []
        total_ep_earned = 0

        for milestone_id, milestone in self._milestone_definitions.items():
            milestone_data = milestone.copy()
            milestone_data["achieved"] = milestone_id in self.achieved_milestones
            milestone_data["achieved_this_run"] = milestone_id in self.milestones_achieved_this_run

            if milestone_data["achieved"]:
                achieved.append(milestone_data)
                total_ep_earned += milestone["reward_ep"]

                if milestone_data["achieved_this_run"]:
                    newly_achieved_this_run.append(milestone_data)
            else:
                progress_info = self._get_milestone_progress_info(milestone)
                milestone_data.update(progress_info)
                open_milestones.append(milestone_data)

        return {
            "achieved": achieved,
            "open": open_milestones,
            "total_ep_earned": total_ep_earned,
            "newly_achieved_this_run": newly_achieved_this_run
        }

    def _get_milestone_progress_info(self, milestone: Dict) -> Dict:
        """Get progress information for a specific milestone."""
        milestone_type = milestone["type"]
        target = milestone["target"]

        if milestone_type == "survive_turns":
            current = self.current_turn
            return {
                "current_progress": current,
                "target_progress": target,
                "progress_description": f"{current}/{target} turns"
            }

        elif milestone_type == "peak_entity_count":
            entity_class = milestone.get("entity_class", "unknown")
            current = self.peak_entity_counts.get(entity_class, 0)
            return {
                "current_progress": current,
                "target_progress": target,
                "progress_description": f"{current}/{target} {entity_class} entities (peak)"
            }

        elif milestone_type == "cumulative_entity_count":
            entity_class = milestone.get("entity_class", "unknown")
            current = self.cumulative_entity_counts.get(entity_class, 0)
            return {
                "current_progress": current,
                "target_progress": target,
                "progress_description": f"{current}/{target} {entity_class} entities (total)"
            }

        return {
            "current_progress": 0,
            "target_progress": target,
            "progress_description": "Unknown milestone type"
        }

    def award_milestone_achievements(self) -> List[Dict]:
        """Award EP for milestones achieved in this run and return list."""
        newly_achieved = []

        for milestone_id in self.milestones_achieved_this_run:
            milestone = self._milestone_definitions.get(milestone_id)
            if milestone:
                reward_ep = milestone["reward_ep"]
                self.award_ep(reward_ep)

                milestone_copy = milestone.copy()
                milestone_copy["achieved"] = True
                newly_achieved.append(milestone_copy)

        return newly_achieved

    def get_available_milestones(self) -> List[Dict]:
        """Get all milestone definitions from database."""
        return list(self._milestone_definitions.values())

    def refresh_milestone_definitions(self):
        """Refresh milestone definitions from database."""
        self._load_milestone_definitions()

    def has_milestones_achieved_this_run(self) -> bool:
        """Check if any milestones were achieved in the current run."""
        return len(self.milestones_achieved_this_run) > 0

    def get_milestones_achieved_this_run(self) -> List[Dict]:
        """Get list of milestones achieved in this specific run."""
        achieved_this_run = []
        for milestone_id in self.milestones_achieved_this_run:
            milestone = self._milestone_definitions.get(milestone_id)
            if milestone:
                milestone_copy = milestone.copy()
                milestone_copy["achieved"] = True
                milestone_copy["achieved_this_run"] = True
                achieved_this_run.append(milestone_copy)
        return achieved_this_run