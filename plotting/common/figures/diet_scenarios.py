"""
Per-capita impact of a country's current consumption under alternative diets.

One stacked bar per diet scenario, split by commodity group. The country's
measured impact is rescaled group by group according to how much of that group
each diet contains relative to the baseline diet, then normalised to a
per-person, per-day figure.

Port of the original misc_scripts/FigX_UKdiets.py, generalised over metrics.

More than one metric can be stacked in a single bar - production emissions plus
carbon opportunity cost, say. Each group then occupies a contiguous block of
its own colour, with the first metric drawn solid and later ones hatched.
Because COC is a one-off release rather than a recurring flow, it is divided by
an assumed production lifetime first (see `Metric.amortized`).

How a scenario is scaled
------------------------
For each commodity group the measured impact is multiplied by

    group_scalar / cal_scalar / p_scalar

where `group_scalar` is the diet's mass of that group over the baseline's,
`cal_scalar` is the diet's calories over the baseline's, and `p_scalar` is the
diet's total mass over the baseline's. Dividing by calories and by total mass
holds the comparison at constant energy intake rather than letting a scenario
look better simply by containing less food.

Stimulants and sugar are held at the baseline: the diet files do not vary them
meaningfully and letting them float added noise to the totals.

Faithfulness note: `p_scalar` sums every non-"Cals" row of the diet file. For
the UK file that includes the helper rows ("Fruit", "Sugar", "Stimulants",
"Scalar") that carry no group_name_v6 match and so contribute nothing
elsewhere. This reproduces the original script's arithmetic exactly; it is
called out here because it is easy to mistake for an oversight.
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd

from .. import paths, style
from ..metrics import AMORTIZATION_YEARS, Metric

# Groups pinned to their baseline value across every scenario.
UNCHANGED_GROUPS = ("Stimulants and spices", "Sugar crops")

DEFAULT_SKIP = ("EAT-Lancet",)

# Hatch applied to the 2nd, 3rd, ... metric stacked in a bar.
HATCHES = (None, "///", "...", "xxx")

# Populations the original script hardcoded, kept as a fallback for countries
# where the FAOSTAT series has no entry for the year.
FALLBACK_POPULATION = {"GBR": 69_487_000, "USA": 342_500_000}


def diets_file_for(country: str) -> Path:
    alias = {"GBR": "UK", "USA": "US"}.get(country.upper(), country.upper())
    path = paths.DIETS_DIR / f"diets5_{alias}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"No diet definition for {country} in {paths.DIETS_DIR}. "
            f"Available: {sorted(p.name for p in paths.DIETS_DIR.glob('diets5_*.csv'))}"
        )
    return path


def load_diets(country: str, skip: tuple[str, ...] = DEFAULT_SKIP) -> pd.DataFrame:
    """Diet scenarios for `country`, with the group_name_v7 mapping attached.

    The files are latin-1 encoded (they contain "Tea and mate" with an accent).
    """
    diets = pd.read_csv(diets_file_for(country), encoding="latin-1")
    diets = diets.drop(columns=[c for c in diets.columns if c in skip])

    crosswalk = pd.read_csv(paths.COMMODITY_CROSSWALK_FILE)
    v6_to_v7 = crosswalk[["group_name_v6", "group_name_v7"]].drop_duplicates()
    return diets.merge(v6_to_v7, left_on="Group", right_on="group_name_v6", how="left")


def load_group_impacts(
    metrics: list[Metric],
    country: str,
    year: int,
    coarse: bool = False,
    results_dir: Path | None = None,
) -> pd.DataFrame:
    """Measured impact for `year`, totalled by group, one column per metric."""
    path = paths.country_dir(year, country, results_dir) / "impacts_full.csv"
    if not path.exists():
        raise FileNotFoundError(f"No impacts_full.csv for {country} in {year}: {path}")

    value_cols = [m.row_col for m in metrics]
    df = pd.read_csv(path, usecols=["ItemT_Code", *value_cols])
    by_item = df.groupby("ItemT_Code", as_index=False)[value_cols].sum()

    crosswalk = pd.read_csv(paths.COMMODITY_CROSSWALK_FILE)
    item_to_v7 = crosswalk[["Item_Code", "group_name_v7"]].drop_duplicates()
    by_item = by_item.merge(item_to_v7, left_on="ItemT_Code", right_on="Item_Code", how="left")

    totals = by_item.groupby("group_name_v7", as_index=False)[value_cols].sum()
    if coarse:
        totals["group"] = totals["group_name_v7"].map(style.to_coarse_group)
    else:
        totals["group"] = totals["group_name_v7"]
    return totals


def species_count(spam_year: int = 2020) -> float:
    """Number of species assessed in the LIFE/MAPSPAM layer."""
    path = paths.mapspam_results_file(spam_year)
    if not path.exists():
        raise FileNotFoundError(f"MAPSPAM results not found: {path}")
    return pd.read_csv(path, usecols=["sp_count"])["sp_count"].max()


def resolve_population(country: str, year: int) -> float:
    """FAOSTAT population, falling back to the original script's constants."""
    area_codes = style.load_area_codes("FAO_Code")
    population = style.load_population()
    code = area_codes.loc[area_codes["Country"] == country.upper(), "FAO_Code"]
    if not code.empty:
        match = population[
            (population["Area Code"] == code.iloc[0]) & (population["Year"] == year)
        ]
        if not match.empty:
            return float(match["Value"].iloc[0])

    if country.upper() in FALLBACK_POPULATION:
        return float(FALLBACK_POPULATION[country.upper()])
    raise KeyError(f"No population available for {country} in {year}")


