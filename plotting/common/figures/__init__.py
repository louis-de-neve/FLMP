"""
Metric-agnostic figure implementations.

Every module here exposes `main(metric, ...)` taking a
`plotting.common.metrics.Metric`; the scripts under `plotting/<metric>/` are
thin wrappers that pick a metric and call it.
"""
