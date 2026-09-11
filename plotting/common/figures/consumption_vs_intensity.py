"""
One country's commodity groups traced through time on consumption against
impact intensity.

Each group draws a line from its earliest year to its latest: x is daily
consumption per capita, y is impact per kilogram. The diagonal reference grid
marks constant total impact per capita, so a group moving parallel to the grid
has changed what it costs without changing what it contributes overall.

Solid lines are imported supply, dotted are domestic. The first year is marked
with a black dot, the last with a filled dot in the group's colour.

Port of the original plotting/Fig2GBplot.py, generalised over metrics.
"""

from pathlib import Path

import matplotlib.pyplot as plt

from .. import loaders, paths, style
from ..metrics import Metric

CONSUMPTION_COL = "consumed_tonnes"
CONSUMPTION_XLIM = (1e-2, 1.0)


def main(
    metric: Metric,
    country: str = "GBR",
    years: list[int] | None = None,
    results_dir: Path | None = None,
    show: bool = False,
) -> Path:
    results_dir = results_dir or paths.RESULTS_DIR
    intensity_col = "impact_per_kg"

    frames = {}
    for scope in ("domestic", "imported"):
        panel = loaders.load_panel(
            metric,
            [country],
            years,
            scope=scope,
            extra_cols=[CONSUMPTION_COL],
            results_dir=results_dir,
        )
        # load_panel put consumption into kg per capita per day already.
        panel[intensity_col] = panel[metric.total_col] / panel[CONSUMPTION_COL]
        frames[scope] = panel.sort_values("Year")

    fig, ax = plt.subplots(figsize=(10, 10))

    groups = sorted(
        set(frames["imported"]["Group"]) | set(frames["domestic"]["Group"]),
        key=lambda g: style.GROUP_ORDER_V7.get(g, 99),
    )

    for group in groups:
        colour = style.GROUP_COLORS_V7.get(group, style.FALLBACK_COLOR)
        for scope, linestyle in (("imported", "-"), ("domestic", ":")):
            data = frames[scope]
            data = data[data["Group"] == group].dropna(subset=[CONSUMPTION_COL, intensity_col])
            if data.empty:
                continue

            ax.plot(
                data[CONSUMPTION_COL],
                data[intensity_col],
                color=colour,
                linestyle=linestyle,
                zorder=2,
            )
            # First year hollow-dark, last year filled: shows direction of travel.
            ax.scatter(
                data[CONSUMPTION_COL].iloc[0],
                data[intensity_col].iloc[0],
                color="black",
                edgecolor=colour,
                marker="o",
                s=40,
                zorder=3,
            )
            ax.scatter(
                data[CONSUMPTION_COL].iloc[-1],
                data[intensity_col].iloc[-1],
                color=colour,
                edgecolor=colour,
                marker="o",
                s=40,
                zorder=3,
                label=group if scope == "domestic" else None,
            )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*CONSUMPTION_XLIM)
    ax.set_ylim(*metric.per_kg_ylim)

    style.iso_impact_grid(ax, CONSUMPTION_XLIM, metric.per_kg_ylim)

    ax.set_xlabel("Daily consumption per capita, kg")
    ax.set_ylabel(metric.label_per_kg)

    year_span = frames["imported"]["Year"]
    first, last = year_span.min(), year_span.max()
    when = (
        f"{first}" if first == last else f"{first} (black dot) to {last} (coloured)"
    )
    ax.set_title(
        f"{metric.name} per capita - {country}\n"
        f"Imports (solid) vs domestic production (dotted)\n{when}"
    )
    ax.legend(title="Food group", fontsize=8)

    style.add_product_axis(ax, f"Total daily {metric.unit} per capita")

    fig.tight_layout()

    out = paths.output_path(
        metric.key,
        f"consumption_vs_intensity_{metric.key}_{country}.png",
        results_dir=results_dir,
    )
    fig.savefig(out, dpi=600)
    print(f"Saved {out}")

    if show:
        plt.show()
    plt.close(fig)
    return out
