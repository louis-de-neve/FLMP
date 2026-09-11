#!/usr/bin/env python3
"""
Extinction opportunity cost: one country's commodity groups traced through time on
consumption against impact intensity.

Replaces plotting/Fig2GBplot.py.

    python plotting/life_extinctions/consumption_vs_intensity.py --country GBR
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
        metrics.LIFE_EXTINCTIONS,
        description=__doc__,
    )
