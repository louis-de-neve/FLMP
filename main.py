#!/usr/bin/env python3
"""
This code is a translation/re-written python script of the original R code of the following publication:
Schwarzmueller, F. & Kastner, T (2022), Agricultural trade and its impact on cropland use
and the global loss of species' habitats. Sustainability Science, doi: 10.1007/s11625-022-01138-7
(c) Florian Schwarzmueller, December 2021

It is then combined with the food_LIFE codebase for impact assessment:
Ball, T.S., Dales, M., Eyres, A. et al. Food impacts on species extinction risks can vary by three orders of magnitude.
Nat Food 6, 848–856 (2025). doi: 10.1038/s43016-025-01224-w

Please cite ;-)

This script was written in Python, October 2025 by Louis De Neve

Added multiprocessing (country-level parallelism), October/December 2025 by Thomas Ball
"""

import os
from pathlib import Path
import time

import multiprocessing

from rich.console import Group
from rich.live import Live
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table

from processing.unzip_data import unzip_data
from processing.calculate_trade_matrix import calculate_trade_matrix
from processing.calculate_error_matrix import calculate_error_matrix
from processing.animal_products_to_feed import animal_products_to_feed

from provenance._get_biodiversity_vals import fetch_biodiversity_vals_path
from provenance._provenance import main as consumption_provenance_main
from provenance._get_impacts_bd import get_impacts as get_impacts_main
from provenance._process_dat import main as process_dat_main
from provenance._process_dat import main_global as process_dat_main_global

from pandas import read_excel, read_csv

# CONFIG
RESULTS_DIR = "../results/mrio_pipeline_results_260826_spam2020" # set this to any dir of your choosing
ERROR_ITERATIONS = 1000
# YEARS = list(range(2022, 2022))
YEARS = [2021]

# Multiprocessing settings
N_PROCESSES = 16

# Overwrite stuff?
OVERWRITE = True

# Defaults to all countries if this is None, otherwise specific a list of your favourite country iso3 codes e.g. ["USA", "IND", "BRA", "JPN", "UGA", "GBR"]
# COUNTRIES = ["USA", "IND", "BRA", "JPN", "UGA", "GBR"]
COUNTRIES = None

# Pipeline components to run
# 0 = all, 1 = unzip, 2 = error matrix, 3 = trade matrix, 4 = animal products to feed, 5 = country impacts
PIPELINE_COMPONENTS: list = [0]  # default to all, but can be overridden by command line args


# Select a conversion method
CONVERSION_OPTION = "dry_matter" # you probably shouldn't change this unless you're doing something crazy

# Prefer import or export data
PREFER_IMPORT = "import" # you also probably shouldn't change this unless you're doing something crazy

# select working directory
WORKING_DIR = '.'

# Setting this to False reverts to using the 2010 mapspam data for all years beyond 2010 
# (because the 2020 data is suspicious, speak to Tom for details. Even better speak to
# someone who knows what they're talking about)
USE_2020_DATA = True # have updated to use most recent mapspam - UK/Ghana/USA issues
# fixed though it seems some issues persist.

# Carbon opportunity cost (COC) is a one-off cost of converting land, but production
# continues indefinitely; this spreads (amortizes) that fixed cost across an assumed
# production lifetime to get an annualized per-year impact: annual_impact = COC / AMORTIZATION_YEARS.
# 30 years is the value used for the "expansion COC" in Wirsenius 2025 (https://www.researchsquare.com/article/rs-6678069/v1)
AMORTIZATION_YEARS = 30

# Which band of the biodiversity opportunity cost (mapspam_outputs) data to use.
# Available bands: "all", "AMPHIBIA", "AVES", "MAMMALIA", "REPTILIA". Generally use 'all'. 
BD_BAND_NAME = "all"

# Which band of the carbon opportunity cost (coc_outputs) data to use.
# Available bands: "agri_potential_carbon".
COC_BAND_NAME = "agri_potential_carbon"

cdat = read_excel("input_data/nocsDataExport_20251021-164754.xlsx")
COUNTRIES = [_.upper() for _ in cdat["ISO3"].unique().tolist() if isinstance(_, str)] if COUNTRIES is None else COUNTRIES

