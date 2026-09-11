"""
The impact metrics the plotting scripts can draw, and the column names each one
lives under in the pipeline outputs.

The pipeline computes three impacts side by side for every commodity flow, and
they only differ by column name and by the units on the axis. Rather than keep
one copy of each figure per impact, the figures take a `Metric` and read their
columns from it.

Column naming follows the pipeline outputs (see provenance/_process_dat.py):

  impacts_full.csv        one row per (consumer, producer, item) flow
                          -> `row_col`, `row_err_col`, `per_m2_col`
  impacts_aggregated.csv  one row per (item, group), food/feed split out
  df_<iso>.csv            as above, domestically produced only
  df_os.csv               as above, imported only
                          -> `food_col`, `feed_col`, `total_col`, `total_err_col`
  food_commodity_impacts.csv
                          -> `per_kg_col`, `per_kg_err_col`

Note `GHG_PROD.total_err_col is None`. provenance/_get_impacts_bd.py does
propagate an error onto `ghg_prod_kgco2e_calc_err` in impacts_full.csv, but
_process_dat.py never aggregates it into the food/feed/total columns the way it
does for life and coc. Figures therefore skip error bars for production GHG;
they draw them for any metric where the column exists.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Metric:
    """One impact metric: where to read it, and how to label and scale it."""

    key: str
    """Short slug, used in output filenames."""

    name: str
    """Human-readable name for titles."""

    # --- columns in impacts_aggregated.csv / df_<iso>.csv / df_os.csv ---
    food_col: str
    feed_col: str
    total_col: str
    total_err_col: str | None

    # --- columns in impacts_full.csv ---
    row_col: str
    row_err_col: str | None
    per_m2_col: str | None

    # --- columns in food_commodity_impacts.csv ---
    per_kg_col: str
    per_kg_err_col: str | None

    # --- presentation ---
    unit: str
    """Unit of the raw total, e.g. "extinctions" or "kg CO2e"."""

    label_total: str
    label_per_kg: str
    label_per_capita_day: str

    # --- axis limits, per metric because the scales differ by ~12 orders ---
    per_kg_ylim: tuple[float, float]
    """Sensible log-scale y range for a per-kilogram intensity axis."""

    per_capita_day_ylim: tuple[float, float]
    """Sensible log-scale range for a per-capita-per-day total axis."""

    normalise_by_species_count: bool = False
    """Whether figures should divide totals by the MAPSPAM species count.

    Extinction figures report a mean change in risk *per species*, so they
    divide the summed delta-E by the number of species assessed. Emissions are
    absolute mass and take no such divisor.
    """

    amortized: bool = False
    """Whether `row_col` is a one-off stock that must be spread over years.

    Carbon opportunity cost is the carbon released once when land is converted,
    while production emissions recur every year. Putting the two on one annual
    axis means dividing the stock by an assumed production lifetime - the
    AMORTIZATION_YEARS setting in main.py, 30 by default. The pipeline applies
    this only in food_commodity_impacts.csv, so `row_col` as read from
    impacts_full.csv is un-amortized and figures must do it themselves.
    """

    @property
    def has_error(self) -> bool:
        """Whether an aggregated error column exists to draw error bars from."""
        return self.total_err_col is not None

    def aggregated_cols(self, include_error: bool = True) -> list[str]:
        """The food/feed/total columns to select out of an aggregated CSV."""
        cols = [self.food_col, self.feed_col, self.total_col]
        if include_error and self.total_err_col is not None:
            cols.append(self.total_err_col)
        return cols


LIFE_EXTINCTIONS = Metric(
    key="life_extinctions",
    name="Extinction opportunity cost",
    food_col="life_extinctions_per_sp_food_calc",
    feed_col="life_extinctions_per_sp_feed_calc",
    total_col="life_extinctions_per_sp_total_calc",
    total_err_col="life_extinctions_per_sp_total_calc_err",
    row_col="life_extinctions_per_sp_calc",
    row_err_col="life_extinctions_per_sp_calc_err",
    per_m2_col="life_extinctions_per_sp_per_m2",
    per_kg_col="life_extinctions_per_sp_per_kg",
    per_kg_err_col="life_extinctions_per_sp_per_kg_err",
    unit="extinctions",
    label_total=r"Extinction opportunity cost ($\Delta$E)",
    label_per_kg=r"Extinction opportunity cost ($\Delta$E per kilogram)",
    label_per_capita_day=r"Extinctions per capita per day ($\Delta$E)",
    per_kg_ylim=(1e-13, 1e-7),
    per_capita_day_ylim=(1e-13, 1e-7),
    normalise_by_species_count=True,
)

GHG_PROD = Metric(
    key="ghg_prod",
    name="Production greenhouse gas emissions",
    food_col="ghg_prod_food_kgco2e_calc",
    feed_col="ghg_prod_feed_kgco2e_calc",
    total_col="ghg_prod_total_kgco2e_calc",
    # Not aggregated by _process_dat.py - see module docstring.
    total_err_col=None,
    row_col="ghg_prod_kgco2e_calc",
    row_err_col="ghg_prod_kgco2e_calc_err",
    # Production emissions are a per-kilogram factor, not a per-area one.
    per_m2_col=None,
    per_kg_col="ghg_prod_kgco2e_per_kg",
    per_kg_err_col=None,
    unit="kg CO$_2$e",
    label_total="Production emissions (kg CO$_2$e)",
    label_per_kg="Production emissions (kg CO$_2$e per kilogram)",
    label_per_capita_day="Production emissions per capita per day (kg CO$_2$e)",
    per_kg_ylim=(1e-1, 2e2),
    per_capita_day_ylim=(1e-2, 1e2),
)

# Carbon opportunity cost. Defined here so it is one line to wire up, but no
# runner scripts point at it yet - the per-year values are amortized over
# AMORTIZATION_YEARS in main.py, which the labels below assume.
GHG_COC = Metric(
    key="ghg_coc",
    name="Carbon opportunity cost",
    food_col="ghg_coc_food_kgco2e_calc",
    feed_col="ghg_coc_feed_kgco2e_calc",
    total_col="ghg_coc_total_kgco2e_calc",
    total_err_col="ghg_coc_total_kgco2e_calc_err",
    row_col="ghg_coc_kgco2e_calc",
    row_err_col="ghg_coc_kgco2e_calc_err",
    per_m2_col="carbon_kgco2e_per_m2",
    per_kg_col="ghg_coc_kgco2e_per_kg_per_year",
    per_kg_err_col="ghg_coc_kgco2e_per_kg_per_year_err",
    unit="kg CO$_2$e",
    label_total="Carbon opportunity cost (kg CO$_2$e)",
    label_per_kg="Carbon opportunity cost (kg CO$_2$e per kilogram per year)",
    label_per_capita_day="Carbon opportunity cost per capita per day (kg CO$_2$e)",
    per_kg_ylim=(1e-2, 1e3),
    per_capita_day_ylim=(1e-2, 1e2),
    amortized=True,
)

# The default production lifetime COC is spread over, matching main.py.
AMORTIZATION_YEARS = 30

REGISTRY: dict[str, Metric] = {m.key: m for m in (LIFE_EXTINCTIONS, GHG_PROD, GHG_COC)}


def get(key: str) -> Metric:
    """Look up a metric by key, with a useful message on a typo."""
    try:
        return REGISTRY[key]
    except KeyError:
        raise KeyError(f"Unknown metric {key!r}. Available: {sorted(REGISTRY)}") from None
