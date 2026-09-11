#!/usr/bin/env python3
"""
Total greenhouse gas cost per capita under alternative diet scenarios:
production emissions plus carbon opportunity cost.

Each bar stacks two components per commodity group, in the group's colour:
production emissions solid, carbon opportunity cost hatched. COC is a one-off
release when land is converted rather than a recurring flow, so it is spread
over an assumed 30-year production lifetime (main.py's AMORTIZATION_YEARS)
before being put on the same per-day axis.

    # both figures: full commodity grouping, and animal vs vegetal
    python plotting/diets/ghgs_with_coc.py --country GBR --both

    # just one of them
    python plotting/diets/ghgs_with_coc.py --country GBR
    python plotting/diets/ghgs_with_coc.py --country GBR --coarse
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
        extra_metrics=(metrics.GHG_COC,),
    )