def _process_year_matrices(year: int, hist: str, conversion_option: str, prefer_import: str, results_dir: Path,
                            error_data, overwrite=True, status=None, completed=None, lock=None):
    """
    Runs the per-year, all-countries-at-once steps (trade matrix + animal-to-feed
    conversion + biodiversity value fetch). Independent across years, so callers
    can run this over a pool spanning all years.

    When `status`/`completed`/`lock` (shared multiprocessing.Manager objects) are
    given, progress is reported into them for the live dashboard instead of via
    plain prints.
    """
    pid = os.getpid()
    desc = f"year {year}"
    marker_file = results_dir / str(year) / ".mrio" / f"TradeMatrixFeed_{prefer_import}_{conversion_option}.csv"
    if status is None:
        print(f"    [PID {pid}] Computing trade matrix for year {year}")
    else:
        status[pid] = {"task": desc, "start": time.perf_counter()}
    t0 = time.perf_counter()
    try:
        if not overwrite and marker_file.exists():
            t1 = time.perf_counter()
            if status is None:
                print(f"    [PID {pid}] Skipping year {year} (already computed)")
            else:
                status[pid] = {"task": f"{desc} skipped (exists)", "start": t1}
            return (year, None)
        calculate_trade_matrix(
            conversion_opt=conversion_option,
            prefer_import=prefer_import,
            year=year,
            historic=hist,
            results_dir=results_dir,
            all_error_data=error_data)
        animal_products_to_feed(
            prefer_import=prefer_import,
            conversion_opt=conversion_option,
            year=year,
            historic=hist,
            results_dir=results_dir)
        fetch_biodiversity_vals_path(year, "./input_data", USE_2020_DATA)
        t1 = time.perf_counter()
        if status is None:
            print(f"    [PID {pid}] Completed matrices for year {year} in {t1 - t0:.2f} seconds")
        else:
            status[pid] = {"task": f"{desc} ✓ done ({t1 - t0:.1f}s)", "start": t1}
        return (year, None)
    except Exception as e:
        if status is None:
            print(f"    [PID {pid}] Error computing matrices for year {year}: {e}")
        else:
            status[pid] = {"task": f"[red]{desc} ERROR: {e}[/red]", "start": time.perf_counter()}
        return (year, str(e))
    finally:
        if completed is not None:
            with lock:
                completed.value += 1


def _process_country(country: str, year: int, hist: str, results_dir: Path, overwrite=True,
                      amortization_years=30, bd_band_name="all", coc_band_name="agri_potential_carbon",
                      status=None, completed=None, lock=None):
    """
    Runs consumption/feed provenance + biodiversity impact assignment for a
    single (country, year). Independent across (country, year), so callers can
    run this over a pool spanning all countries and years.

    When `status`/`completed`/`lock` (shared multiprocessing.Manager objects) are
    given, progress is reported into them for the live dashboard instead of via
    plain prints.
    """
    pid = os.getpid()
    desc = f"{country} / {year}"
    missing_items_local = []
    marker_file = results_dir / str(year) / country / "food_commodity_impacts.csv"
    if status is None:
        print(f"    [PID {pid}] Processing country: {country}")
    else:
        status[pid] = {"task": desc, "start": time.perf_counter()}
    t0 = time.perf_counter()
    try:
        if not overwrite and marker_file.exists():
            t1 = time.perf_counter()
            if status is None:
                print(f"    [PID {pid}] Skipping {country} / {year} (already computed)")
            else:
                status[pid] = {"task": f"{desc} skipped (exists)", "start": t1}
            return []
        # consumption_provenance_main returns (cons, feed) per original script
        cons, feed = consumption_provenance_main(year, country, hist, results_dir=results_dir)
        if len(cons) == 0:
            if status is None:
                print(f"    [PID {pid}] No consumption data for {country} in {year}")
            else:
                status[pid] = {"task": f"{desc}: no consumption data", "start": time.perf_counter()}
            return []  # nothing to do for this country
        bf = get_impacts_main(feed, year, country, "feed_impacts_wErr.csv", results_dir=results_dir, use_2020=USE_2020_DATA,
                               bd_band_name=bd_band_name, coc_band_name=coc_band_name)
        bh = get_impacts_main(cons, year, country, "human_consumed_impacts_wErr.csv", results_dir=results_dir, use_2020=USE_2020_DATA,
                               bd_band_name=bd_band_name, coc_band_name=coc_band_name)
        if country == "WORLD":
            mi = process_dat_main_global(year, "WORLD", bh, bf, results_dir=results_dir, amortization_years=amortization_years)
        else:
            mi = process_dat_main(year, country, bh, bf, results_dir=results_dir, amortization_years=amortization_years)
        missing_items_local.extend(mi)
        t1 = time.perf_counter()
        if status is None:
            print(f"    [PID {pid}] Completed {country} in {t1 - t0:.2f} seconds")
        else:
            status[pid] = {"task": f"{desc} ✓ done ({t1 - t0:.1f}s)", "start": t1}
        return missing_items_local
    except Exception as e:
        # Print error and continue; return empty list so caller can continue aggregating
        if status is None:
            print(f"    [PID {pid}] Error processing {country} for {year}: {e}")
        else:
            status[pid] = {"task": f"[red]{desc} ERROR: {e}[/red]", "start": time.perf_counter()}
        return []
    finally:
        if completed is not None:
            with lock:
                completed.value += 1

