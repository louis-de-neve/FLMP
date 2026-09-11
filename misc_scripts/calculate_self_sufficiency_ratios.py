from pathlib import Path
import pandas as pd
from tqdm import tqdm

RESULTS_DIR = Path("/maps/tsb42/leakage_v1/results/mrio_pipeline_results_260713")

cdat = pd.read_excel("input_data/nocsDataExport_20251021-164754.xlsx")
countries = [_.upper() for _ in cdat["ISO3"].unique().tolist() if isinstance(_, str)]

# COUNTRIES = ["USA", "NLD", "GBR", "DEU", "FRA", "TZA"]
COUNTRIES = countries

YEARS = None
QUIET = True

def calculate_self_sufficiency_ratios(results_dir: Path, countries=None, years=None) -> pd.DataFrame:

    df = pd.DataFrame()

    year_dirs = sorted(results_dir.glob("*"))
    year_dirs = [d for d in year_dirs if "impacts" not in d.name and d.is_dir()]
    if years is not None:
        year_dirs = [d for d in year_dirs if d.name in years]

    year_c_dirs = []
    for year_dir in year_dirs:
        c_dirs = list(year_dir.glob("*"))
        c_dirs = [f for f in c_dirs if f.is_dir() and f.name != ".mrio"] #and f.name != "impacts"]
        if countries is not None:
            c_dirs = [f for f in c_dirs if f.name in countries]
        year_c_dirs.extend((year_dir, c_dir) for c_dir in c_dirs)

    pbar = tqdm(year_c_dirs)
    for year_dir, c_dir in pbar:
        c = c_dir.name
        year = year_dir.name
        pbar.set_description(f"Processing {c} in {year}")

        try:
            df_c = pd.read_csv(c_dir / f"df_{c.lower()}.csv")
            df_imported = pd.read_csv(c_dir / f"df_os.csv")
            df_full = pd.read_csv(c_dir / f"impacts_full.csv")

            domestic_no_feed = df_c.throughput_tonnes.sum()
            imported_no_feed = df_imported.throughput_tonnes.sum()

            domestic_full = df_full[df_full.Country_ISO == c.upper()].provenance_tonnes.sum()
            imported_full = df_full[df_full.Country_ISO != c.upper()].provenance_tonnes.sum()

            new_row = pd.DataFrame([{
                "country": c,
                "year": year,
                "domestic_tonnes_no_feed": domestic_no_feed,
                "imported_tonnes_no_feed": imported_no_feed,
                "ratio_no_feed": domestic_no_feed / (domestic_no_feed + imported_no_feed),
                "domestic_tonnes_full": domestic_full,
                "imported_tonnes_full": imported_full,
                "ratio_full": domestic_full / (domestic_full + imported_full)
            }])

            df = pd.concat([df, new_row], ignore_index=True)

        except Exception as e:
            if not QUIET:
                print(f"Error processing {c} in {year}: {e}")

    return df

if __name__ == "__main__":
    df = calculate_self_sufficiency_ratios(results_dir=RESULTS_DIR, years=YEARS, countries=COUNTRIES)
    Path(RESULTS_DIR / "ssr").mkdir(exist_ok=True)
    df.to_csv(RESULTS_DIR / "ssr" /  "self_sufficiency_ratios.csv", index=False)