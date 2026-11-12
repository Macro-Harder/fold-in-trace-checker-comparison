#!/usr/bin/env python3
"""trace_checker: mechanically check a fold-in trace against its target documents.

Reads a markdown trace whose entries claim that design elements landed in
named target documents, checks every claim against the actual target text,
and prints one verdict per element plus a full accounting.

Verdicts: LANDED, PARTIAL, CONTRADICTED, MISSING. Material that cannot be
checked is reported as UNVERIFIABLE (target unavailable) or UNCHECKED
(entry carries nothing checkable), always with the reason named.

Exit codes: 0 no discrepancies; 1 discrepancies found; 2 usage error;
3 trace input could not be parsed; 4 unverifiable or unchecked material
present. When several apply, the highest severity wins (4 > 3 > 2 > 1 > 0;
in practice 3 and 2 end the run before any checking happens).

Python standard library only. Fully offline. Deterministic apart from the
run date and time printed in the header.
"""

import argparse
import re
import sys
from datetime import datetime

VERDICTS = ("LANDED", "PARTIAL", "CONTRADICTED", "MISSING")

# Words that, on a target line naming the element, mark the landing as
# contradicted by the target document itself.
NEGATION_MARKERS = (
    "removed", "superseded", "rejected", "deleted", "withdrawn",
    "not landed", "never landed", "dropped", "reverted", "struck",
)

HEADING_RE = re.compile(r"^(#{1,6})\s+(\S+)\s*(.*)$")
FIELD_RE = re.compile(r"^\s*(?:[-*]\s*)?(Target|Claim)\s*:\s*(.*)$", re.IGNORECASE)

MIN_FRAGMENT = 12  # shortest claim fragment that can support a PARTIAL


def normalize(text):
    """Collapse all whitespace runs to single spaces and strip the ends.

    Returns (normalized_text, index_map) where index_map[i] is the offset
    in the original text of normalized character i, so a match found in
    normalized space can be quoted verbatim from the original.
    """
    out = []
    index_map = []
    pending_space = False
    for i, ch in enumerate(text):
        if ch.isspace():
            pending_space = True
            continue
        if pending_space and out:
            out.append(" ")
            index_map.append(i - 1)  # the whitespace char before this one
        pending_space = False
        out.append(ch)
        index_map.append(i)
    return "".join(out), index_map


def original_span(index_map, original, start, end):
    """Map a normalized [start, end) span back to the original text."""
    if start >= len(index_map):
        return ""
    lo = index_map[start]
    hi = index_map[end - 1] + 1 if end - 1 < len(index_map) else len(original)
    return original[lo:hi]


def one_line(text, limit=160):
    """Flatten a quote to a single display line, truncated with a marker."""
    flat = " ".join(text.split())
    if len(flat) > limit:
        return flat[: limit - 3] + "..."
    return flat


class Entry:
    def __init__(self, element_id, title, line_no):
        self.element_id = element_id
        self.title = title
        self.line_no = line_no
        self.target = None
        self.claim = None


def parse_trace(text):
    """Extract element entries from a trace.

    An entry is a heading block whose body carries a Target: and/or Claim:
    field. Heading blocks with neither field are ordinary sections and are
    not elements. Returns a list of Entry in file order.
    """
    entries = []
    current = None

    def flush():
        nonlocal current
        if current is not None and (current.target is not None or current.claim is not None):
            entries.append(current)
        current = None

    for line_no, line in enumerate(text.splitlines(), start=1):
        m = HEADING_RE.match(line)
        if m:
            flush()
            element_id = m.group(2).rstrip(":")
            title = (m.group(3) or "").strip()
            if title[:1] in (":", "-"):
                title = title[1:].strip()
            current = Entry(element_id, title, line_no)
            continue
        if current is not None:
            f = FIELD_RE.match(line)
            if f:
                name, value = f.group(1).lower(), f.group(2).strip()
                if name == "target" and current.target is None:
                    current.target = value.strip("`").strip()
                elif name == "claim" and current.claim is None:
                    current.claim = value
    flush()
    return entries


def split_fragments(claim_norm):
    """Split a normalized claim into sentence-sized fragments."""
    parts = re.split(r"(?<=[.!?])\s+", claim_norm)
    return [p for p in (p.strip() for p in parts) if len(p) >= MIN_FRAGMENT]


