"""
Shared library for the FLMP plotting scripts.

Figures live in `plotting.common.figures` and are written against a
`plotting.common.metrics.Metric` rather than against a hardcoded column name,
so the same figure serves extinctions, production GHG and carbon opportunity
cost. The runnable entrypoints are the thin scripts in `plotting/<metric>/`.
"""

from . import metrics, paths, style

__all__ = ["metrics", "paths", "style"]
