# Comparison: one specification, two builds

The same product specification was built twice.

The first build is the one in this repository. It was written by a single agent working from the specification alone, with no process rules.

The second build was made under a 23 step build flow, with audits and tests first. It lives in the fold-in-trace-checker repository: https://github.com/Macro-Harder/fold-in-trace-checker

## The free build, measured

- One file of code, trace_checker.py, with 285 lines.
- Seven files in its own tree: the tool, its README, and five example files.
- Built in about two minutes.
- It invents its own trace format, so it cannot read the real traces the programme writes.
- It has no table handling, no count checking, and no duplicate detection.

## The flow build, measured

Measured on the finished tree on 2026-11-12, after the build completed. An earlier version of this page carried mid-build figures; they were corrected on the same day.

- 5,366 lines of product code in its single product file, and 8,595 lines of tests in the test suite files, 11,622 lines under tests/ in total with fixtures included.
- Final test suite of 443 tests, with 443 passing, run from a clean copy at the release gate.
- It reads the real trace grammar. At its live proof it checked the real 169 row Step 9 trace.
