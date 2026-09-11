"""
Argument parsing shared by the per-metric runner scripts.

Every runner accepts the same core options - which results directory to read,
which year(s), whether to pop the figure up - so they are defined once here.
A runner stays a handful of lines: pick a metric, call a figure.
"""

import argparse
from pathlib import Path

from . import metrics as metrics_module
from . import paths
from .metrics import Metric

DEFAULT_COUNTRIES = ["GBR", "POL", "CHN", "IND", "RWA", "USA"]


def _base_parser(metric: Metric, description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"{description}\n\nMetric: {metric.name} ({metric.key})",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=paths.RESULTS_DIR,
        help="Pipeline results directory (default: %(default)s)",
    )
    parser.add_argument("--show", action="store_true", help="Display the figure as well as saving it")
    return parser


def run_single_year(figure_main, metric: Metric, description: str = "", **defaults):
    """Run a figure that reads one year."""
    parser = _base_parser(metric, description or figure_main.__module__)
    parser.add_argument("--year", type=int, default=defaults.get("year", 2021))
    args = parser.parse_args()
    return figure_main(metric, year=args.year, results_dir=args.results_dir, show=args.show)


def run_time_series(figure_main, metric: Metric, description: str = "", **defaults):
    """Run a figure that reads every year available, for a set of countries."""
    parser = _base_parser(metric, description or figure_main.__module__)
    parser.add_argument(
        "--countries",
        nargs="+",
        default=defaults.get("countries", DEFAULT_COUNTRIES),
        help="ISO3 codes to plot (default: %(default)s)",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=None,
        help="Years to include (default: every year present in the results directory)",
    )
    if defaults.get("relative_option"):
        parser.add_argument(
            "--relative",
            action="store_true",
            help="Plot each group as a share of the country total rather than an absolute value",
        )
    args = parser.parse_args()

    kwargs = dict(
        countries=args.countries,
        years=args.years,
        results_dir=args.results_dir,
        show=args.show,
    )
    if defaults.get("relative_option"):
        kwargs["relative"] = args.relative
    return figure_main(metric, **kwargs)


def run_one_country(figure_main, metric: Metric, description: str = "", **defaults):
    """Run a figure that traces a single country through time."""
    parser = _base_parser(metric, description or figure_main.__module__)
    parser.add_argument("--country", default=defaults.get("country", "GBR"), help="ISO3 code")
    parser.add_argument("--years", nargs="+", type=int, default=None)
    args = parser.parse_args()
    return figure_main(
        metric,
        country=args.country,
        years=args.years,
        results_dir=args.results_dir,
        show=args.show,
    )


def run_diet_scenarios(figure_main, metric: Metric, description: str = "", **defaults):
    """Run the diet-scenario figure for one country-year.

    `extra_metrics` in defaults stacks further metrics into each bar; when set,
    --both writes the fine-grouped and coarse animal/vegetal figures in one go.
    """
    extra_metrics = tuple(defaults.get("extra_metrics", ()))

    parser = _base_parser(metric, description or figure_main.__module__)
    parser.add_argument("--country", default=defaults.get("country", "GBR"), help="ISO3 code")
    parser.add_argument("--year", type=int, default=defaults.get("year", 2021))
    parser.add_argument(
        "--skip",
        nargs="*",
        default=list(defaults.get("skip", ("EAT-Lancet",))),
        help="Diet scenarios to leave out (default: %(default)s)",
    )
    parser.add_argument(
        "--population",
        type=float,
        default=None,
        help="Override the population used to get a per-capita figure "
        "(default: the FAOSTAT series for that country and year)",
    )
    grouping = parser.add_mutually_exclusive_group()
    grouping.add_argument(
        "--coarse",
        action="store_true",
        help="Collapse commodity groups to animal vs vegetal products",
    )
    grouping.add_argument(
        "--both",
        action="store_true",
        help="Write both the full-grouping and the coarse animal/vegetal figure",
    )
    if any(m.amortized for m in (metric, *extra_metrics)):
        parser.add_argument(
            "--amortization-years",
            type=int,
            default=metrics_module.AMORTIZATION_YEARS,
            help="Production lifetime the one-off carbon cost is spread over "
            "(default: %(default)s, matching main.py)",
        )
    args = parser.parse_args()

    kwargs = dict(
        extra_metrics=extra_metrics,
        country=args.country,
        year=args.year,
        skip=tuple(args.skip),
        population=args.population,
        results_dir=args.results_dir,
        show=args.show,
    )
    if hasattr(args, "amortization_years"):
        kwargs["amortization_years"] = args.amortization_years

    if args.both:
        return [figure_main(metric, coarse=c, **kwargs) for c in (False, True)]
    return figure_main(metric, coarse=args.coarse, **kwargs)


def run_two_year(figure_main, metric: Metric, description: str = "", **defaults):
    """Run a figure that compares two years side by side."""
    parser = _base_parser(metric, description or figure_main.__module__)
    parser.add_argument(
        "--years",
        nargs=2,
        type=int,
        default=defaults.get("years", [2010, 2021]),
        metavar=("EARLY", "LATE"),
    )
    if defaults.get("country_option"):
        parser.add_argument(
            "--country",
            default=defaults.get("country"),
            help="ISO3 code, or omit for the world aggregate",
        )
    args = parser.parse_args()

    kwargs = dict(years=tuple(args.years), results_dir=args.results_dir, show=args.show)
    if defaults.get("country_option"):
        kwargs["country"] = args.country
    return figure_main(metric, **kwargs)
