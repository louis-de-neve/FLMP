"""
Per-capita impact through time, stacked by commodity group, one panel per
country.

Port of the original plotting/Fig2recreation.py, generalised over metrics.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn.objects as so

from .. import loaders, paths, style
from ..metrics import Metric


def _panel_grid(n: int):
    """A roughly square grid of axes, sized to the number of countries."""
    ncols = 1 if n == 1 else 2
    nrows = -(-n // ncols)
    fig, axs = plt.subplots(
        nrows=nrows, ncols=ncols, figsize=(5 * ncols, 3.4 * nrows), squeeze=False
    )
    return fig, axs.flatten()


def stacked_mark(n_years: int):
    """Area for a real time series, bars when only one year is on disk.

    A stacked area over a single x value has zero width and draws nothing, so a
    results directory holding one year would otherwise produce blank panels.
    """
    return so.Bar(alpha=1, width=0.4) if n_years < 2 else so.Area(alpha=1)


def main(
    metric: Metric,
    countries: list[str] | None = None,
    years: list[int] | None = None,
    relative: bool = False,
    results_dir: Path | None = None,
    show: bool = False,
) -> Path:
    results_dir = results_dir or paths.RESULTS_DIR
    countries = countries or ["GBR", "POL", "CHN", "IND", "RWA", "USA"]

    panel = loaders.load_panel(metric, countries, years, scope="total", results_dir=results_dir)
    value_col = metric.total_col

    if relative:
        totals = panel.groupby(["Country", "Year"])[value_col].sum().rename("Total").reset_index()
        panel = panel.merge(totals, on=["Country", "Year"])
        panel[value_col] = panel[value_col] / panel["Total"] * 100
        panel = panel.drop(columns=["Total"])

    plotted = [c for c in countries if c in set(panel["Country"])]
    n_years = panel["Year"].nunique()
    mark = stacked_mark(n_years)
    fig, axs = _panel_grid(len(plotted))

    for ax, country in zip(axs, plotted):
        country_df = panel[panel["Country"] == country]
        (
            so.Plot(country_df, x="Year", y=value_col, color="Group")
            .add(mark, so.Stack(), legend=False)
            .scale(color=style.GROUP_COLORS_V7)
            .on(ax)
            .plot()
        )
        ax.set_title(country)
        ax.set_ylabel("")
        if n_years > 1:
            ax.set_xlim(panel["Year"].min(), panel["Year"].max())
        else:
            # Keep the single bar from being stretched across a default range.
            ax.set_xticks([panel["Year"].iloc[0]])
        if relative:
            ax.set_ylim(0, 100)

    for ax in axs[len(plotted) :]:
        ax.set_visible(False)

    label = "Share of total (%)" if relative else metric.label_per_capita_day
    axs[0].set_ylabel(label)

    # Drop x tick labels on every row but the last, as in the original.
    for ax in axs[: max(0, len(plotted) - 2)]:
        ax.set_xlabel("")
        ax.set_xticklabels([])

    fig.suptitle(f"{metric.name} per capita per day")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    style.group_legend(fig)

    suffix = "relative" if relative else "total"
    out = paths.output_path(
        metric.key, f"group_timeseries_{metric.key}_{suffix}.png", results_dir=results_dir
    )
    fig.savefig(out, dpi=600)
    print(f"Saved {out}")

    if show:
        plt.show()
    plt.close(fig)
    return out
