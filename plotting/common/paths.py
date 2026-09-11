"""
Filesystem locations for the plotting scripts.

The old scripts each hardcoded their own relative paths ("../results/",
"../../../results/...", "input_data/") which meant they only ran from one
particular working directory - and, in several cases, from no working directory
at all, because a single script mixed "input_data" with "../outputs". Everything
here is anchored to the repository root instead, so a script works no matter
where it is invoked from.

Override the results directory without editing code:

    FLMP_RESULTS_DIR=/path/to/flmp_results_261010 python plotting/ghgs/per_kg_distribution.py
"""

import os
from pathlib import Path

# plotting/common/paths.py -> plotting/common -> plotting -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]

INPUT_DATA_DIR = REPO_ROOT / "input_data"

# main.py writes results outside the repo, alongside it. Keep that convention.
_DEFAULT_RESULTS_DIR = REPO_ROOT.parent / "flmp_results" / "flmp_results_261009"

RESULTS_DIR = Path(os.environ.get("FLMP_RESULTS_DIR", _DEFAULT_RESULTS_DIR))

OUTPUTS_DIR = Path(os.environ.get("FLMP_OUTPUTS_DIR", REPO_ROOT.parent / "flmp_outputs"))

# Files under input_data/ that more than one plotting script needs.
AREA_CODES_FILE = INPUT_DATA_DIR / "nocsDataExport_20251021-164754.xlsx"
COMMODITY_CROSSWALK_FILE = INPUT_DATA_DIR / "commodity_crosswalk.csv"
REGIONS_FILE = INPUT_DATA_DIR / "regions.csv"
SUA_DATA_FILE = INPUT_DATA_DIR / "SUA_Crops_Livestock_E_All_Data_(Normalized).csv"
ITEM_CODES_FILE = INPUT_DATA_DIR / "SUA_Crops_Livestock_E_ItemCodes.csv"

GROUPING = "group_name_v6"

# Diet scenario definitions, moved here from misc_scripts/.
DIETS_DIR = REPO_ROOT / "plotting" / "diets" / "data"


def mapspam_results_file(spam_year: int = 2020) -> Path:
    """Processed MAPSPAM/LIFE results, which carry the assessed species count."""
    return (
        INPUT_DATA_DIR
        / "mapspam_outputs"
        / "outputs"
        / str(spam_year)
        / f"processed_results_{spam_year}.csv"
    )


def year_dir(year: int, results_dir: Path | None = None) -> Path:
    return (results_dir or RESULTS_DIR) / str(year)


def country_dir(year: int, iso3: str, results_dir: Path | None = None) -> Path:
    return year_dir(year, results_dir) / iso3.upper()


def available_years(results_dir: Path | None = None) -> list[int]:
    """Years that actually have results on disk, ascending.

    The results root also holds non-year directories ("impacts",
    "impacts_matrices"), so select on the name being a 4-digit number rather
    than on it merely being a directory.
    """
    root = results_dir or RESULTS_DIR
    if not root.is_dir():
        raise FileNotFoundError(
            f"Results directory not found: {root}\n"
            f"Set FLMP_RESULTS_DIR to point at a populated results directory."
        )
    return sorted(int(p.name) for p in root.iterdir() if p.is_dir() and p.name.isdigit())


def available_countries(year: int, results_dir: Path | None = None) -> list[str]:
    """ISO3 codes with an impacts_aggregated.csv for `year`, ascending."""
    ydir = year_dir(year, results_dir)
    if not ydir.is_dir():
        raise FileNotFoundError(f"No results for year {year} under {ydir.parent}")
    return sorted(
        p.name
        for p in ydir.iterdir()
        if p.is_dir() and len(p.name) == 3 and (p / "impacts_aggregated.csv").exists()
    )


def output_path(*parts: str, results_dir: Path | None = None) -> Path:
    """Path under the outputs dir, namespaced by which results produced it.

    Keeping the results-directory name in the path means figures from two
    different pipeline runs do not silently overwrite each other.
    """
    root = results_dir or RESULTS_DIR
    path = OUTPUTS_DIR / root.name / Path(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