def _render_dashboard(status, completed, total, processes, label):
    now = time.perf_counter()
    table = Table(title=f"Active workers (up to {processes})")
    table.add_column("PID", justify="right")
    table.add_column("Current task")
    table.add_column("Elapsed (s)", justify="right")
    for pid, info in sorted(status.items()):
        table.add_row(str(pid), info["task"], f"{now - info['start']:.1f}")
    return table


def _run_pool_with_dashboard(processes: int, worker_func, args_iterable: list, label: str):
    """
    Runs `worker_func` over `args_iterable` on a Pool of `processes` workers,
    rendering a live table of per-worker status plus an overall progress bar.
    `worker_func` must accept trailing (status, completed, lock) args, as
    `_process_year_matrices`/`_process_country` do.
    """
    total = len(args_iterable)
    with multiprocessing.Manager() as manager:
        status = manager.dict()
        completed = manager.Value("i", 0)
        lock = manager.Lock()
        full_args = [tuple(args) + (status, completed, lock) for args in args_iterable]

        progress = Progress(
            TextColumn("[bold]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        )
        progress_task = progress.add_task(label, total=total)

        with multiprocessing.Pool(processes=processes) as pool:
            async_result = pool.starmap_async(worker_func, full_args)
            with Live(refresh_per_second=4) as live:
                while not async_result.ready():
                    progress.update(progress_task, completed=completed.value)
                    live.update(Group(_render_dashboard(status, completed, total, processes, label), progress))
                    time.sleep(0.25)
                progress.update(progress_task, completed=completed.value)
                live.update(Group(_render_dashboard(status, completed, total, processes, label), progress))
            results = async_result.get()
    return results


def main(years=list(range(1986, 2022)),
         conversion_option="dry_matter",
         prefer_import="import",
         pipeline_components=[0],
         working_dir=".",
         countries=None,
         results_dir="./results",
         n_processes=None,
         overwrite=True,
         amortization_years=30,
         bd_band_name="all",
         coc_band_name="agri_potential_carbon"):

    if countries is None:
        countries = COUNTRIES

    # os.system('cls' if os.name == 'nt' else 'clear')
    os.chdir(working_dir)

    component_dict = {
        0: "Full pipeline",
        1: "Unzipping data",
        2: "Error matrix calculation",
        3: "Trade matrix calculation",
        4: "Animal products to feed calculation",
        5: "Country-level provenance calculations",
    }

    print(f"""\nStarting MRIO calculations with options:
    Working directory: {working_dir}
    Using {conversion_option} as the conversion option
    Preferring {prefer_import} data
    Running pipeline component {[p for p in pipeline_components]}: {[component_dict[p] for p in pipeline_components]}

    Years to process: {years}
    """)

    # check results dir
    results_dir = Path(results_dir)
    results_dir.mkdir(exist_ok=True)

    if (0 in pipeline_components) or (1 in pipeline_components):
        print("Unzipping data...")
        try:
            unzip_data("./input_data") 
            print("Data already unzipped or unzipping completed successfully.")
        except Exception as e:
            print(f"Error during data unzipping: {e}")

    if pipeline_components == [1]:
        return
    
    if (0 in pipeline_components) or (2 in pipeline_components):
        error_data = calculate_error_matrix(
            conversion_opt=conversion_option,
            prefer_import=prefer_import,
            historic="",
            iterations=ERROR_ITERATIONS)
    else:
        error_data = None

    if n_processes is None:
        try:
            n_processes = max(1, multiprocessing.cpu_count() - 1)
        except Exception:
            n_processes = 1

    # Phase 0: directory setup + per-year historic flag, cheap and sequential
    year_hist = {}
    for year in years:
        year_dir = results_dir / str(year)
        year_dir.mkdir(exist_ok=True)
        mrio_dir = results_dir / str(year) / ".mrio"
        mrio_dir.mkdir(exist_ok=True)
        for country in countries:
            country_dir = results_dir / str(year) / country
            country_dir.mkdir(exist_ok=True)
        year_hist[year] = "Historic" if year < 2010 else ""

    # Phase 1: trade matrix + animal-to-feed conversion, parallel across years
    if (0 in pipeline_components) or (3 in pipeline_components) or (4 in pipeline_components):
        processes = min(n_processes, len(years))
        print(f"\nComputing trade matrices for {len(years)} years using up to {processes} worker processes")
        args_iterable = [(y, year_hist[y], conversion_option, prefer_import, results_dir, error_data, overwrite) for y in years]
        if processes == 1:
            results = [_process_year_matrices(*args) for args in args_iterable]
        else:
            results = _run_pool_with_dashboard(
                processes, _process_year_matrices, args_iterable,
                label=f"Trade matrices ({len(years)} years)")
        for y, err in results:
            if err:
                print(f"Error computing matrices for year {y}: {err}")

    # Phase 2: country-level provenance and impacts, parallel across (year, country)
    if (0 in pipeline_components) or (5 in pipeline_components):
        print("\nProcessing country-level provenance and impacts...")
        tasks = [(country, year, year_hist[year], results_dir, overwrite, amortization_years, bd_band_name, coc_band_name) for year in years for country in countries]

        if n_processes == 1:
            results = [_process_country(*task) for task in tasks]
        else:
            processes = min(n_processes, len(tasks))
            print(f"    Spawning {processes} worker processes for {len(tasks)} (year, country) tasks")
            results = _run_pool_with_dashboard(
                processes, _process_country, tasks,
                label=f"Country/year provenance ({len(tasks)} tasks)")

        missing_by_year = {year: [] for year in years}
        for (country, year, hist, _rd, _ow, _am, _bd, _coc), res in zip(tasks, results):
            if res:
                missing_by_year[year].extend(res)

        for year in years:
            missing_items_file = results_dir / str(year) / "missing_items.txt"
            with open(missing_items_file, "w") as f:
                f.write("Items missing from crosswalk and their codes:\n")
                for item, code in set(missing_by_year[year]):
                    f.write(f" - {item}: {code}\n")

    print("\nAll years processed successfully\n")

if __name__ == "__main__":

    main(
        years=YEARS,
        conversion_option=CONVERSION_OPTION,
        prefer_import=PREFER_IMPORT,
        pipeline_components=PIPELINE_COMPONENTS,
        working_dir=WORKING_DIR,
        results_dir=RESULTS_DIR,
        countries=COUNTRIES,
        n_processes=N_PROCESSES,
        overwrite=OVERWRITE,
        amortization_years=AMORTIZATION_YEARS,
        bd_band_name=BD_BAND_NAME,
        coc_band_name=COC_BAND_NAME,
    )