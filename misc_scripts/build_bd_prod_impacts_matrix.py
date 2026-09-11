"""
Builds a producer country x commodity matrix of the extinction opportunity cost
per kilogram of PRODUCTION (bd_opp_cost_calc / production_kg), plus a matching
matrix of its error, from the impacts_full.csv files for a given year.

Where build_bd_cons_impacts_matrix.py answers "what does a tonne of commodity X
consumed by country Y cost?", this answers "what does a kilogram of commodity X
*produced* in country Y cost?". Every consumer country's impacts_full.csv is read
and each row reattributed to the country that actually produced it, following the
logic of plotting/Fig1recreation.py. Extinctions only - the cost-of-conservation
columns (coc_*) are ignored.
"""

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

RESULTS_DIR = Path("../flmp_results/flmp_results_261009")
INPUT_DATA_DIR = Path("input_data")
YEAR = 2021

USECOLS = [
    "Consumer_Country_Code",
    "Producer_Country_Code",
    "Animal_Product_Code",
    "ItemT_Code",
    "ItemT_Name",
    "provenance_tonnes",
    "life_extinctions_per_sp_calc",
    "life_extinctions_per_sp_calc_err",
]
VALUE_COLS = ["life_extinctions_per_sp_calc", "life_extinctions_per_sp_calc_err", "production_tonnes"]
GROUPING = "group_name_v6"


def build_prod_impacts_long(results_dir: Path, year: int) -> tuple[pd.DataFrame, dict]:
    """Sum extinction cost and production tonnage by (item, producing country).

    Rows where Animal_Product_Code is NaN are the crops and the primary animal
    products: they carry the production itself, so they are attributed to
    Producer_Country_Code. The remaining rows are feed, whose
    Consumer_Country_Code is the country that raised the animal - their impact
    lands on that country's animal product, but they add no production tonnage.
    """

    files = sorted((results_dir / str(year)).glob("*/impacts_full.csv"))
    if not files:
        raise FileNotFoundError(f"No impacts_full.csv files under {results_dir / str(year)}")

    item_names: dict[float, str] = {}
    rows = []
    for f in tqdm(files, desc=f"Reading impacts_full files for {year}"):
        df = pd.read_csv(f, usecols=USECOLS)

        is_primary = df["Animal_Product_Code"].isna()
        df["Effective_Producer_Code"] = df["Producer_Country_Code"].where(
            is_primary, df["Consumer_Country_Code"]
        )
        df["production_tonnes"] = df["provenance_tonnes"].where(is_primary, 0.0)

        item_names.update(
            df[["ItemT_Code", "ItemT_Name"]].dropna().drop_duplicates().set_index("ItemT_Code")["ItemT_Name"]
        )

        rows.append(
            df.groupby(["ItemT_Code", "Effective_Producer_Code"], as_index=False)[VALUE_COLS].sum()
        )

    long_df = pd.concat(rows, ignore_index=True)
    long_df = long_df.groupby(["ItemT_Code", "Effective_Producer_Code"], as_index=False)[VALUE_COLS].sum()

    return long_df, item_names


def add_labels(long_df: pd.DataFrame, item_names: dict, input_data_dir: Path) -> pd.DataFrame:
    """Attach the producer ISO3, the item name and the commodity group."""

    long_df = long_df.copy()
    long_df["ItemT_Name"] = long_df["ItemT_Code"].map(item_names)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        area_codes = pd.read_excel(
            input_data_dir / "nocsDataExport_20251021-164754.xlsx", engine="openpyxl"
        )
    area_codes = area_codes[["ISO3", "FAOSTAT"]].rename(
        columns={"ISO3": "Country", "FAOSTAT": "Effective_Producer_Code"}
    )
    long_df = long_df.merge(area_codes, on="Effective_Producer_Code", how="left")

    commodity_crosswalk = pd.read_csv(input_data_dir / "commodity_crosswalk.csv")
    long_df = long_df.merge(
        commodity_crosswalk[["Item_Code", GROUPING]],
        left_on="ItemT_Code",
        right_on="Item_Code",
        how="left",
    ).drop(columns=["Item_Code"])

    return long_df


