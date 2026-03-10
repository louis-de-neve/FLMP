from __future__ import annotations

from pathlib import Path

import pandas as pd


def collate_fp_m2_kg(repo_root: Path) -> pd.DataFrame:
    results_dir = repo_root / "results"
    csv_paths = sorted(results_dir.glob("*/.mrio/Pasture_calc.csv"))

    if not csv_paths:
        raise FileNotFoundError(f"No Pasture_calc.csv files found under: {results_dir}")

    by_year: dict[str, pd.Series] = {}

    for csv_path in csv_paths:
        year = csv_path.parents[1].name  # results/<year>/.mrio/Pasture_calc.csv
        df = pd.read_csv(csv_path, usecols=["Country_ISO", "fp_m2_kg"])

        df["Country_ISO"] = df["Country_ISO"].astype(str).str.strip()
        df["fp_m2_kg"] = pd.to_numeric(df["fp_m2_kg"], errors="coerce")

        df = df[df["Country_ISO"].notna() & (df["Country_ISO"] != "")]
        df = df.dropna(subset=["fp_m2_kg"])

        # Multiple rows per country can exist; aggregate to one value per country/year.
        by_year[year] = df.groupby("Country_ISO", sort=True)["fp_m2_kg"].sum()

    out = pd.DataFrame(by_year)
    out = out.sort_index()

    # Sort columns numerically when possible.
    out = out.reindex(sorted(out.columns, key=lambda y: int(y) if str(y).isdigit() else str(y)), axis=1)
    out.index.name = "Country_ISO"

    return out


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    output_path = "pasture_fp_m2_kg_by_country_year.csv"

    collated = collate_fp_m2_kg(repo_root)
    collated.to_csv(output_path)

    print(f"Wrote: {output_path}")


if __name__ == "__main__":
    main()