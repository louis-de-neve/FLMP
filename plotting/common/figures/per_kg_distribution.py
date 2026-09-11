"""
Distribution of impact per kilogram of production, by commodity group.

One bar per commodity group spanning the production-weighted 10th-90th
percentile of its per-kilogram intensity across producing countries, with the
weighted median marked. This is the figure that shows the same commodity
costing very different amounts depending on where it was grown.

Port of the original plotting/Fig1recreation.py, generalised over metrics.

Impacts are reattributed from the consuming country to the *producing* one:
rows with no Animal_Product_Code (crops, and primary animal products) carry
production and are credited to Producer_Country_Code, while feed rows are
credited to Consumer_Country_Code - the country that raised the animal - and
contribute impact but no production tonnage. This follows the same logic as
misc_scripts/build_bd_prod_impacts_matrix.py.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

from .. import paths, style
from ..metrics import Metric

QUANTILES = (10, 50, 90)


def load_production_impacts(metric: Metric, year: int, results_dir: Path | None = None) -> pd.DataFrame:
    """Impact and production tonnage per (item, producing country) for `year`.

    Reads every country's impacts_full.csv. Only the handful of needed columns
    are parsed - these files are ~80MB each and there are ~250 of them.
    """
    results_dir = results_dir or paths.RESULTS_DIR
    files = sorted(paths.year_dir(year, results_dir).glob("*/impacts_full.csv"))
    if not files:
        raise FileNotFoundError(
            f"No impacts_full.csv files under {paths.year_dir(year, results_dir)}"
        )

    usecols = [
        "Consumer_Country_Code",
        "Producer_Country_Code",
        "Animal_Product_Code",
        "ItemT_Code",
        metric.row_col,
        "provenance_tonnes",
    ]
    value_cols = [metric.row_col, "production_tonnes"]

    frames = []
    for f in tqdm(files, desc=f"Reading {year} impacts_full", unit="country"):
        df = pd.read_csv(f, usecols=usecols)

        # "Primary" marks an animal product's own production row; NaN marks a
        # crop. Both carry production, everything else is feed.
        carries_production = df["Animal_Product_Code"].isna() | (
            df["Animal_Product_Code"] == "Primary"
        )
        df["Effective_Producer_Code"] = df["Producer_Country_Code"].where(
            carries_production, df["Consumer_Country_Code"]
        )
        df["production_tonnes"] = df["provenance_tonnes"].where(carries_production, 0.0)

        frames.append(
            df.groupby(["ItemT_Code", "Effective_Producer_Code"], as_index=False)[value_cols].sum()
        )

    long_df = pd.concat(frames, ignore_index=True)
    return long_df.groupby(["ItemT_Code", "Effective_Producer_Code"], as_index=False)[
        value_cols
    ].sum()


def add_groups_and_intensity(long_df: pd.DataFrame, metric: Metric, grouping: str) -> pd.DataFrame:
    """Attach the commodity group and compute impact per kilogram."""
    crosswalk = style.load_commodity_crosswalk(grouping)
    df = long_df.merge(crosswalk, left_on="ItemT_Code", right_on="Item_Code", how="left")

    kg = df["production_tonnes"] * 1000
    # NaN rather than inf where no production was traced to this cell.
    df["impact_per_kg"] = df[metric.row_col].where(kg > 0) / kg.where(kg > 0)
    return df


def summarise_groups(df: pd.DataFrame, grouping: str) -> pd.DataFrame:
    """Production-weighted percentiles of per-kg intensity, one row per group.

    Weighting by production means a group's median reflects where the world's
    output actually comes from, not an unweighted average over countries.
    """
    rows = []
    for group in df[grouping].dropna().unique():
        data = df[(df[grouping] == group) & df["impact_per_kg"].notna()]
        data = data[data["impact_per_kg"] > 0]
        if data.empty:
            continue

        q10, median, q90 = (
            np.percentile(
                a=data["impact_per_kg"],
                q=q,
                weights=data["production_tonnes"],
                method="inverted_cdf",
            )
            for q in QUANTILES
        )
        rows.append(
            {
                grouping: group,
                "q10": q10,
                "median_impact": median,
                "q90": q90,
                "colour": style.GROUP_COLORS_V6.get(group, style.FALLBACK_COLOR),
                "count": len(data),
            }
        )

    summary = pd.DataFrame(rows).sort_values("median_impact", ignore_index=True)
    summary["range"] = summary["q90"] - summary["q10"]
    return summary


def _padded_limits(summary: pd.DataFrame, pad_decades: float = 0.35) -> tuple[float, float]:
    """Log-scale limits that enclose the drawn bars with a little headroom."""
    lo = summary["q10"].min()
    hi = summary["q90"].max()
    return 10 ** (np.log10(lo) - pad_decades), 10 ** (np.log10(hi) + pad_decades)


def plot(
    ax,
    summary: pd.DataFrame,
    metric: Metric,
    grouping: str,
    ylim: tuple[float, float] | None = None,
) -> None:
    """Draw the percentile bars with a median rule across each.

    `ylim` defaults to the data's own range; pass `metric.per_kg_ylim` to pin
    the axis when figures need to be comparable across runs.
    """
    for i, row in summary.iterrows():
        ax.bar(x=i, height=row["range"], bottom=row["q10"], color=row["colour"])
        # Zero-height bar = a rule marking the median, outlined to stay visible
        # against its own fill colour.
        ax.bar(
            x=i,
            height=0,
            bottom=row["median_impact"],
            fill=False,
            edgecolor=style.invert_color(row["colour"]),
            linewidth=2,
        )

    ticks = [f"(n={c}) {g}" for g, c in zip(summary[grouping], summary["count"])]
    ax.set_xticks(range(len(summary)), ticks, rotation=90, ha="center")
    ax.set_xlim(-0.6, len(summary) - 0.4)
    ax.set_ylim(*(ylim or _padded_limits(summary)))
    ax.set_yscale("log")
    ax.set_ylabel(metric.label_per_kg)


def main(
    metric: Metric,
    year: int = 2021,
    results_dir: Path | None = None,
    grouping: str = "group_name_v6",
    ylim: tuple[float, float] | None = None,
    show: bool = False,
) -> Path:
    results_dir = results_dir or paths.RESULTS_DIR

    long_df = load_production_impacts(metric, year, results_dir)
    long_df = add_groups_and_intensity(long_df, metric, grouping)
    summary = summarise_groups(long_df, grouping)

    print(summary[[grouping, "q10", "median_impact", "q90", "count"]].to_string(index=False))

    fig, ax = plt.subplots(figsize=(8, 7))
    plot(ax, summary, metric, grouping, ylim=ylim)
    ax.set_title(f"{metric.name} per kilogram of production, {year}")

    out = paths.output_path(
        metric.key, f"per_kg_distribution_{metric.key}_{year}.png", results_dir=results_dir
    )
    fig.savefig(out, dpi=600, bbox_inches="tight")
    print(f"Saved {out}")

    csv_out = out.with_suffix(".csv")
    summary.to_csv(csv_out, index=False)
    print(f"Saved {csv_out}")

    if show:
        plt.show()
    plt.close(fig)
    return out