def normalisation(
    metric: Metric, population: float, amortization_years: int
) -> float:
    """Factor turning a national total into a per-person, per-day figure."""
    factor = 1.0 / (population * 365)
    if metric.normalise_by_species_count:
        factor /= species_count()
    if metric.amortized:
        factor /= amortization_years
    return factor


def diet_scalars(diets: pd.DataFrame, diet: str) -> tuple[float, float]:
    """(calorie scalar, total-mass scalar) for one diet against the baseline."""
    is_cals = diets["Group"] == "Cals"
    cal_scalar = diets.loc[is_cals, diet].sum() / diets.loc[is_cals, "Baseline"].sum()

    # Total mass proxy - see the module docstring on which rows this includes.
    mass = ~is_cals
    p_scalar = diets.loc[mass, diet].sum() / diets.loc[mass, "Baseline"].sum()
    return cal_scalar, p_scalar


def group_scalar(diets: pd.DataFrame, diet: str, group_v7: str, cal_scalar: float) -> float:
    """How much of `group_v7` this diet carries relative to the baseline."""
    in_group = diets["group_name_v7"] == group_v7
    baseline = diets.loc[in_group, "Baseline"].sum()
    if group_v7 in UNCHANGED_GROUPS or baseline == 0:
        return 1.0
    return diets.loc[in_group, diet].sum() / baseline / cal_scalar


def scenario_table(
    diets: pd.DataFrame,
    group_impacts: pd.DataFrame,
    metrics: list[Metric],
    scenarios: list[str],
    population: float,
    amortization_years: int,
) -> pd.DataFrame:
    """Long table of (diet, group, metric) -> per-capita per-day value."""
    factors = {m.key: normalisation(m, population, amortization_years) for m in metrics}

    rows = []
    for diet in scenarios:
        cal_scalar, p_scalar = diet_scalars(diets, diet)
        for _, impact_row in group_impacts.iterrows():
            scalar = group_scalar(diets, diet, impact_row["group_name_v7"], cal_scalar) / p_scalar
            for metric in metrics:
                rows.append(
                    {
                        "diet": diet,
                        "group": impact_row["group"],
                        "metric": metric.key,
                        "value": impact_row[metric.row_col] * scalar * factors[metric.key],
                    }
                )

    table = pd.DataFrame(rows)
    # Several v7 groups can fold into one coarse group, so sum after scaling.
    return table.groupby(["diet", "group", "metric"], as_index=False)["value"].sum()


