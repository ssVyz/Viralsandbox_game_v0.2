"""
Virus Simulation Logic

Handles virus building and simulation execution.
"""

import random
from typing import Dict, List, Optional, Any

from constants import (
    DEFAULT_STARTING_ENTITY_COUNT,
    INTERFERON_MIN,
    INTERFERON_MAX,
    INTERFERON_DECAY_PER_TURN,
    INTERFERON_PRECISION,
    INTERFERON_RNA_DEGRADATION_BONUS,
    INTERFERON_PROTEIN_DEGRADATION_BONUS,
    INTERFERON_DNA_DEGRADATION_BONUS,
    ENTITY_CLASS_RNA,
    ENTITY_CLASS_PROTEIN,
    ENTITY_CLASS_DNA,
    LOCATION_DISPLAY_ORDER,
    LOCATION_DISPLAY_LABELS,
)


class VirusBuilder:
    """Builds virus configurations from selected genes."""

    def __init__(self, gene_database, game_state=None):
        self.gene_db = gene_database
        self.game_state = game_state
        self.selected_genes: List[Dict] = []

    def set_game_state(self, game_state):
        """Set game state reference."""
        self.game_state = game_state

    def get_starter_entity(self) -> str:
        """Get the current starter entity."""
        if self.game_state:
            return self.game_state.get_selected_starter_entity()
        return "unenveloped virion (extracellular)"

    def can_add_gene(self, gene_name: str) -> tuple[bool, str]:
        """
        Non-mutating validation for whether a gene can be added.
        Returns (ok: bool, reason: str).
        """
        gene = self.gene_db.get_gene(gene_name)
        if not gene:
            return False, "unknown_gene"

        if any(g["name"] == gene_name for g in self.selected_genes):
            return False, "already_installed"

        requires = gene.get("requires", [])
        selected_names = [g["name"] for g in self.selected_genes]
        if not all(req in selected_names for req in requires):
            return False, "missing_prerequisites"

        if gene.get("is_polymerase", False) and self._has_polymerase_gene():
            return False, "polymerase_limit"

        return True, ""

    def add_gene(self, gene_name: str) -> bool:
        """Add a gene to the virus."""
        gene = self.gene_db.get_gene(gene_name)
        if not gene:
            return False

        if any(g["name"] == gene_name for g in self.selected_genes):
            return False

        requires = gene.get("requires", [])
        selected_names = [g["name"] for g in self.selected_genes]
        if not all(req in selected_names for req in requires):
            return False

        if gene.get("is_polymerase", False):
            if self._has_polymerase_gene():
                return False

        self.selected_genes.append(gene)
        return True

    def remove_gene(self, gene_name: str):
        """Remove a gene from the virus (and dependent genes)."""
        to_remove = []

        for gene in self.selected_genes:
            if gene_name in gene.get("requires", []):
                to_remove.append(gene["name"])

        for dep_gene in to_remove:
            self.remove_gene(dep_gene)

        for i, gene in enumerate(self.selected_genes):
            if gene["name"] == gene_name:
                del self.selected_genes[i]
                break

    def _has_polymerase_gene(self) -> bool:
        """Check if there's already a polymerase gene selected."""
        return any(gene.get("is_polymerase", False) for gene in self.selected_genes)

    def get_selected_polymerase_gene(self) -> Optional[str]:
        """Get the name of the currently selected polymerase gene."""
        for gene in self.selected_genes:
            if gene.get("is_polymerase", False):
                return gene["name"]
        return None

    def count_polymerase_genes(self) -> int:
        """Count the number of polymerase genes currently selected."""
        return sum(1 for gene in self.selected_genes if gene.get("is_polymerase", False))

    def get_virus_capabilities(self) -> Dict:
        """Get the full virus configuration."""
        available_entities = set()
        transition_rules = []

        starter_entity_name = self.get_starter_entity()
        available_entities.add(starter_entity_name)

        # FIRST PASS: Process all add_transition effects
        for gene in self.selected_genes:
            for effect in gene["effects"]:
                if effect["type"] in ["add_transition", "add_production"]:
                    rule = effect["rule"].copy()

                    for input_spec in rule["inputs"]:
                        available_entities.add(input_spec["entity"])
                    for output_spec in rule["outputs"]:
                        available_entities.add(output_spec["entity"])

                    if "interferon_amount" in rule:
                        rule["interferon_amount"] = round(float(rule.get("interferon_amount", 0.0)), 2)

                    transition_rules.append(rule)

        # SECOND PASS: Process all modify_transition effects
        for gene in self.selected_genes:
            for effect in gene["effects"]:
                if effect["type"] == "modify_transition":
                    rule_name = effect["rule_name"]
                    modification = effect.get("modification", {})

                    for rule in transition_rules:
                        if rule["name"] == rule_name:
                            if "probability_multiplier" in modification:
                                rule["probability"] *= modification["probability_multiplier"]
                                rule["probability"] = min(1.0, rule["probability"])

                            if "interferon_multiplier" in modification:
                                current_interferon = rule.get("interferon_amount", 0.0)
                                if current_interferon > 0:
                                    new_interferon = current_interferon * modification["interferon_multiplier"]
                                    rule["interferon_amount"] = round(new_interferon, 2)
                            break

        # Get degradation rates for all entities
        entity_degradation_rates = {}
        if self.gene_db and self.gene_db.db_manager:
            for entity_name in available_entities:
                entity_data = self.gene_db.db_manager.get_entity(entity_name)
                if entity_data:
                    entity_degradation_rates[entity_name] = entity_data.get("base_degradation_rate", 0.05)
                else:
                    entity_degradation_rates[entity_name] = 0.05
        else:
            for entity_name in available_entities:
                entity_degradation_rates[entity_name] = 0.05

        starting_count = DEFAULT_STARTING_ENTITY_COUNT
        if self.game_state:
            starting_count = self.game_state.get_starting_entity_count()

        return {
            "starting_entities": {starter_entity_name: starting_count},
            "possible_entities": list(available_entities),
            "transition_rules": transition_rules,
            "genes": [gene["name"] for gene in self.selected_genes],
            "entity_degradation_rates": entity_degradation_rates
        }


