"""
Data Models and Database Management

Handles gene database loading, saving, validation, and access.
"""

import json
from datetime import datetime
from typing import Optional, Dict, List, Any

from constants import (
    DEFAULT_DEGRADATION_RATE,
    DEFAULT_BASE_ENTITY_NAME,
    DATABASE_VERSION,
    DATABASE_DEFAULT_NAME,
    VALID_MILESTONE_TYPES,
    LOCATION_EXTRACELLULAR,
    LOCATION_CYTOPLASM,
    LOCATION_ENDOSOME,
    LOCATION_NUCLEUS,
    ENTITY_CLASS_VIRION,
    ENTITY_CLASS_PROTEIN,
    ENTITY_CLASS_RNA,
    ENTITY_CLASS_DNA,
)


class GeneDatabaseManager:
    """Manages loading, saving, and editing gene databases."""

    def __init__(self):
        self.database = {
            "database_info": {
                "name": DATABASE_DEFAULT_NAME,
                "version": DATABASE_VERSION,
                "description": "",
                "created_by": "User",
                "created_date": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            },
            "entities": {
                DEFAULT_BASE_ENTITY_NAME: {
                    "name": DEFAULT_BASE_ENTITY_NAME,
                    "description": "Basic viral particle outside the cell",
                    "base_degradation_rate": DEFAULT_DEGRADATION_RATE,
                    "location": LOCATION_EXTRACELLULAR,
                    "entity_class": ENTITY_CLASS_VIRION,
                    "is_starter": True
                }
            },
            "genes": {},
            "milestones": {}
        }
        self.file_path: Optional[str] = None
        self.is_modified = False

    def load_database(self, file_path: str) -> bool:
        """Load database from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            if not self._validate_database_structure(loaded_data):
                raise ValueError("Invalid database structure")

            self.database = loaded_data
            self.file_path = file_path
            self.is_modified = False
            self._ensure_base_entity()
            self._ensure_milestones_section()
            self._migrate_genes_add_polymerase_field(loaded_data)
            return True

        except Exception as e:
            raise Exception(f"Failed to load database: {e}")

    def save_database(self, file_path: Optional[str] = None) -> bool:
        """Save database to JSON file."""
        save_path = file_path or self.file_path
        if not save_path:
            raise ValueError("No file path specified")

        self.database["database_info"]["last_modified"] = datetime.now().isoformat()

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.database, f, indent=2, ensure_ascii=False)
            self.file_path = save_path
            self.is_modified = False
            return True
        except Exception as e:
            raise Exception(f"Failed to save database: {e}")

    def _validate_database_structure(self, data: Dict) -> bool:
        """Validate that the loaded data has the expected structure."""
        try:
            required_keys = ["database_info", "genes", "entities"]
            if not all(key in data for key in required_keys):
                return False

            info_keys = ["name", "version", "created_date", "last_modified"]
            if not all(key in data["database_info"] for key in info_keys):
                return False

            if not isinstance(data["genes"], dict):
                return False

            if isinstance(data["entities"], list):
                self._migrate_entities_to_new_format(data)
            elif not isinstance(data["entities"], dict):
                return False

            self._migrate_entities_add_starter_field(data)
            self._migrate_genes_add_polymerase_field(data)

            if "milestones" not in data:
                data["milestones"] = {}
            elif not isinstance(data["milestones"], dict):
                data["milestones"] = {}

            return True
        except:
            return False

    def _ensure_milestones_section(self):
        """Ensure milestones section exists in database."""
        if "milestones" not in self.database:
            self.database["milestones"] = {}
            self.is_modified = True

    def _migrate_entities_to_new_format(self, data: Dict):
        """Migrate old entities list format to new entities object format."""
        if isinstance(data["entities"], list):
            old_entities = data["entities"]
            new_entities = {}

            for entity_name in old_entities:
                new_entities[entity_name] = {
                    "name": entity_name,
                    "description": f"Auto-migrated entity: {entity_name}",
                    "base_degradation_rate": DEFAULT_DEGRADATION_RATE,
                    "location": self._guess_location_from_name(entity_name),
                    "entity_class": self._guess_class_from_name(entity_name),
                    "is_starter": entity_name == DEFAULT_BASE_ENTITY_NAME
                }

            data["entities"] = new_entities

    def _migrate_entities_add_starter_field(self, data: Dict):
        """Add is_starter field to entities that don't have it."""
        if "entities" in data and isinstance(data["entities"], dict):
            for entity_name, entity_data in data["entities"].items():
                if "is_starter" not in entity_data:
                    entity_data["is_starter"] = (entity_name == DEFAULT_BASE_ENTITY_NAME)

    def _migrate_genes_add_polymerase_field(self, data: Dict):
        """Add is_polymerase field to genes that don't have it."""
        if "genes" in data and isinstance(data["genes"], dict):
            modified = False
            for gene_name, gene_data in data["genes"].items():
                if "is_polymerase" not in gene_data:
                    gene_data["is_polymerase"] = False
                    modified = True
            if modified:
                self.is_modified = True

    def _guess_location_from_name(self, entity_name: str) -> str:
        """Guess location from entity name."""
        name_lower = entity_name.lower()
        if "(extracellular)" in name_lower:
            return LOCATION_EXTRACELLULAR
        elif "(cytoplasm)" in name_lower:
            return LOCATION_CYTOPLASM
        elif "(endosome)" in name_lower:
            return LOCATION_ENDOSOME
        elif "(nucleus)" in name_lower:
            return LOCATION_NUCLEUS
        else:
            return "unknown"

    def _guess_class_from_name(self, entity_name: str) -> str:
        """Guess entity class from name."""
        name_lower = entity_name.lower()
        if "rna" in name_lower:
            return ENTITY_CLASS_RNA
        elif any(term in name_lower for term in ["protein", "polymerase", "protease"]):
            return ENTITY_CLASS_PROTEIN
        elif "virion" in name_lower:
            return ENTITY_CLASS_VIRION
        else:
            return "unknown"

    def _ensure_base_entity(self):
        """Ensure the base entity exists."""
        if DEFAULT_BASE_ENTITY_NAME not in self.database["entities"]:
            self.database["entities"][DEFAULT_BASE_ENTITY_NAME] = {
                "name": DEFAULT_BASE_ENTITY_NAME,
                "description": "Basic viral particle outside the cell",
                "base_degradation_rate": DEFAULT_DEGRADATION_RATE,
                "location": LOCATION_EXTRACELLULAR,
                "entity_class": ENTITY_CLASS_VIRION,
                "is_starter": True
            }

    # =================== ENTITY MANAGEMENT ===================

    def add_entity(self, entity_data: Dict):
        """Add or update an entity."""
        entity_name = entity_data["name"]
        if "is_starter" not in entity_data:
            entity_data["is_starter"] = False

        self.database["entities"][entity_name] = entity_data.copy()
        self.is_modified = True

    def delete_entity(self, entity_name: str):
        """Delete an entity."""
        if entity_name in self.database["entities"]:
            del self.database["entities"][entity_name]
            self.is_modified = True

    def get_entity(self, entity_name: str) -> Optional[Dict]:
        """Get an entity by name."""
        return self.database["entities"].get(entity_name)

    def get_all_entity_names(self) -> List[str]:
        """Get all entity names."""
        return list(self.database["entities"].keys())

    def get_entities(self) -> Dict:
        """Get all entities as a dict."""
        return self.database["entities"].copy()

    def get_starter_entities(self) -> List[str]:
        """Get all entities marked as starter entities."""
        starter_entities = []
        for entity_name, entity_data in self.database["entities"].items():
            if entity_data.get("is_starter", False):
                starter_entities.append(entity_name)
        return starter_entities

    def get_starter_entity_names(self) -> List[str]:
        """Get names of all starter entities (alias for compatibility)."""
        return self.get_starter_entities()

    def set_entity_starter_status(self, entity_name: str, is_starter: bool) -> bool:
        """Set the starter status of an entity."""
        if entity_name in self.database["entities"]:
            self.database["entities"][entity_name]["is_starter"] = bool(is_starter)
            self.is_modified = True
            return True
        return False

    # =================== GENE MANAGEMENT ===================

    def add_gene(self, gene_data: Dict):
        """Add or update a gene."""
        gene_name = gene_data["name"]

        if "is_polymerase" not in gene_data:
            gene_data["is_polymerase"] = False

        self.database["genes"][gene_name] = gene_data.copy()
        self._update_entities_from_genes()
        self.is_modified = True

    def delete_gene(self, gene_name: str):
        """Delete a gene."""
        if gene_name in self.database["genes"]:
            del self.database["genes"][gene_name]
            self._update_entities_from_genes()
            self.is_modified = True

    def get_gene(self, gene_name: str) -> Optional[Dict]:
        """Get a gene by name."""
        gene_data = self.database["genes"].get(gene_name)
        if gene_data and "is_polymerase" not in gene_data:
            gene_data["is_polymerase"] = False
        return gene_data

    def get_all_genes(self) -> List[str]:
        """Get all gene names."""
        return list(self.database["genes"].keys())

    def get_polymerase_genes(self) -> List[str]:
        """Get all genes marked as polymerase genes."""
        polymerase_genes = []
        for gene_name, gene_data in self.database["genes"].items():
            if gene_data.get("is_polymerase", False):
                polymerase_genes.append(gene_name)
        return polymerase_genes

    def is_polymerase_gene(self, gene_name: str) -> bool:
        """Check if a gene is marked as a polymerase gene."""
        gene_data = self.database["genes"].get(gene_name)
        if gene_data:
            return gene_data.get("is_polymerase", False)
        return False

    def _update_entities_from_genes(self):
        """Update entities list based on genes (for backwards compatibility)."""
        referenced_entities = set()

        for gene in self.database["genes"].values():
            for effect in gene.get("effects", []):
                if effect["type"] == "enable_entity":
                    referenced_entities.add(effect["entity"])
                elif effect["type"] in ["add_transition"]:
                    rule = effect["rule"]
                    for input_spec in rule["inputs"]:
                        referenced_entities.add(input_spec["entity"])
                    for output_spec in rule["outputs"]:
                        referenced_entities.add(output_spec["entity"])

        for entity_name in referenced_entities:
            if entity_name not in self.database["entities"]:
                self.database["entities"][entity_name] = {
                    "name": entity_name,
                    "description": f"Auto-generated entity: {entity_name}",
                    "base_degradation_rate": DEFAULT_DEGRADATION_RATE,
                    "location": self._guess_location_from_name(entity_name),
                    "entity_class": self._guess_class_from_name(entity_name),
                    "is_starter": False
                }

    # =================== MILESTONE MANAGEMENT ===================

    def add_milestone(self, milestone_data: Dict):
        """Add or update a milestone."""
        milestone_id = milestone_data["id"]
        self.database["milestones"][milestone_id] = milestone_data.copy()
        self.is_modified = True

    def delete_milestone(self, milestone_id: str):
        """Delete a milestone."""
        if milestone_id in self.database["milestones"]:
            del self.database["milestones"][milestone_id]
            self.is_modified = True

    def get_milestone(self, milestone_id: str) -> Optional[Dict]:
        """Get a milestone by ID."""
        return self.database["milestones"].get(milestone_id)

    def get_all_milestones(self) -> List[str]:
        """Get all milestone IDs."""
        return list(self.database["milestones"].keys())

    def get_milestones(self) -> Dict:
        """Get all milestones as a dict."""
        return self.database["milestones"].copy()

    def get_entity_classes(self) -> List[str]:
        """Get all unique entity classes defined in the database."""
        classes = set()
        for entity_data in self.database["entities"].values():
            entity_class = entity_data.get("entity_class", "unknown")
            if entity_class:
                classes.add(entity_class)
        return sorted(list(classes))

    def validate_milestone_data(self, milestone_data: Dict) -> tuple[bool, str]:
        """Validate milestone data structure and values."""
        required_fields = ["id", "name", "description", "type", "target", "reward_ep"]

        for field in required_fields:
            if field not in milestone_data:
                return False, f"Missing required field: {field}"

        milestone_id = milestone_data["id"]
        if not milestone_id.replace("_", "").replace("-", "").isalnum():
            return False, "Milestone ID must contain only letters, numbers, underscores, and hyphens"

        if milestone_data["type"] not in VALID_MILESTONE_TYPES:
            return False, f"Invalid milestone type. Must be one of: {', '.join(VALID_MILESTONE_TYPES)}"

        try:
            target = int(milestone_data["target"])
            if target <= 0:
                return False, "Target must be a positive integer"
        except (ValueError, TypeError):
            return False, "Target must be a valid positive integer"

        try:
            reward = int(milestone_data["reward_ep"])
            if reward < 0:
                return False, "Reward EP must be a non-negative integer"
        except (ValueError, TypeError):
            return False, "Reward EP must be a valid non-negative integer"

        if milestone_data["type"] in ["peak_entity_count", "cumulative_entity_count"]:
            if "entity_class" not in milestone_data:
                return False, "Entity count milestones must specify an entity_class"

            available_classes = self.get_entity_classes()
            if milestone_data["entity_class"] not in available_classes:
                return False, f"Invalid entity_class. Available classes: {', '.join(available_classes)}"

        return True, "Valid milestone data"

    def create_sample_database(self):
        """Create a sample database with example genes and milestones."""
        self.database = {
            "database_info": {
                "name": "Sample Virus Gene Database",
                "version": DATABASE_VERSION,
                "description": "Sample database with basic viral genes and milestones",
                "created_by": "Virus Sandbox",
                "created_date": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            },
            "entities": {
                "unenveloped virion (extracellular)": {
                    "name": "unenveloped virion (extracellular)",
                    "description": "Basic viral particle outside the cell",
                    "base_degradation_rate": 0.05,
                    "location": LOCATION_EXTRACELLULAR,
                    "entity_class": ENTITY_CLASS_VIRION,
                    "is_starter": True
                },
                "enveloped virion (extracellular)": {
                    "name": "enveloped virion (extracellular)",
                    "description": "Viral particle with lipid envelope",
                    "base_degradation_rate": 0.08,
                    "location": LOCATION_EXTRACELLULAR,
                    "entity_class": ENTITY_CLASS_VIRION,
                    "is_starter": True
                },
                "viral spore (extracellular)": {
                    "name": "viral spore (extracellular)",
                    "description": "Dormant viral form with enhanced resistance",
                    "base_degradation_rate": 0.02,
                    "location": LOCATION_EXTRACELLULAR,
                    "entity_class": ENTITY_CLASS_VIRION,
                    "is_starter": True
                },
                "virion in endosome (cytoplasm)": {
                    "name": "virion in endosome (cytoplasm)",
                    "description": "Viral particle inside cellular endosome",
                    "base_degradation_rate": 0.03,
                    "location": LOCATION_ENDOSOME,
                    "entity_class": ENTITY_CLASS_VIRION,
                    "is_starter": False
                },
                "viral polymerase (cytoplasm)": {
                    "name": "viral polymerase (cytoplasm)",
                    "description": "Viral RNA polymerase enzyme",
                    "base_degradation_rate": 0.08,
                    "location": LOCATION_CYTOPLASM,
                    "entity_class": ENTITY_CLASS_PROTEIN,
                    "is_starter": False
                },
                "viral RNA (cytoplasm)": {
                    "name": "viral RNA (cytoplasm)",
                    "description": "Viral genetic material",
                    "base_degradation_rate": 0.12,
                    "location": LOCATION_CYTOPLASM,
                    "entity_class": ENTITY_CLASS_RNA,
                    "is_starter": False
                },
                "mature viral proteins (cytoplasm)": {
                    "name": "mature viral proteins (cytoplasm)",
                    "description": "Processed viral proteins ready for assembly",
                    "base_degradation_rate": 0.06,
                    "location": LOCATION_CYTOPLASM,
                    "entity_class": ENTITY_CLASS_PROTEIN,
                    "is_starter": False
                }
            },
            "genes": self._create_sample_genes(),
            "milestones": self._create_sample_milestones()
        }
        self.is_modified = True

    def _create_sample_genes(self) -> Dict:
        """Create sample gene definitions."""
        return {
            "Basic Capsid": {
                "name": "Basic Capsid",
                "cost": 0,
                "description": "Basic viral capsid protein. Provides structural integrity.",
                "effects": [],
                "is_polymerase": False
            },
            "Glycoprotein S1": {
                "name": "Glycoprotein S1",
                "cost": 50,
                "description": "Surface protein enabling receptor binding and endocytosis",
                "effects": [
                    {
                        "type": "add_transition",
                        "rule": {
                            "name": "Receptor-mediated endocytosis",
                            "inputs": [
                                {"entity": "unenveloped virion (extracellular)", "count": 1, "consumed": True}
                            ],
                            "outputs": [
                                {"entity": "virion in endosome (cytoplasm)", "count": 1}
                            ],
                            "probability": 0.3,
                            "rule_type": "per_entity"
                        }
                    }
                ],
                "is_polymerase": False
            },
            "RNA-dependent RNA polymerase": {
                "name": "RNA-dependent RNA polymerase",
                "cost": 80,
                "description": "Enzyme enabling viral RNA replication",
                "effects": [
                    {
                        "type": "add_transition",
                        "rule": {
                            "name": "RNA replication",
                            "inputs": [
                                {"entity": "viral polymerase (cytoplasm)", "count": 1, "consumed": False},
                                {"entity": "viral RNA (cytoplasm)", "count": 1, "consumed": False}
                            ],
                            "outputs": [
                                {"entity": "viral RNA (cytoplasm)", "count": 1}
                            ],
                            "probability": 0.7,
                            "rule_type": "per_pair"
                        }
                    }
                ],
                "is_polymerase": True
            },
            "Membrane fusion protein": {
                "name": "Membrane fusion protein",
                "cost": 60,
                "description": "Protein that enables escape from endosomes",
                "requires": ["Glycoprotein S1"],
                "effects": [
                    {
                        "type": "add_transition",
                        "rule": {
                            "name": "Endosome escape",
                            "inputs": [
                                {"entity": "virion in endosome (cytoplasm)", "count": 1, "consumed": True}
                            ],
                            "outputs": [
                                {"entity": "viral RNA (cytoplasm)", "count": 2},
                                {"entity": "viral polymerase (cytoplasm)", "count": 1}
                            ],
                            "probability": 0.8,
                            "rule_type": "per_entity"
                        }
                    }
                ],
                "is_polymerase": False
            }
        }

    def _create_sample_milestones(self) -> Dict:
        """Create sample milestone definitions."""
        return {
            "survivor_5": {
                "id": "survivor_5",
                "name": "Basic Survival",
                "description": "Keep your virus alive for at least 5 turns",
                "type": "survive_turns",
                "target": 5,
                "reward_ep": 25
            },
            "survivor_15": {
                "id": "survivor_15",
                "name": "Extended Survival",
                "description": "Keep your virus alive for at least 15 turns",
                "type": "survive_turns",
                "target": 15,
                "reward_ep": 75
            },
            "protein_peak_10": {
                "id": "protein_peak_10",
                "name": "Protein Factory",
                "description": "Have 10 protein entities present simultaneously",
                "type": "peak_entity_count",
                "entity_class": ENTITY_CLASS_PROTEIN,
                "target": 10,
                "reward_ep": 50
            }
        }


class GeneDatabase:
    """Interface to gene database for virus building."""

    def __init__(self, database_manager: Optional[GeneDatabaseManager] = None):
        self.db_manager = database_manager

    def set_database_manager(self, database_manager: GeneDatabaseManager):
        """Set the database manager."""
        self.db_manager = database_manager

    def get_gene(self, name: str) -> Optional[Dict]:
        """Get a gene by name."""
        if not self.db_manager:
            return None
        return self.db_manager.get_gene(name)

    def get_all_genes(self) -> List[str]:
        """Get all gene names."""
        if not self.db_manager:
            return []
        return self.db_manager.get_all_genes()

    def get_available_genes(self, selected_genes: List[Dict]) -> List[str]:
        """Get genes that can be selected given current selection."""
        if not self.db_manager:
            return []

        available = []
        selected_gene_names = [gene["name"] for gene in selected_genes]

        for gene_name in self.db_manager.get_all_genes():
            if gene_name in selected_gene_names:
                continue

            gene_data = self.db_manager.get_gene(gene_name)
            if not gene_data:
                continue

            requires = gene_data.get("requires", [])
            if all(req in selected_gene_names for req in requires):
                available.append(gene_name)

        return available