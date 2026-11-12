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

- 5,043 lines of product code and 7,001 lines of tests.
- Final test suite of 443 tests, with 443 passing, run from a clean copy at the release gate.
- It reads the real trace grammar. At its live proof it checked the real 169 row Step 9 trace.
