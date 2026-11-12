# Fold-in trace checker: the comparison

This repository holds the free build of a fold-in trace checker, together with a measured comparison against the same specification built under a full build flow.

What is in it:

- trace_checker.py, the free build itself: one file, 285 lines, written by a single agent from the product specification alone, with no process rules. Sample files sit under examples/.
- COMPARISON.md, which sets out what the two builds are and how they measured up.
- LICENSE, Apache 2.0.

The flow built version is here: https://github.com/Macro-Harder/fold-in-trace-checker

To run the free build: python3 trace_checker.py TRACE TARGET [TARGET ...]

The free build's own README, written alongside the tool, arrived with the free build files and is preserved in this repository's history, in the commit that added them.
