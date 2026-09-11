"""
Palettes, group orderings, label tidying and the small reference tables that
nearly every figure needs.

Two commodity groupings are in play and they are easy to confuse:

  group_name_v7   8 coarse groups ("Ruminant meat", "Dairy and eggs", ...).
                  provenance/_process_dat.py writes this into the `Group`
                  column of impacts_aggregated.csv and df_*.csv, so figures
                  reading those files are already grouped this way.

  group_name_v6   24 fine groups ("Ruminant meat", "Pig meat", "Dairy", "Rice",
                  ...). Not present in the results; figures that want it merge
                  it on from commodity_crosswalk.csv by Item_Code.
"""

import warnings

import matplotlib.pyplot as plt
import pandas as pd

from . import paths

# --- group_name_v7: the 8 coarse groups -------------------------------------

GROUP_COLORS_V7 = {
    "Grains, roots, starchy carbohydrates": "#E69F00",
    "Legumes, beans, nuts": "#F0E442",
    "Fruit and vegetables": "#009E73",
    "Stimulants and spices": "#56B4E9",
    "Ruminant meat": "#D55E00",
    "Dairy and eggs": "#0072B2",
    "Poultry and pig meat": "#CC79A7",
    "Sugar crops": "#93F840",
    "Total": "#000000",
}

# Lighter end of each group's ramp, for the item-level shading inside a mosaic.
GROUP_COLORS_V7_LIGHT = {
    "Grains, roots, starchy carbohydrates": "#ffd066",
    "Legumes, beans, nuts": "#f7f1a1",
    "Fruit and vegetables": "#00ffba",
    "Stimulants and spices": "#fb9b98",
    "Ruminant meat": "#ffaa66",
    "Dairy and eggs": "#33b6ff",
    "Poultry and pig meat": "#e3b5ce",
    "Sugar crops": "#c7fb9d",
}

# Plot order: animal products first, then staples, then the rest.
GROUP_ORDER_V7 = {
    "Ruminant meat": 0,
    "Poultry and pig meat": 1,
    "Dairy and eggs": 2,
    "Grains, roots, starchy carbohydrates": 3,
    "Fruit and vegetables": 4,
    "Legumes, beans, nuts": 5,
    "Stimulants and spices": 6,
    "Sugar crops": 7,
    "Total": 8,
}

# --- group_name_v6: the 24 fine groups --------------------------------------

GROUP_COLORS_V6 = {
    "Ruminant meat": "#C90D75",
    "Pig meat": "#D64A98",
    "Poultry meat": "#D880B1",
    "Dairy": "#F7BDDD",
    "Eggs": "#FFEDF7",
    "Grains": "#D55E00",
    "Rice": "#D88E53",
    "Soybeans": "#DCBA9E",
    "Roots and tubers": "#0072B2",
    "Vegetables": "#4F98C1",
    "Legumes and pulses": "#9EBFD2",
    "Bananas": "#FFED00",
    "Tropical fruit": "#FFF357",
    "Temperate fruit": "#FDF8B9",
    "Tropical nuts": "#27E2FF",
    "Temperate nuts": "#7DEEFF",
    "Sugar beet": "#FFC000",
    "Sugar cane": "#F7C93B",
    "Spices": "#009E73",
    "Coffee": "#33CCA2",
    "Cocoa": "#62DEBC",
    "Tea and maté": "#A2F5DE",
    "Oilcrops": "#000000",
    "Other": "#A2A2A2",
}

FALLBACK_COLOR = "#A2A2A2"

# --- coarse two-way split -----------------------------------------------------

ANIMAL_GROUPS_V7 = frozenset(
    {"Ruminant meat", "Poultry and pig meat", "Dairy and eggs"}
)

ANIMAL_PRODUCTS = "Animal products"
VEGETAL_PRODUCTS = "Vegetal products"

COARSE_COLORS = {
    ANIMAL_PRODUCTS: "#D55E00",
    VEGETAL_PRODUCTS: "#009E73",
}

COARSE_ORDER = {ANIMAL_PRODUCTS: 0, VEGETAL_PRODUCTS: 1}


def to_coarse_group(group_v7: str) -> str:
    """Collapse a group_name_v7 value to animal vs vegetal."""
    return ANIMAL_PRODUCTS if group_v7 in ANIMAL_GROUPS_V7 else VEGETAL_PRODUCTS


def grouping_palette(coarse: bool) -> tuple[dict[str, str], dict[str, int]]:
    """Colours and plot order for whichever grouping a figure is using."""
    if coarse:
        return COARSE_COLORS, COARSE_ORDER
    return GROUP_COLORS_V7, GROUP_ORDER_V7

REGION_COLORS = {
    "Asia": "#c2bf01ca",
    "Europe": "#2b56e2aa",
    "Americas": "#41d341c7",
    "Africa": "#ff0000aa",
    "Oceania": "#f700ffaa",
}

# The blue used for the "iso-impact" reference grid and its twin axis.
GRID_COLOR = "#2F7FF8"


