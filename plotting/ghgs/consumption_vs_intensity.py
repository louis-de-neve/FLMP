#!/usr/bin/env python3
"""
Production greenhouse gas emissions: one country's commodity groups traced through time on
consumption against impact intensity.

Replaces plotting/Fig2GBplot.py.

    python plotting/ghgs/consumption_vs_intensity.py --country GBR
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from plotting.common import metrics
from plotting.common.cli import run_one_country
from plotting.common.figures import consumption_vs_intensity

if __name__ == "__main__":
    run_one_country(
        consumption_vs_intensity.main,
        metrics.GHG_PROD,
        description=__doc__,
    )