def main(
    metric: Metric,
    extra_metrics: tuple[Metric, ...] = (),
    country: str = "GBR",
    year: int = 2021,
    skip: tuple[str, ...] = DEFAULT_SKIP,
    coarse: bool = False,
    population: float | None = None,
    amortization_years: int = AMORTIZATION_YEARS,
    results_dir: Path | None = None,
    show: bool = False,
) -> Path:
    results_dir = results_dir or paths.RESULTS_DIR
    country = country.upper()
    metrics = [metric, *extra_metrics]

    diets = load_diets(country, skip)
    group_impacts = load_group_impacts(metrics, country, year, coarse, results_dir)
    population = population or resolve_population(country, year)

    scenarios = [c for c in diets.columns[1:] if c not in ("group_name_v6", "group_name_v7")]
    table = scenario_table(
        diets, group_impacts, metrics, scenarios, population, amortization_years
    )

    colors, order = style.grouping_palette(coarse)
    groups = sorted(table["group"].unique(), key=lambda g: order.get(g, 99))

    fig, ax = plt.subplots(figsize=(8, 6) if not coarse else (7, 6))

    for x, diet in enumerate(scenarios):
        bottom = 0.0
        for group in groups:
            colour = colors.get(group, style.FALLBACK_COLOR)
            # Each group is one contiguous block: solid first metric, then the
            # hatched remainder, so the split is readable within the group.
            for depth, m in enumerate(metrics):
                sel = table[
                    (table["diet"] == diet)
                    & (table["group"] == group)
                    & (table["metric"] == m.key)
                ]
                if sel.empty:
                    continue
                value = float(sel["value"].iloc[0])
                ax.bar(
                    x,
                    value,
                    bottom=bottom,
                    color=colour,
                    hatch=HATCHES[depth % len(HATCHES)],
                    edgecolor="white" if depth else "none",
                    linewidth=0.0,
                )
                bottom += value

    totals = table.groupby("diet")["value"].sum().reindex(scenarios)
    for diet, total in totals.items():
        print(f"{diet}: {total:.4g}")

    ax.set_xticks(range(len(scenarios)))
    ax.set_xticklabels(scenarios, rotation=45, ha="right")
    ax.set_ylabel(_ylabel(metrics))
    ax.set_title(_title(metrics, country, year, amortization_years))

    _legend(ax, groups, colors, metrics)

    fig.tight_layout()

    name = "_".join(m.key for m in metrics)
    suffix = "coarse" if coarse else "groups"
    out = paths.output_path(
        metrics[0].key,
        f"diet_scenarios_{name}_{suffix}_{country}_{year}.png",
        results_dir=results_dir,
    )
    fig.savefig(out, dpi=600, bbox_inches="tight")
    print(f"Saved {out}")

    table.to_csv(out.with_suffix(".csv"), index=False)
    print(f"Saved {out.with_suffix('.csv')}")

    if show:
        plt.show()
    plt.close(fig)
    return out


def _legend(ax, groups, colors, metrics: list[Metric]) -> None:
    """Group colours, plus a hatch key when more than one metric is stacked."""
    handles = [
        mpatches.Patch(color=colors.get(g, style.FALLBACK_COLOR), label=g) for g in groups
    ]
    if len(metrics) > 1:
        handles.append(mpatches.Patch(facecolor="white", edgecolor="white", label=" "))
        for depth, m in enumerate(metrics):
            handles.append(
                mpatches.Patch(
                    facecolor="#7a7a7a",
                    hatch=HATCHES[depth % len(HATCHES)],
                    edgecolor="white",
                    label=m.name,
                )
            )
    ax.legend(handles=handles, fontsize=8)


def _ylabel(metrics: list[Metric]) -> str:
    if metrics[0].normalise_by_species_count:
        return r"Mean change in extinction risk" "\n" r"($\Delta E$ per sp., per capita per day)"
    return f"Emissions per capita per day ({metrics[0].unit})"


def _title(metrics: list[Metric], country: str, year: int, amortization_years: int) -> str:
    names = " + ".join(m.name for m in metrics)
    title = f"{names}\nby diet scenario - {country}, {year}"
    if any(m.amortized for m in metrics):
        title += f"\n(carbon opportunity cost amortized over {amortization_years} years)"
    return title
