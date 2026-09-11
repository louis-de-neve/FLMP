#!/usr/bin/env python3
"""
Extinction opportunity cost per kilogram, distribution by commodity group.

Replaces the original plotting/Fig1recreation.py.

    python plotting/life_extinctions/per_kg_distribution.py --year 2021
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from plotting.common import metrics
from plotting.common.cli import run_single_year
from plotting.common.figures import per_kg_distribution

if __name__ == "__main__":
    run_single_year(
        per_kg_distribution.main,
        metrics.LIFE_EXTINCTIONS,
        description=__doc__,
    )
