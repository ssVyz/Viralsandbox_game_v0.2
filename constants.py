"""
Constants for Virus Sandbox Game

All magic numbers, configuration values, and game parameters.
"""

# =================== GAME ECONOMY ===================
DEFAULT_STARTING_EP = 100
DEFAULT_GENE_REMOVE_COST = 10
DEFAULT_STARTING_ENTITY_COUNT = 10
STARTING_ENTITY_COUNT_BONUS = 2  # Bonus when skipping gene offers

# =================== DECK BUILDING ===================
INITIAL_DECK_SIZE = 10
DEFAULT_GENE_OFFER_SIZE = 5
MAX_GENE_INSTALLS_PER_ROUND = 1

# =================== GAME CYCLES ===================
DEFAULT_CYCLE_LIMIT = 10
VICTORY_ENTITY_THRESHOLD = 10000  # Win condition

# =================== ENTITY PROPERTIES ===================
DEFAULT_DEGRADATION_RATE = 0.05
MIN_DEGRADATION_RATE = 0.0
MAX_DEGRADATION_RATE = 1.0

DEFAULT_BASE_ENTITY_NAME = "unenveloped virion (extracellular)"

# Entity locations
LOCATION_EXTRACELLULAR = "extracellular"
LOCATION_CYTOPLASM = "cytoplasm"
LOCATION_ENDOSOME = "endosome"
LOCATION_NUCLEUS = "nucleus"
LOCATION_MEMBRANE = "membrane"
LOCATION_UNKNOWN = "unknown"

VALID_LOCATIONS = [
    LOCATION_EXTRACELLULAR,
    LOCATION_CYTOPLASM,
    LOCATION_ENDOSOME,
    LOCATION_NUCLEUS,
    LOCATION_MEMBRANE,
    LOCATION_UNKNOWN
]

# Entity classes
ENTITY_CLASS_VIRION = "virion"
ENTITY_CLASS_PROTEIN = "protein"
ENTITY_CLASS_RNA = "RNA"
ENTITY_CLASS_DNA = "DNA"
ENTITY_CLASS_COMPLEX = "complex"
ENTITY_CLASS_UNKNOWN = "unknown"

VALID_ENTITY_CLASSES = [
    ENTITY_CLASS_VIRION,
    ENTITY_CLASS_PROTEIN,
    ENTITY_CLASS_RNA,
    ENTITY_CLASS_DNA,
    ENTITY_CLASS_COMPLEX,
    ENTITY_CLASS_UNKNOWN
]

# =================== INTERFERON SYSTEM ===================
INTERFERON_MIN = 0.0
INTERFERON_MAX = 100.0
INTERFERON_DECAY_PER_TURN = 1.0
INTERFERON_PRECISION = 2  # Decimal places

# Interferon degradation bonuses (multiplier per interferon level)
INTERFERON_RNA_DEGRADATION_BONUS = 0.0125  # 1.25% per level
INTERFERON_PROTEIN_DEGRADATION_BONUS = 0.0075  # 0.75% per level
INTERFERON_DNA_DEGRADATION_BONUS = 0.005  # 0.5% per level

# Interferon thresholds for display
INTERFERON_THRESHOLD_HIGH = 75.0
INTERFERON_THRESHOLD_MEDIUM = 50.0
INTERFERON_THRESHOLD_LOW = 25.0

# =================== TRANSITION RULES ===================
RULE_TYPE_PER_ENTITY = "per_entity"
RULE_TYPE_PER_PAIR = "per_pair"

VALID_RULE_TYPES = [RULE_TYPE_PER_ENTITY, RULE_TYPE_PER_PAIR]

# Effect types
EFFECT_TYPE_ADD_TRANSITION = "add_transition"
EFFECT_TYPE_MODIFY_TRANSITION = "modify_transition"
EFFECT_TYPE_ENABLE_ENTITY = "enable_entity"

VALID_EFFECT_TYPES = [
    EFFECT_TYPE_ADD_TRANSITION,
    EFFECT_TYPE_MODIFY_TRANSITION,
    EFFECT_TYPE_ENABLE_ENTITY
]

# =================== MILESTONES ===================
MILESTONE_TYPE_SURVIVE_TURNS = "survive_turns"
MILESTONE_TYPE_PEAK_ENTITY_COUNT = "peak_entity_count"
MILESTONE_TYPE_CUMULATIVE_ENTITY_COUNT = "cumulative_entity_count"

VALID_MILESTONE_TYPES = [
    MILESTONE_TYPE_SURVIVE_TURNS,
    MILESTONE_TYPE_PEAK_ENTITY_COUNT,
    MILESTONE_TYPE_CUMULATIVE_ENTITY_COUNT
]

# =================== DATABASE ===================
DATABASE_VERSION = "1.0"
DATABASE_DEFAULT_NAME = "Untitled Database"

# =================== UI CONSTANTS ===================

# Window sizes
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 700

# Dialog sizes
GENE_OFFER_DIALOG_WIDTH = 460
GENE_OFFER_DIALOG_HEIGHT = 360
EFFECT_EDITOR_DIALOG_WIDTH = 700
EFFECT_EDITOR_DIALOG_HEIGHT = 650
VICTORY_DIALOG_WIDTH = 500
VICTORY_DIALOG_HEIGHT = 400