def group_order_frame(order: dict[str, int] | None = None) -> pd.DataFrame:
    """The group ordering as a two-column frame, for merging onto plot data."""
    return pd.DataFrame((order or GROUP_ORDER_V7).items(), columns=["Group", "Order"])


def label_formatting(label: str) -> str:
    """Shorten a FAOSTAT item name enough to fit inside a mosaic tile."""
    if "Other" in label:
        label = "Other"
    if ";" in label:
        label = label.split(";")[0]
    if "with the bone" in label:
        label = label.replace("with the bone", "")
    if "Cashew" in label:
        label = "Cashews"
    if "Maize" in label:
        label = "Maize"
    if "Oil palm" in label:
        label = "Palm oil"
    return label


def invert_color(hex_color: str) -> str:
    """Complement of a hex colour, used to outline a bar against its own fill."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (255 - int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"#{r:02x}{g:02x}{b:02x}"


# --- reference tables -------------------------------------------------------


def load_area_codes(rename_to: str = "FAO_Code") -> pd.DataFrame:
    """ISO3 <-> FAOSTAT area code lookup.

    `rename_to` names the FAOSTAT column, because different figures join it
    against differently named columns ("FAO_Code", "Effective_Producer_Code").
    """
    with warnings.catch_warnings():
        # openpyxl warns about the workbook's unsupported default style.
        warnings.simplefilter("ignore")
        area_codes = pd.read_excel(paths.AREA_CODES_FILE, engine="openpyxl")
    return area_codes[["ISO3", "FAOSTAT"]].rename(columns={"ISO3": "Country", "FAOSTAT": rename_to})


def load_population() -> pd.DataFrame:
    """Per-country population by year, in individuals.

    FAOSTAT element 511 is total population, reported in thousands.
    """
    pop = pd.read_csv(paths.SUA_DATA_FILE, encoding="latin-1", low_memory=False)
    pop = pop[pop["Element Code"] == 511][["Area Code", "Year", "Value"]].copy()
    pop["Value"] *= 1000
    return pop


def load_region_map() -> pd.DataFrame:
    """ISO3 -> region, with the region's plotting colour attached."""
    regions = pd.DataFrame(REGION_COLORS.items(), columns=["region", "Color"])
    region_map = pd.read_csv(paths.REGIONS_FILE)[["alpha-3", "region"]]
    return region_map.merge(regions, on="region", how="left")


def load_commodity_crosswalk(grouping: str = "group_name_v6") -> pd.DataFrame:
    """Item_Code -> fine commodity group."""
    crosswalk = pd.read_csv(paths.COMMODITY_CROSSWALK_FILE)
    return crosswalk[["Item_Code", grouping]]


def group_legend(fig, ncol: int = 4, fontsize: int = 8):
    """Put one commodity-group legend on the figure, below the panels.

    A figure-level legend keeps the key out of the data area, which matters
    because the busiest panel is often the one the legend would land on.
    """
    handles, labels = [], []
    for group, colour in sorted(
        GROUP_COLORS_V7.items(), key=lambda kv: GROUP_ORDER_V7.get(kv[0], 99)
    ):
        if group == "Total":
            continue
        handles.append(plt.Rectangle((0, 0), 1, 1, color=colour))
        labels.append(group)
    return fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=ncol,
        fontsize=fontsize,
        frameon=False,
        bbox_to_anchor=(0.5, 0.0),
    )


def iso_impact_grid(ax, xlim: tuple[float, float], ylim: tuple[float, float]) -> None:
    """Draw the hyperbolic x*y = constant reference lines on a log-log axis.

    Each solid line is a decade of the product (e.g. total impact per capita),
    with dashed minor lines between them. The decade range is derived from the
    axis limits rather than hardcoded, so it suits any metric's scale.
    """
    import numpy as np

    (x1, x2), (y1, y2) = xlim, ylim
    # A line x*y = c is visible only if c falls within the box's corner
    # products; going wider just paints lines outside the axes.
    lo = int(np.floor(np.log10(x1 * y1)))
    hi = int(np.ceil(np.log10(x2 * y2)))
    x = np.logspace(np.log10(x1), np.log10(x2), 50)

    # Minor lines get crowded once the box spans many decades, so drop them
    # when they would stop reading as a grid.
    draw_minor = (hi - lo) <= 6

    for decade in range(lo, hi + 1):
        ax.plot(x, (10.0**decade) / x, color=GRID_COLOR, alpha=0.4, linewidth=0.8, zorder=1)
        if not draw_minor:
            continue
        for minor in np.linspace(2 * 10.0**decade, 9 * 10.0**decade, 8):
            ax.plot(x, minor / x, ls="dashed", color=GRID_COLOR, alpha=0.2, linewidth=0.8, zorder=1)


def add_product_axis(ax, label: str):
    """Twin x-axis labelling the product of the two axes (the iso-grid value)."""
    twin = ax.twiny()
    twin.set_xscale("log")
    x1, x2 = ax.get_xlim()
    _, y2 = ax.get_ylim()
    twin.set_xlim(x1 * y2, x2 * y2)
    twin.set_xlabel(label, color=GRID_COLOR)
    twin.tick_params(axis="x", colors=GRID_COLOR)
    return twin
