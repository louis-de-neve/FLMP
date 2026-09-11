"""
Readers for the pipeline's per-country result files.

These wrap the repeated "read impacts_aggregated.csv, group it, divide by
population" block that the original Fig2* scripts each carried their own copy
of. Metric columns are selected via a `Metric` so the same loader serves every
impact.
"""

from pathlib import Path

import pandas as pd

from . import paths, style
from .metrics import Metric

# Which file holds which slice of a country's consumption.
SCOPES = {
    "total": "impacts_aggregated.csv",  # everything the country consumed
    "domestic": None,                   # df_<iso>.csv - produced at home
    "imported": "df_os.csv",            # produced overseas
}


def scope_filename(scope: str, iso3: str) -> str:
    """Filename holding `scope` for country `iso3`."""
    if scope not in SCOPES:
        raise ValueError(f"Unknown scope {scope!r}. Available: {sorted(SCOPES)}")
    if scope == "domestic":
        return f"df_{iso3.lower()}.csv"
    return SCOPES[scope]


def load_country_year(
    metric: Metric,
    year: int,
    iso3: str,
    scope: str = "total",
    extra_cols: list[str] | None = None,
    results_dir: Path | None = None,
) -> pd.DataFrame:
    """Per-group impact for one country-year, or an empty frame if absent.

    Returns columns: Group, <metric totals>, [extra_cols], Year, Country.
    """
    path = paths.country_dir(year, iso3, results_dir) / scope_filename(scope, iso3)
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path, index_col=0)
    cols = ["Group", *metric.aggregated_cols(), *(extra_cols or [])]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(
            f"{path} is missing {missing}. "
            f"Was it produced by a pipeline run that computed {metric.key}?"
        )

    df = df[cols].groupby("Group", as_index=False).sum()
    df["Year"] = int(year)
    df["Country"] = iso3
    return df


def load_panel(
    metric: Metric,
    countries: list[str],
    years: list[int] | None = None,
    scope: str = "total",
    extra_cols: list[str] | None = None,
    per_capita: bool = True,
    per_day: bool = True,
    results_dir: Path | None = None,
) -> pd.DataFrame:
    """Country x year x group panel, optionally normalised per capita per day.

    `extra_cols` are carried through and normalised alongside the metric
    columns, except that tonnage columns are converted to kilograms - the
    original scripts divided `consumed_tonnes` by `population * 365 / 1000`.
    """
    years = years or paths.available_years(results_dir)

    frames = []
    for year in years:
        for iso3 in countries:
            df = load_country_year(metric, year, iso3, scope, extra_cols, results_dir)
            if not df.empty:
                frames.append(df)

    if not frames:
        raise FileNotFoundError(
            f"No {scope} results found for {countries} in {years} under "
            f"{results_dir or paths.RESULTS_DIR}"
        )

    panel = pd.concat(frames, ignore_index=True)

    if per_capita:
        panel = _normalise(panel, metric, extra_cols or [], per_day=per_day)

    order = style.group_order_frame()
    panel = panel.merge(order, on="Group", how="left")
    panel = panel.sort_values(["Country", "Year", "Order"]).drop(columns=["Order"])
    return panel.reset_index(drop=True)


def _normalise(
    panel: pd.DataFrame, metric: Metric, extra_cols: list[str], per_day: bool
) -> pd.DataFrame:
    """Divide impact columns by population (and days), in place on a copy."""
    area_codes = style.load_area_codes("FAO_Code")
    population = style.load_population()

    panel = panel.merge(area_codes, on="Country", how="left")
    panel = panel.merge(
        population, left_on=["FAO_Code", "Year"], right_on=["Area Code", "Year"], how="left"
    )

    denominator = panel["Value"] * (365 if per_day else 1)
    for col in metric.aggregated_cols():
        panel[col] = panel[col] / denominator
    for col in extra_cols:
        # Tonnages become kilograms so a per-capita figure reads in kg.
        panel[col] = panel[col] / (denominator / 1000 if "tonnes" in col else denominator)

    return panel.drop(columns=["FAO_Code", "Area Code", "Value"])
