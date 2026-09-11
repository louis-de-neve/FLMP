#!/usr/bin/env python3
"""
Production greenhouse gas emissions: imported vs domestically produced, mirrored about zero.

Replaces plotting/Fig2internal_external_recreation.py.

    python plotting/ghgs/internal_external.py --countries GBR USA CHN
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from plotting.common import metrics
from plotting.common.cli import run_time_series
from plotting.common.figures import internal_external

if __name__ == "__main__":
    run_time_series(
        internal_external.main,
        metrics.GHG_PROD,
        description=__doc__,
    )