# Font configurations
FONT_TITLE = ("Arial", 24, "bold")
FONT_SUBTITLE = ("Arial", 12, "italic")
FONT_HEADER = ("Arial", 16, "bold")
FONT_SUBHEADER = ("Arial", 14, "bold")
FONT_BODY = ("Arial", 11)
FONT_SMALL = ("Arial", 10)
FONT_TINY = ("Arial", 9)
FONT_ITALIC_SMALL = ("Arial", 9, "italic")
FONT_CONSOLE = ("Consolas", 11)
FONT_UI_MONO = ("Segoe UI", 11)

# Colors
COLOR_TEXT_PRIMARY = "#2d3748"
COLOR_TEXT_SECONDARY = "#4a5568"
COLOR_TEXT_LIGHT = "#6b7280"
COLOR_TEXT_DISABLED = "#d1d5db"

COLOR_BG_WHITE = "#fbfbfb"
COLOR_BG_LIGHT = "#f7fafc"
COLOR_BG_SELECTION = "#e2e8f0"
COLOR_BG_HOVER = "#bee3f8"

COLOR_SUCCESS = "#16a34a"
COLOR_WARNING = "#ea580c"
COLOR_DANGER = "#dc2626"
COLOR_INFO = "#2563eb"
COLOR_YELLOW = "#ca8a04"

COLOR_BORDER = "#e5e7eb"

# Graph colors for entity types
COLOR_GRAPH_VIRION = "#6b7280"  # Grey
COLOR_GRAPH_RNA = "#22c55e"     # Green
COLOR_GRAPH_DNA = "#3b82f6"     # Blue
COLOR_GRAPH_PROTEIN = "#f97316"  # Orange

# =================== GRAPH SETTINGS ===================
GRAPH_HEIGHT = 200
GRAPH_MAX_HISTORY = 50
GRAPH_GRID_LINES_Y = 5
GRAPH_GRID_LINES_X = 10
GRAPH_MARGIN_LEFT = 40
GRAPH_MARGIN_RIGHT = 20
GRAPH_MARGIN_TOP = 20
GRAPH_MARGIN_BOTTOM = 30

# =================== SIMULATION DISPLAY ===================
CONSOLE_SEPARATOR_FULL = "=" * 70
CONSOLE_SEPARATOR_HALF = "-" * 70
CONSOLE_SEPARATOR_SECTION = "-" * 35

DRAMATIC_DISPLAY_DELAY = 0.1  # Seconds between events

# =================== BUILDER SETTINGS ===================
BUILDER_GENE_LIST_HEIGHT = 8
BUILDER_EFFECT_LIST_HEIGHT = 6
BUILDER_DETAILS_TEXT_HEIGHT = 15

# =================== EDITOR SETTINGS ===================
EDITOR_LISTBOX_WIDTH = 35
EDITOR_LISTBOX_HEIGHT = 20
EDITOR_DESC_TEXT_HEIGHT = 3
EDITOR_DESC_TEXT_WIDTH = 60
EDITOR_GENE_DESC_HEIGHT = 3
EDITOR_GENE_DESC_WIDTH = 60

# Input/output limits in effect editor
EFFECT_EDITOR_MAX_INPUTS = 3
EFFECT_EDITOR_MAX_OUTPUTS = 3

# =================== LOCATION DISPLAY ORDER ===================
LOCATION_DISPLAY_ORDER = [
    LOCATION_EXTRACELLULAR,
    LOCATION_MEMBRANE,
    LOCATION_ENDOSOME,
    LOCATION_CYTOPLASM,
    LOCATION_NUCLEUS
]

LOCATION_DISPLAY_LABELS = {
    LOCATION_EXTRACELLULAR: "EXTRACELLULAR",
    LOCATION_MEMBRANE: "MEMBRANE",
    LOCATION_CYTOPLASM: "CYTOPLASM",
    LOCATION_ENDOSOME: "ENDOSOME",
    LOCATION_NUCLEUS: "NUCLEUS"
}

# =================== FILE TYPES ===================
FILE_TYPE_JSON = [("JSON files", "*.json"), ("All files", "*.*")]
DEFAULT_SAMPLE_FILENAME = "sample_virus_genes.json"

# =================== TEXT WIDGET STYLING ===================
TEXT_WIDGET_CONFIG = {
    "font": FONT_UI_MONO,
    "bg": COLOR_BG_WHITE,
    "fg": COLOR_TEXT_PRIMARY,
    "selectbackground": COLOR_BG_SELECTION,
    "selectforeground": COLOR_TEXT_PRIMARY,
    "insertbackground": COLOR_TEXT_SECONDARY,
    "relief": "flat",
    "borderwidth": 1,
    "highlightthickness": 0,
    "padx": 12,
    "pady": 8
}

CONSOLE_WIDGET_CONFIG = {
    "font": FONT_CONSOLE,
    "bg": COLOR_BG_LIGHT,
    "fg": COLOR_TEXT_PRIMARY,
    "selectbackground": COLOR_BG_HOVER,
    "selectforeground": "#1a202c",
    "insertbackground": COLOR_TEXT_SECONDARY,
    "relief": "flat",
    "borderwidth": 1,
    "highlightthickness": 0,
    "padx": 10,
    "pady": 6
}