def check_entry(entry, targets):
    """Return (verdict, evidence_quote_or_None, reason_or_None).

    verdict is one of VERDICTS, or UNVERIFIABLE / UNCHECKED with a reason.
    targets maps basename -> (original_text, normalized_text, index_map).
    """
    if entry.claim is None or not entry.claim.strip():
        return ("UNCHECKED", None, "entry names no claim text to check")
    if entry.target is None or not entry.target.strip():
        return ("UNCHECKED", None, "entry names no target document")

    claim = entry.claim.strip()
    if len(claim) >= 2 and claim[0] == claim[-1] and claim[0] in "\"'":
        claim = claim[1:-1].strip()

    base = entry.target.replace("\\", "/").rsplit("/", 1)[-1]
    if base not in targets:
        return ("UNVERIFIABLE", None,
                "target document not supplied: %s" % entry.target)

    original, target_norm, index_map = targets[base]
    claim_norm, _ = normalize(claim)

    pos = target_norm.find(claim_norm)
    if pos >= 0:
        quote = original_span(index_map, original, pos, pos + len(claim_norm))
        return ("LANDED", quote, None)

    fragments = split_fragments(claim_norm)
    found = []
    for frag in fragments:
        p = target_norm.find(frag)
        if p >= 0:
            found.append((frag, p))
    if found and len(fragments) > 1:
        frag, p = found[0]
        quote = original_span(index_map, original, p, p + len(frag))
        return ("PARTIAL", quote,
                "%d of %d claim fragments found" % (len(found), len(fragments)))
    if found and len(fragments) == 1 and len(fragments[0]) < len(claim_norm):
        frag, p = found[0]
        quote = original_span(index_map, original, p, p + len(frag))
        return ("PARTIAL", quote, "only part of the claim text found")

    # No part of the claim found. The target may still contradict it:
    # a line naming this element together with a negation marker.
    id_pattern = re.compile(re.escape(entry.element_id), re.IGNORECASE)
    for line in original.splitlines():
        if id_pattern.search(line):
            lowered = line.lower()
            if any(marker in lowered for marker in NEGATION_MARKERS):
                return ("CONTRADICTED", line.strip(), None)

    return ("MISSING", None, None)


def load_targets(paths):
    """Read target files. Returns (targets, errors)."""
    targets = {}
    errors = []
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except (OSError, UnicodeDecodeError) as exc:
            errors.append("cannot read target %s: %s" % (path, exc))
            continue
        base = path.replace("\\", "/").rsplit("/", 1)[-1]
        if base in targets:
            errors.append("duplicate target basename ignored: %s" % path)
            continue
        norm, index_map = normalize(text)
        targets[base] = (text, norm, index_map)
    return targets, errors


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="trace_checker",
        description="Check a fold-in trace against its target documents.")
    parser.add_argument("trace", help="the trace file (markdown)")
    parser.add_argument("targets", nargs="+",
                        help="target document files named by the trace")
    args = parser.parse_args(argv)

    try:
        with open(args.trace, "r", encoding="utf-8") as fh:
            trace_text = fh.read()
    except OSError as exc:
        print("error: cannot read trace file: %s" % exc, file=sys.stderr)
        return 2
    except UnicodeDecodeError as exc:
        print("error: trace file is not readable text: %s" % exc, file=sys.stderr)
        return 3

    targets, target_errors = load_targets(args.targets)
    for err in target_errors:
        print("warning: %s" % err, file=sys.stderr)

    entries = parse_trace(trace_text)
    if not entries:
        print("error: no trace entries found in %s; nothing to check"
              % args.trace, file=sys.stderr)
        return 3

    results = []
    counts = {v: 0 for v in VERDICTS}
    counts["UNVERIFIABLE"] = 0
    counts["UNCHECKED"] = 0
    for entry in entries:
        verdict, quote, reason = check_entry(entry, targets)
        counts[verdict] += 1
        results.append((entry, verdict, quote, reason))

    out = []
    out.append("Fold-in Trace Check")
    out.append("Run: %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    out.append("Trace: %s" % args.trace)
    out.append("Targets supplied: %d" % len(targets))
    out.append("")
    out.append("Verdicts")
    for entry, verdict, quote, reason in results:
        head = "%s %s" % (entry.element_id, verdict)
        if entry.target:
            head += " (target: %s)" % entry.target
        out.append(head)
        if reason and verdict in ("UNVERIFIABLE", "UNCHECKED"):
            out.append("  Reason: %s" % reason)
        elif reason:
            out.append("  Note: %s" % reason)
        if quote is not None:
            out.append('  Evidence: "%s"' % one_line(quote))
    out.append("")
    out.append("Accounting")
    out.append("Elements extracted: %d" % len(entries))
    for v in VERDICTS:
        out.append("%s: %d" % (v, counts[v]))
    out.append("Unverifiable: %d" % counts["UNVERIFIABLE"])
    out.append("Unchecked: %d" % counts["UNCHECKED"])
    accounted = sum(counts.values())
    out.append("Total accounted: %d" % accounted)
    print("\n".join(out))

    if counts["UNVERIFIABLE"] or counts["UNCHECKED"]:
        return 4
    if any(counts[v] for v in ("PARTIAL", "CONTRADICTED", "MISSING")):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
