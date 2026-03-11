from __future__ import annotations

from pathlib import Path

import pandas as pd


def collate_fp_m2_kg(repo_root: Path) -> pd.DataFrame:
    results_dir = repo_root / "results"
    csv_paths = sorted(results_dir.glob("*/.mrio/Pasture_calc.csv"))

    if not csv_paths:
        raise FileNotFoundError(f"No Pasture_calc.csv files found under: {results_dir}")
    pasture_items = [867, 882, 947, 951, 977, 982, 1017, 1020, 1097]
    pasture_item_strings = ["Cow_Meat", "Cow_Milk", "Buffalo_Meat", "Buffalo_Milk", "Sheep_Meat", "Sheep_Milk", "Goat_Meat", "Goat_Milk", "Horse_Meat"]
    for i, item in enumerate(pasture_items):
        by_year: dict[str, pd.Series] = {}

        for csv_path in csv_paths:
            year = csv_path.parents[1].name  # results/<year>/.mrio/Pasture_calc.csv
            df = pd.read_csv(csv_path, usecols=["Country_ISO", "fp_m2_kg", "Item_Code"])

            df["Country_ISO"] = df["Country_ISO"].astype(str).str.strip()
            df["fp_m2_kg"] = pd.to_numeric(df["fp_m2_kg"], errors="coerce")

            df = df[df["Country_ISO"].notna() & (df["Country_ISO"] != "")]
            df = df.dropna(subset=["fp_m2_kg"])

            # Multiple rows per country can exist; aggregate to one value per country/year.
            by_year[year] = df[df["Item_Code"]==item].groupby("Country_ISO")["fp_m2_kg"].sum()
            by_year[year] = 1/by_year[year]  # convert from m2/kg to kg/m2

        out = pd.DataFrame(by_year)
        out = out.sort_index()

        # Sort columns numerically when possible.
        out = out.reindex(sorted(out.columns, key=lambda y: int(y) if str(y).isdigit() else str(y)), axis=1)
        out.index.name = "Country_ISO"
        output_path = f"pasture_yields/pasture_fp_kg_m2_by_country_year_{pasture_item_strings[i]}.csv"
        out.to_csv(output_path)


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    collate_fp_m2_kg(repo_root)




if __name__ == "__main__":
    main()