def impact_per_kg(bd: pd.Series, tonnes: pd.Series) -> pd.Series:
    """Extinctions per kg, NaN (not inf) where no production was traced."""
    kg = tonnes * 1000
    return bd.where(kg > 0) / kg.where(kg > 0)


def mask_undefined_errors(err: pd.Series, label: str) -> pd.Series:
    """A handful of upstream rows carry bd_opp_cost_calc_err = inf while their
    bd_opp_cost_calc is finite (7 rows, in BDI and TCD, for 2021/spam2020).
    Summing errors linearly propagates that to every cell those rows touch, so
    write those cells as NaN - error unknown - rather than inf."""
    undefined = np.isinf(err)
    if undefined.any():
        print(
            f"Warning: {undefined.sum()} {label} cells have an undefined error "
            f"(inf bd_opp_cost_calc_err upstream) and are written as NaN"
        )
    return err.mask(undefined)


def build_matrices(long_df: pd.DataFrame, level: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pivot to Country x <level>, summing before dividing so the group-level
    intensity is production-weighted rather than a mean of per-item ratios."""

    df = long_df.dropna(subset=["Country", level])
    df = df.groupby(["Country", level], as_index=False)[VALUE_COLS].sum()

    df["impact_per_kg"] = impact_per_kg(df["life_extinctions_per_sp_calc"], df["production_tonnes"])
    df["impact_per_kg_err"] = mask_undefined_errors(
        impact_per_kg(df["life_extinctions_per_sp_calc_err"], df["production_tonnes"]), level
    )

    matrix = df.pivot(index="Country", columns=level, values="impact_per_kg")
    err_matrix = df.pivot(index="Country", columns=level, values="impact_per_kg_err")

    return matrix, err_matrix


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=YEAR)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--input-data-dir", type=Path, default=INPUT_DATA_DIR)
    args = parser.parse_args()

    long_df, item_names = build_prod_impacts_long(args.results_dir, args.year)
    long_df = add_labels(long_df, item_names, args.input_data_dir)

    long_df["impact_per_kg"] = impact_per_kg(long_df["life_extinctions_per_sp_calc"], long_df["production_tonnes"])
    long_df["impact_per_kg_err"] = mask_undefined_errors(
        impact_per_kg(long_df["life_extinctions_per_sp_calc_err"], long_df["production_tonnes"]),
        "long-format",
    )

    item_matrix, item_err_matrix = build_matrices(long_df, "ItemT_Name")
    group_matrix, group_err_matrix = build_matrices(long_df, GROUPING)

    out_dir = args.results_dir / "impacts_matrices"
    out_dir.mkdir(exist_ok=True)

    item_matrix.to_csv(out_dir / f"bd_prod_extinctions_per_kg_item_{args.year}.csv")
    item_err_matrix.to_csv(out_dir / f"bd_prod_extinctions_per_kg_item_err_{args.year}.csv")
    group_matrix.to_csv(out_dir / f"bd_prod_extinctions_per_kg_group_{args.year}.csv")
    group_err_matrix.to_csv(out_dir / f"bd_prod_extinctions_per_kg_group_err_{args.year}.csv")

    long_df[
        [
            "Country",
            "Effective_Producer_Code",
            "ItemT_Code",
            "ItemT_Name",
            GROUPING,
            "life_extinctions_per_sp_calc",
            "life_extinctions_per_sp_calc_err",
            "production_tonnes",
            "impact_per_kg",
            "impact_per_kg_err",
        ]
    ].to_csv(out_dir / f"bd_prod_extinctions_long_{args.year}.csv", index=False)

    print(f"Wrote {item_matrix.shape[0]} x {item_matrix.shape[1]} item matrices to {out_dir}")
    print(f"Wrote {group_matrix.shape[0]} x {group_matrix.shape[1]} group matrices to {out_dir}")
