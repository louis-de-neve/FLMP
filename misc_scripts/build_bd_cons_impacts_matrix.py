"""
Builds a country x commodity matrix of biodiversity opportunity cost per
tonne (bd_opp_total / tonnage), plus a matching matrix of its error, from
the impacts_aggregated_<ISO3>.csv files for a given year.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

RESULTS_DIR = Path("../flmp_results/flmp_results_261009")
YEAR = 2021


def build_bd_intensity_matrix(results_dir: Path, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:

    files = sorted((results_dir / "impacts" / str(year)).glob("impacts_aggregated_*.csv"))

    rows = []
    for f in tqdm(files, desc=f"Reading impacts_aggregated files for {year}"):
        iso = f.stem.split("_")[-1]
        df = pd.read_csv(f, usecols=["Item", "throughput_tonnes", "life_extinctions_per_sp_total_calc", "life_extinctions_per_sp_total_calc_err"])
        df = df.groupby("Item", as_index=False)[["throughput_tonnes", "life_extinctions_per_sp_total_calc", "life_extinctions_per_sp_total_calc_err"]].sum()

        tonnage = df["throughput_tonnes"].where(df["throughput_tonnes"] != 0, np.nan)
        df["ratio"] = df["life_extinctions_per_sp_total_calc"] / tonnage
        df["err_ratio"] = df["life_extinctions_per_sp_total_calc_err"] / tonnage
        df["Country"] = iso

        rows.append(df[["Country", "Item", "ratio", "err_ratio"]])

    long_df = pd.concat(rows, ignore_index=True)

    matrix = long_df.pivot_table(index="Country", columns="Item", values="ratio")
    err_matrix = long_df.pivot_table(index="Country", columns="Item", values="err_ratio")

    return matrix, err_matrix


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=YEAR)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()

    matrix, err_matrix = build_bd_intensity_matrix(args.results_dir, args.year)

    out_dir = args.results_dir / "impacts_matrices"
    out_dir.mkdir(exist_ok=True)

    matrix.to_csv(out_dir / f"bd_opp_per_tonne_used_{args.year}.csv")
    err_matrix.to_csv(out_dir / f"bd_opp_per_tonne_used_err_{args.year}.csv")

    print(f"Wrote {matrix.shape[0]} x {matrix.shape[1]} matrices to {out_dir}")
