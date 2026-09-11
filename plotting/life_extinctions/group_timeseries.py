#!/usr/bin/env python3
"""
Extinction opportunity cost per capita per day, stacked by commodity group, one panel per country.

Replaces plotting/Fig2recreation.py.

    python plotting/life_extinctions/group_timeseries.py --countries GBR USA CHN
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from plotting.common import metrics
from plotting.common.cli import run_time_series
from plotting.common.figures import group_timeseries

if __name__ == "__main__":
    run_time_series(
        group_timeseries.main,
        metrics.LIFE_EXTINCTIONS,
        description=__doc__,
        relative_option=True,
    )
