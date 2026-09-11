"""
Domestically produced vs imported impact, mirrored about zero, one panel per
country.

Impact from home-grown food is drawn below the axis and impact embodied in
imports above it, so the split between what a country does to its own land and
what it displaces abroad is readable at a glance.

Port of the original plotting/Fig2internal_external_recreation.py, generalised
over metrics.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn.objects as so

from .. import loaders, paths, style
from ..metrics import Metric
from .group_timeseries import _panel_grid, stacked_mark


def main(
    metric: Metric,
    countries: list[str] | None = None,
    years: list[int] | None = None,
    results_dir: Path | None = None,
    show: bool = False,
) -> Path:
    results_dir = results_dir or paths.RESULTS_DIR
    countries = countries or ["GBR", "POL", "CHN", "IND", "RWA", "USA"]
    value_col = metric.total_col

    domestic = loaders.load_panel(
        metric, countries, years, scope="domestic", results_dir=results_dir
    )
    imported = loaders.load_panel(
        metric, countries, years, scope="imported", results_dir=results_dir
    )

    # Domestic production hangs below the axis.
    domestic = domestic.copy()
    for col in metric.aggregated_cols():
        domestic[col] = domestic[col] * -1

    plotted = [c for c in countries if c in set(domestic["Country"])]
    n_years = domestic["Year"].nunique()
    mark = stacked_mark(n_years)
    fig, axs = _panel_grid(len(plotted))

    for ax, country in zip(axs, plotted):
        for source in (domestic, imported):
            country_df = source[source["Country"] == country]
            if country_df.empty:
                continue
            (
                so.Plot(country_df, x="Year", y=value_col, color="Group")
                .add(mark, so.Stack(), legend=False)
                .scale(color=style.GROUP_COLORS_V7)
                .on(ax)
                .plot()
            )

        # Symmetric limits so the two halves are visually comparable.
        span = np.abs(ax.get_ylim()).max()
        ax.set_ylim(-span, span)
        ax.set_title(country)
        ax.set_ylabel("")
        ax.axhline(0, color="black", linewidth=0.8)
        if n_years > 1:
            ax.set_xlim(domestic["Year"].min(), domestic["Year"].max())
        else:
            ax.set_xticks([domestic["Year"].iloc[0]])

    for ax in axs[len(plotted) :]:
        ax.set_visible(False)

    axs[0].set_ylabel(f"{metric.label_per_capita_day}\nimported (+) vs domestic (-)")

    for ax in axs[: max(0, len(plotted) - 2)]:
        ax.set_xlabel("")
        ax.set_xticklabels([])

    fig.suptitle(f"{metric.name}: imported vs domestically produced")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    style.group_legend(fig)

    out = paths.output_path(
        metric.key, f"internal_external_{metric.key}.png", results_dir=results_dir
    )
    fig.savefig(out, dpi=600)
    print(f"Saved {out}")

    if show:
        plt.show()
    plt.close(fig)
    return out
