#!/usr/bin/env python3
"""
Production greenhouse gas emissions per capita under alternative diet
scenarios.

The GHG counterpart of plotting/diets/life_extinctions.py. Emissions are
absolute mass, so unlike the extinction version nothing is divided by a
species count.

    python plotting/diets/ghgs.py --country GBR
    python plotting/diets/ghgs.py --country USA --year 2021
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
        metrics.GHG_PROD,
        description=__doc__,
    )
