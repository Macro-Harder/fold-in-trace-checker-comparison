# Trace Checker (free build)

A command line tool that mechanically checks a fold-in trace against its
target documents. For every element claim in the trace it prints one
verdict, LANDED, PARTIAL, CONTRADICTED, or MISSING, with a verbatim quote
from the target document as evidence where evidence exists, and it ends
with a full accounting in which every extracted element is counted.

Python standard library only. Fully offline.

## How to run

```
python3 trace_checker.py TRACE TARGET [TARGET ...]
```

Example, using the sample files in `examples/`:

```
python3 trace_checker.py examples/trace.md examples/alpha.md examples/beta.md
```

## Trace format

The trace is markdown. Each element is a heading block:

```
## E-101: Cache expiry rule
- Target: alpha.md
- Claim: "The cache expires after thirty minutes of inactivity."
```

- The heading's first word is the element ID; the rest is a title.
- `Target:` names the target document by file name. The tool matches it
  against the base name of the target files given on the command line.
- `Claim:` is the verbatim text the trace claims landed in the target.
  Surrounding quotes are optional. Keep the claim on one line.
- A heading block with a Target or Claim field counts as one extracted
  element. Sections with neither field are ignored.

## How verdicts are decided

Matching ignores whitespace differences: line breaks and extra spaces in
the target do not matter.

- LANDED: the full claim text is found in the named target. The evidence
  quote is the matching text copied from the target itself.
- PARTIAL: the full claim is not found, but at least one sentence-sized
  fragment of it is. The note states how many fragments were found.
- CONTRADICTED: no part of the claim is found, but the target has a line
  naming this element together with a word such as removed, superseded,
  rejected, or not landed. That line is quoted as evidence.
- MISSING: no part of the claim is found and there is no contradiction
  evidence.
- UNVERIFIABLE: the entry names a target document that was not supplied
  on the command line, so the claim cannot be checked. Counted separately
  in the accounting, with the reason.
- UNCHECKED: the entry carries no claim text, or no target name, so there
  is nothing to check. Counted separately, with the reason.

## Accounting and exit codes

The accounting lists the elements extracted, the count for each of the
four verdicts, the unverifiable and unchecked counts with their reasons
given per element in the verdict list, and a total that sums to the whole.

Exit codes:

- 0: no discrepancies, everything LANDED.
- 1: discrepancies found (any PARTIAL, CONTRADICTED, or MISSING).
- 2: usage error (bad arguments, trace file unreadable).
- 3: the trace could not be parsed (no entries found, or not text).
- 4: unverifiable or unchecked material is present.

When more than one applies, the highest severity wins: a run with both
discrepancies and unverifiable material exits 4.

Two runs over identical inputs produce identical reports apart from the
Run date and time line in the header.

## Potential problem causers

Known possible problems, stated plainly:

- Exact wording only. The tool checks text, not meaning. A claim that
  landed with different wording, however faithful, reads as PARTIAL or
  MISSING, and a claim can read LANDED while the surrounding text changes
  its meaning.
- PARTIAL is a rough measure. It counts sentence-sized fragments of the
  claim that appear anywhere in the target, in any order or context, so a
  scattered claim can look better landed than it is.
- CONTRADICTED rests on a short fixed word list (removed, superseded,
  rejected, and a few more) on a line that names the element ID. A
  contradiction written in other words is missed, and an innocent line
  that happens to pair the ID with one of those words can false-fire.
- One claim per entry, one line per claim. An entry with two claims, or
  a claim wrapped over two lines in the trace, is not read as intended:
  only the first Claim field is checked.
- Target matching is by file base name. Two supplied targets with the
  same base name collide; the second is ignored with a warning, and an
  entry naming the shared name is checked against the first file only.
- Evidence quotes are truncated for display at 160 characters, so a long
  landed passage is shown in part. The verdict itself is computed on the
  full text.
- The tool trusts the trace's own element IDs. Duplicate IDs, renamed
  elements, and claims filed under the wrong ID are checked as written
  and not detected.
- Exit code 4 covers two different things, unverifiable and unchecked
  material, which the accounting separates but the exit code does not.