class ViralSimulation:
    """Handles the actual virus simulation."""

    def __init__(self, virus_blueprint: Dict):
        self.entities = virus_blueprint["starting_entities"].copy()
        self.transition_rules = virus_blueprint["transition_rules"]
        self.degradation_rates = virus_blueprint.get("entity_degradation_rates", {})
        self.db_manager = None
        self.turn_count = 0
        self.console_log: List[str] = []

        self.interferon_level = INTERFERON_MIN

    def process_turn(self) -> List[str]:
        """Process one simulation turn."""
        self.turn_count += 1
        starting_entities = self.entities.copy()
        changes = []

        # Apply degradation first
        degradation_changes = self.apply_degradation(starting_entities)
        changes.extend(degradation_changes)

        working_entities = starting_entities.copy()
        for change in degradation_changes:
            if change["type"] == "degraded":
                entity_name = change["entity"]
                count = change["count"]
                working_entities[entity_name] -= count
                if working_entities[entity_name] <= 0:
                    del working_entities[entity_name]

        # Process transition rules
        interferon_added_this_turn = 0.0
        for rule in self.transition_rules:
            rule_changes = self.apply_rule_to_state(rule, working_entities)
            changes.extend(rule_changes)

            interferon_added = self._process_rule_interferon_effects(rule, rule_changes)
            if interferon_added > 0:
                interferon_added_this_turn += interferon_added

            for change in rule_changes:
                if change["type"] == "consumed":
                    entity_name = change["entity"]
                    count = change["count"]
                    working_entities[entity_name] -= count
                    if working_entities[entity_name] <= 0:
                        del working_entities[entity_name]

        # Apply interferon decay
        self.interferon_level = max(INTERFERON_MIN, self.interferon_level - INTERFERON_DECAY_PER_TURN)

        # Add interferon generated this turn
        if interferon_added_this_turn > 0:
            self.interferon_level = min(INTERFERON_MAX, self.interferon_level + interferon_added_this_turn)

        self.apply_all_changes(changes)

        turn_log = self.generate_turn_log(starting_entities, changes, interferon_added_this_turn)
        self.console_log.extend(turn_log)

        return turn_log

    def _estimate_applications_from_changes(self, rule: Dict, rule_changes: List[Dict]) -> int:
        """Estimate how many times a rule actually applied."""
        consumed_counts = {}
        for ch in rule_changes:
            if ch["type"] == "consumed":
                consumed_counts[ch["entity"]] = consumed_counts.get(ch["entity"], 0) + ch["count"]

        apps_from_consumed = None
        if rule.get("inputs"):
            consumed_inputs = [i for i in rule["inputs"] if i.get("consumed", True)]
            if consumed_inputs and consumed_counts:
                vals = []
                for i in consumed_inputs:
                    per_app = max(1, int(i.get("count", 1)))
                    have = int(consumed_counts.get(i["entity"], 0))
                    vals.append(have // per_app)
                if vals:
                    apps_from_consumed = min(vals)

        if apps_from_consumed:
            return int(apps_from_consumed)

        # Fall back to produced outputs
        produced_counts = {}
        for ch in rule_changes:
            if ch["type"] == "produced":
                produced_counts[ch["entity"]] = produced_counts.get(ch["entity"], 0) + ch["count"]

        if rule.get("outputs") and produced_counts:
            vals = []
            for o in rule["outputs"]:
                per_app = max(1, int(o.get("count", 1)))
                made = int(produced_counts.get(o["entity"], 0))
                vals.append(made // per_app)
            if vals:
                return int(min(vals))

        return 0

    def _process_rule_interferon_effects(self, rule: Dict, rule_changes: List[Dict]) -> float:
        """Process interferon effects for a rule."""
        interferon_amount = float(rule.get("interferon_amount", 0.0) or 0.0)
        if interferon_amount <= 0:
            return 0.0

        successful_applications = self._estimate_applications_from_changes(rule, rule_changes)
        total_interferon = successful_applications * interferon_amount
        return round(total_interferon, INTERFERON_PRECISION)

    def apply_degradation(self, entity_state: Dict[str, int]) -> List[Dict]:
        """Apply degradation to entities."""
        degradation_changes = []

        for entity_name, count in entity_state.items():
            if count <= 0:
                continue

            base_degradation_rate = self.degradation_rates.get(entity_name, 0.05)
            interferon_bonus = self._calculate_interferon_degradation_bonus(entity_name)
            final_degradation_rate = min(1.0, base_degradation_rate * (1.0 + interferon_bonus))

            if final_degradation_rate <= 0:
                continue

            degraded_count = 0
            for _ in range(count):
                if random.random() < final_degradation_rate:
                    degraded_count += 1

            if degraded_count > 0:
                degradation_changes.append({
                    "type": "degraded",
                    "entity": entity_name,
                    "count": degraded_count,
                    "rule_name": "Natural degradation"
                })

        return degradation_changes

    def _calculate_interferon_degradation_bonus(self, entity_name: str) -> float:
        """Calculate additional degradation rate due to interferon."""
        if self.interferon_level <= 0 or not self.db_manager:
            return 0.0

        entity_data = self.db_manager.get_entity(entity_name)
        if not entity_data:
            return 0.0

        entity_class = entity_data.get("entity_class", "").lower()

        interferon_multipliers = {
            ENTITY_CLASS_RNA.lower(): INTERFERON_RNA_DEGRADATION_BONUS,
            ENTITY_CLASS_PROTEIN.lower(): INTERFERON_PROTEIN_DEGRADATION_BONUS,
            ENTITY_CLASS_DNA.lower(): INTERFERON_DNA_DEGRADATION_BONUS
        }

        multiplier = interferon_multipliers.get(entity_class, 0.0)
        bonus = self.interferon_level * multiplier

        return round(bonus, 4)

    def apply_rule_to_state(self, rule: Dict, entity_state: Dict[str, int]) -> List[Dict]:
        """Apply a single transition rule to a given entity state."""
        max_applications = self.get_max_applications_from_state(rule, entity_state)
        if max_applications == 0:
            return []

        if rule["rule_type"] == "per_entity":
            actual_applications = sum(1 for _ in range(max_applications)
                                      if random.random() < rule["probability"])
        elif rule["rule_type"] == "per_pair":
            actual_applications = sum(1 for _ in range(max_applications)
                                      if random.random() < rule["probability"])
        else:
            actual_applications = 0

        if actual_applications == 0:
            return []

        changes = []

        for input_spec in rule["inputs"]:
            if input_spec["consumed"]:
                consumed = actual_applications * input_spec["count"]
                entity_name = input_spec["entity"]

                changes.append({
                    "type": "consumed",
                    "entity": entity_name,
                    "count": consumed,
                    "rule_name": rule["name"]
                })

        for output_spec in rule["outputs"]:
            produced = actual_applications * output_spec["count"]
            entity_name = output_spec["entity"]

            changes.append({
                "type": "produced",
                "entity": entity_name,
                "count": produced,
                "rule_name": rule["name"]
            })

        return changes

    def get_max_applications_from_state(self, rule: Dict, entity_state: Dict[str, int]) -> int:
        """Calculate maximum times rule can be applied from a given state."""
        max_apps = float('inf')

        for input_spec in rule["inputs"]:
            entity_name = input_spec["entity"]
            required_count = input_spec["count"]
            available = entity_state.get(entity_name, 0)

            if available < required_count:
                return 0

            if input_spec["consumed"]:
                max_apps = min(max_apps, available // required_count)
            else:
                max_apps = min(max_apps, available // required_count)

        return max_apps if max_apps != float('inf') else 0

    def apply_all_changes(self, changes: List[Dict]):
        """Apply all accumulated changes to the entity state."""
        consumed = {}
        produced = {}
        degraded = {}

        for change in changes:
            entity_name = change["entity"]
            count = change["count"]

            if change["type"] == "consumed":
                consumed[entity_name] = consumed.get(entity_name, 0) + count
            elif change["type"] == "produced":
                produced[entity_name] = produced.get(entity_name, 0) + count
            elif change["type"] == "degraded":
                degraded[entity_name] = degraded.get(entity_name, 0) + count

        for entity_name, count in degraded.items():
            if entity_name in self.entities:
                self.entities[entity_name] -= count
                if self.entities[entity_name] <= 0:
                    del self.entities[entity_name]

        for entity_name, count in consumed.items():
            if entity_name in self.entities:
                self.entities[entity_name] -= count
                if self.entities[entity_name] <= 0:
                    del self.entities[entity_name]

        for entity_name, count in produced.items():
            if entity_name in self.entities:
                self.entities[entity_name] += count
            else:
                self.entities[entity_name] = count

    def generate_turn_log(
        self, starting_entities: Dict, changes: List[Dict], interferon_added_this_turn: float = 0.0
    ) -> List[str]:
        """Generate console log for this turn."""
        log_entries = []

        if self.turn_count == 1:
            log_entries.append("=" * 70)
            log_entries.append("  SIMULATION START")
            log_entries.append("=" * 70)
        else:
            log_entries.append("")
            log_entries.append("-" * 70)

        log_entries.append(f"  TURN {self.turn_count}")
        log_entries.append("-" * 70)

        # EVENTS SECTION
        if changes:
            log_entries.append("")
            log_entries.append("  Events this turn:")

            rule_changes = {}
            for change in changes:
                rule_name = change["rule_name"]
                if rule_name not in rule_changes:
                    rule_changes[rule_name] = {"consumed": [], "produced": [], "degraded": []}

                if change["type"] == "consumed":
                    rule_changes[rule_name]["consumed"].append(change)
                elif change["type"] == "produced":
                    rule_changes[rule_name]["produced"].append(change)
                elif change["type"] == "degraded":
                    rule_changes[rule_name]["degraded"].append(change)

            event_count = 0

            # Degradation events first
            for rule_name, rule_change in rule_changes.items():
                if rule_name == "Natural degradation" and rule_change["degraded"]:
                    event_count += 1
                    log_entries.append("")
                    log_entries.append(f"    [{event_count}] Natural Degradation")

                    if self.interferon_level > 0:
                        log_entries.append(f"        (Enhanced by interferon: {self.interferon_level:.1f}/100)")

                    degraded_items = []
                    for deg_change in rule_change["degraded"]:
                        entity_name = deg_change["entity"]
                        count = deg_change["count"]
                        degraded_items.append(f"{count} {self._format_entity_name(entity_name)}")

                    if len(degraded_items) == 1:
                        log_entries.append(f"        - {degraded_items[0]} degraded")
                    else:
                        log_entries.append("        Degraded:")
                        for item in degraded_items:
                            log_entries.append(f"          - {item}")

            # Biological processes
            for rule_name, rule_change in rule_changes.items():
                if rule_name == "Natural degradation":
                    continue

                consumed = rule_change["consumed"]
                produced = rule_change["produced"]

                if consumed or produced:
                    event_count += 1
                    log_entries.append("")
                    log_entries.append(f"    [{event_count}] {rule_name}")

                    if consumed:
                        consumed_items = []
                        for cons_change in consumed:
                            entity_name = cons_change["entity"]
                            count = cons_change["count"]
                            consumed_items.append(f"{count} {self._format_entity_name(entity_name)}")

                        if len(consumed_items) == 1:
                            log_entries.append(f"        Consumed: {consumed_items[0]}")
                        else:
                            log_entries.append("        Consumed:")
                            for item in consumed_items:
                                log_entries.append(f"          - {item}")

                    if produced:
                        produced_items = []
                        for prod_change in produced:
                            entity_name = prod_change["entity"]
                            count = prod_change["count"]
                            produced_items.append(f"{count} {self._format_entity_name(entity_name)}")

                        if len(produced_items) == 1:
                            log_entries.append(f"        Produced: {produced_items[0]}")
                        else:
                            log_entries.append("        Produced:")
                            for item in produced_items:
                                log_entries.append(f"          + {item}")

                    # Show interferon generation
                    rule_def = next((r for r in self.transition_rules if r.get("name") == rule_name), None)
                    if rule_def:
                        rule_interferon = float(rule_def.get("interferon_amount", 0.0) or 0.0)
                        if rule_interferon > 0:
                            mini_changes = []
                            if consumed:
                                mini_changes.extend(consumed)
                            if produced:
                                mini_changes.extend(produced)
                            applications = self._estimate_applications_from_changes(rule_def, mini_changes)
                            interferon_from_rule = applications * rule_interferon
                            if interferon_from_rule > 0:
                                log_entries.append(f"        Interferon generated: +{interferon_from_rule:.1f}")

            if event_count == 0:
                log_entries.append("")
                log_entries.append("    No events occurred this turn")

        else:
            log_entries.append("")
            log_entries.append("  Events this turn:")
            log_entries.append("    No events occurred this turn")

        # FINAL POPULATION
        log_entries.append("")
        log_entries.append("  Population at end:")
        if self.entities:
            total_entities = sum(self.entities.values())

            location_sections = self._generate_location_grouped_population()
            for section in location_sections:
                log_entries.extend(section)

            log_entries.append("")
            log_entries.append(f"    Total entities: {total_entities}")
        else:
            log_entries.append("    *** No entities remaining - EXTINCTION ***")

        log_entries.append("")
        log_entries.append(f"  Interferon activity is at {self.interferon_level:.1f}/100")

        return log_entries

    def _generate_location_grouped_population(self) -> List[List[str]]:
        """Generate location-grouped population display."""
        if not self.entities:
            return []

        entities_by_location = self._group_entities_by_location()

        sections = []

        for location in LOCATION_DISPLAY_ORDER:
            if location in entities_by_location:
                section = self._format_location_section_for_log(
                    location,
                    entities_by_location[location],
                    LOCATION_DISPLAY_LABELS.get(location, location.upper())
                )
                sections.append(section)
                del entities_by_location[location]

        for location, location_entities in entities_by_location.items():
            section = self._format_location_section_for_log(
                location,
                location_entities,
                location.upper()
            )
            sections.append(section)

        return sections

    def _group_entities_by_location(self) -> Dict[str, List[tuple[str, int]]]:
        """Group entities by their location property."""
        entities_by_location = {}

        for entity_name, count in self.entities.items():
            location = "unknown"
            if self.db_manager:
                entity_data = self.db_manager.get_entity(entity_name)
                if entity_data:
                    location = entity_data.get("location", "unknown")

            if location not in entities_by_location:
                entities_by_location[location] = []
            entities_by_location[location].append((entity_name, count))

        return entities_by_location

    def _format_location_section_for_log(
        self, location: str, location_entities: List[tuple[str, int]], label: str
    ) -> List[str]:
        """Format a location section for the console log."""
        location_entities.sort(key=lambda x: x[0].lower())

        section = []
        section.append(f"    [{label}]")

        for entity_name, count in location_entities:
            formatted_name = self._format_entity_name(entity_name)
            section.append(f"      {count:3d}x {formatted_name}")

        return section

    def _format_entity_name(self, entity_name: str) -> str:
        """Format entity names for better readability."""
        if len(entity_name) > 45:
            if "(extracellular)" in entity_name:
                return entity_name.replace("(extracellular)", "(ext)")
            elif "(cytoplasm)" in entity_name:
                return entity_name.replace("(cytoplasm)", "(cyto)")
            elif "(endosome)" in entity_name:
                return entity_name.replace("(endosome)", "(endo)")
            elif "(nucleus)" in entity_name:
                return entity_name.replace("(nucleus)", "(nuc)")

        return entity_name

    def is_simulation_over(self) -> bool:
        """Check if simulation should end."""
        return len(self.entities) == 0

    def get_interferon_level(self) -> float:
        """Get current interferon level."""
        return self.interferon_level