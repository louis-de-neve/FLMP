"""Global production-weighted LIFE (extinction opportunity cost) values per kg.

Same aggregation as Fig1recreation.py, but writes CSVs instead of plotting:
  - per item:  global_life_per_kg_items_{year}.csv
  - per group: global_life_per_kg_groups_{year}.csv

Impacts (incl. feed) are attributed to the effective producer country (the
consumer country for processed animal products, the producer otherwise), and
each (item, producer) pair is weighted by its production (tonnes).

Run from the FLMP root directory.
"""
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

results_dir = Path("../outputs/flmp_results/flmp_results_261010")
out_dir = Path(f"../outputs/flmp_outputs/{results_dir.name}")
year = 2021

input_data_dir = Path("input_data")
commodity_crosswalk = pd.read_csv(input_data_dir / "commodity_crosswalk.csv")
item_codes = pd.read_csv(input_data_dir / "SUA_Crops_Livestock_E_ItemCodes.csv")[[" Item Code", " Item"]].rename(columns={" Item Code": "Item_Code", " Item": "Item"})

df = pd.DataFrame()
for country_iso in os.listdir(f"{results_dir}/{year}"):
    if len(country_iso) != 3 or not os.path.exists(f"{results_dir}/{year}/{country_iso}/df_{country_iso.lower()}.csv"):
        continue
    print(country_iso)
    country_df = pd.read_csv(f"{results_dir}/{year}/{country_iso}/impacts_full.csv")[["Consumer_Country_Code", "Producer_Country_Code", "Animal_Product_Code", "ItemT_Code", "life_extinctions_per_sp_calc", "provenance_tonnes"]]

    primary = country_df.Animal_Product_Code.isna() | (country_df.Animal_Product_Code == "Primary")
    country_df["Effective_Producer_Code"] = country_df["Consumer_Country_Code"]
    country_df.loc[primary, "Effective_Producer_Code"] = country_df.loc[primary, "Producer_Country_Code"]
    country_df["TotalProduction"] = 0.0
    country_df.loc[primary, "TotalProduction"] = country_df.loc[primary, "provenance_tonnes"]
    country_df = country_df[["ItemT_Code", "life_extinctions_per_sp_calc", "TotalProduction", "Effective_Producer_Code"]]

    df = pd.concat([df, country_df], ignore_index=True)

df = df.groupby(["ItemT_Code", "Effective_Producer_Code"]).sum().reset_index()
df = df.merge(commodity_crosswalk[["Item_Code", "group_name_v6"]], left_on="ItemT_Code", right_on="Item_Code", how="left").drop(columns=["Item_Code"])
df = df.merge(item_codes, left_on="ItemT_Code", right_on="Item_Code", how="left").drop(columns=["Item_Code"])
df["Impact_per_kg"] = df["life_extinctions_per_sp_calc"] / (df["TotalProduction"] * 1000)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    area_codes = pd.read_excel(input_data_dir / "nocsDataExport_20251021-164754.xlsx", engine="openpyxl")
    area_codes = area_codes[["ISO3", "FAOSTAT"]].rename(columns={"ISO3": "Country", "FAOSTAT": "Effective_Producer_Code"})
df = df.merge(area_codes, on="Effective_Producer_Code", how="left")

# As in Fig1: keep only producers with positive production and positive impact
df = df[np.isfinite(df["Impact_per_kg"]) & (df["Impact_per_kg"] > 0)]


def summarise(g):
    w = g["TotalProduction"]
    v = g["Impact_per_kg"]
    q10, median, q90 = (np.percentile(a=v, q=q, weights=w, method="inverted_cdf") for q in (10, 50, 90))
    return pd.Series({
        "n_producers": len(g),
        "total_production_t": w.sum(),
        "total_life_extinctions": g["life_extinctions_per_sp_calc"].sum(),
        "weighted_mean_life_per_kg": np.average(v, weights=w),
        "weighted_median_life_per_kg": median,
        "weighted_q10_life_per_kg": q10,
        "weighted_q90_life_per_kg": q90,
    })


items_df = (df.groupby(["ItemT_Code", "Item", "group_name_v6"], dropna=False)
              .apply(summarise, include_groups=False)
              .reset_index()
              .sort_values("weighted_mean_life_per_kg", ascending=False))
groups_df = (df.dropna(subset=["group_name_v6"])
               .groupby("group_name_v6")
               .apply(summarise, include_groups=False)
               .reset_index()
               .sort_values("weighted_median_life_per_kg"))


out_dir.mkdir(parents=True, exist_ok=True)
items_df.to_csv(out_dir / f"global_life_per_kg_items_{year}.csv", index=False)
groups_df.to_csv(out_dir / f"global_life_per_kg_groups_{year}.csv", index=False)
print(f"Saved CSVs to {out_dir}")
print(groups_df.to_string())
