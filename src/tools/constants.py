"""Shared constants for the tools package."""

from enum import Enum

# Grid and site detection parameters
Z_AXIS_PENETRATION_LIMIT = -1.0
EPSILON_TOLERANCE = 0.3
DEFAULT_PRECISION = 0.25

# Collision detection and geometry optimization
COLLISION_SAFETY_BUFFER_ANGSTROM = 0.2
MIN_COLLISION_THRESHOLD_ANGSTROM = 1.6
PRE_LIFT_HEIGHT_ANGSTROM = 0.5

# Bonding criteria for chemical analysis
BASE_BOND_MULTIPLIER = 1.30
STRONG_ADSORPTION_BOND_MULTIPLIER = 1.45
STRONG_ADSORPTION_THRESHOLD_EV = -0.5

# Subsurface layer detection for crystallographic analysis
SUBSURFACE_LOWER_BOUND_ANGSTROM = 1.2
SUBSURFACE_UPPER_BOUND_ANGSTROM = 4.0
HCP_DETECTION_RADIUS_ANGSTROM = 1.0

# Slab and vacuum handling
MIN_CELL_SIZE_ANGSTROM = 6.0
MIN_VACUUM_THICKNESS_ANGSTROM = 15.0

# Surface relaxation settings
FIXED_BOTTOM_FRACTION = 1.0 / 3.0


class RelaxationMode(Enum):
    """
    Surface relaxation mode for adsorption calculations.

    FAST: All surface atoms fixed. Suitable for rapid screening on laptops.
    STANDARD: Bottom 1/3 of slab fixed, top 2/3 + adsorbate relaxed.
    """

    FAST = "fast"
    STANDARD = "standard"
