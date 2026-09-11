#!/usr/bin/env python3
"""
Extinction opportunity cost per capita under alternative diet scenarios.

Replaces misc_scripts/FigX_UKdiets.py (kept at plotting/legacy/FigX_UKdiets.py).

    python plotting/diets/life_extinctions.py --country GBR
    python plotting/diets/life_extinctions.py --country USA --year 2021
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from plotting.common import metrics
from plotting.common.cli import run_diet_scenarios
from plotting.common.figures import diet_scenarios

if __name__ == "__main__":
    run_diet_scenarios(
        diet_scenarios.main,
        metrics.LIFE_EXTINCTIONS,
        description=__doc__,
    )
