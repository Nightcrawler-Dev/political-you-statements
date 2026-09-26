#!/usr/bin/env python3
"""Validate a Current Statements batch (statements/current.json).

Usage: python3 workbench/validate_statements.py [file] [--today YYYY-MM-DD]
Exit code 0 = clean, 1 = errors. Python 3.8+, standard library only.
If the optional `jsonschema` package is installed, the file is also checked
against current.schema.json (next to the file, else statements/).

Rules (docs/STATEMENTS_WORKFLOW.md):
- Structure and field formats match statements/current.schema.json.
- Balance: statements are keyed by topic (the 7 quiz topics). A topic is
  all four parties or none: a topic may be left out for a month, but a topic
  that is present must have all four parties, with the same number of
  statements for each party (1 each or 2 each). A missing party is an error.
  The batch must cover at least one topic.
- Every statement has an https source URL, a source title, and a date.
- batchMonth is no later than next month (a batch may be prepared ahead).
- Dates fall within about 12 months: no earlier than 365 days before the
  end of the batch month, not after the batch month, and not in the future.
  A published batch must also be no more than 365 days old today.
- verifiedAt is on or after the statement date and not in the future.
- sample files are never published, and every sample speaker and quote says
  SAMPLE. Real files must not contain the word SAMPLE.
"""
from __future__ import annotations

import calendar
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILE = ROOT / "statements" / "current.json"
SCHEMA_FILE = ROOT / "statements" / "current.schema.json"

PARTIES = ["green", "libertarian", "democratic", "republican"]
# The 7 quiz topics. Checked against data/topics.json when that file exists.
TOPICS = [
    "courts-justices", "safety-security", "trust-democracy", "jobs-prices",
    "borders-immigration", "health-care-access", "abortion-choice",
]
TOP_KEYS = {"schemaVersion", "batchMonth", "published", "sample", "notes", "statements"}
REQUIRED_TOP = TOP_KEYS - {"notes"}
FIELDS = ["id", "topicId", "partyId", "speaker", "speakerTitle", "quote",
          "date", "sourceUrl", "sourceTitle", "verifiedAt"]
MAX_PER_PARTY = 2
WINDOW_DAYS = 365
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _date(value):
    if not isinstance(value, str) or not ISO.match(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _topics_from_data(root: Path) -> list | None:
    path = root / "data" / "topics.json"
    if not path.is_file():
        return None
    topics = json.loads(path.read_text(encoding="utf-8"))
    return [t.get("id") for t in sorted(topics, key=lambda t: t.get("order", 0))]


def validate(path: Path = DEFAULT_FILE, today: date | None = None, root: Path = ROOT):
    """Return (errors, warnings, summary) for the batch at [path]."""
    today = today or date.today()
    errors: list[str] = []
    warnings: list[str] = []
    label = path.name

    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"{label}: file not found"], [], ""
    except Exception as exc:  # noqa: BLE001
        return [f"{label}: cannot parse JSON ({exc})"], [], ""
    if not isinstance(doc, dict):
        return [f"{label}: top level must be an object"], [], ""

    topics = list(TOPICS)
    from_data = _topics_from_data(root)
    if from_data is not None and from_data != topics:
        errors.append("validate_statements.py: TOPICS no longer matches data/topics.json; update it")
        topics = from_data

    try:
        import jsonschema  # type: ignore

        schema_file = path.parent / "current.schema.json"
        if not schema_file.is_file():
            schema_file = SCHEMA_FILE
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        for problem in jsonschema.Draft202012Validator(schema).iter_errors(doc):
            where = "/".join(str(p) for p in problem.absolute_path) or "(root)"
            errors.append(f"{label}: schema: {where}: {problem.message}")
    except ImportError:
        pass

    for key in sorted(REQUIRED_TOP - doc.keys()):
        errors.append(f"{label}: missing {key}")
    for key in sorted(doc.keys() - TOP_KEYS):
        errors.append(f"{label}: unknown top-level field {key}")
    if doc.get("schemaVersion") != 1:
        errors.append(f"{label}: schemaVersion must be 1")
    published = doc.get("published")
    sample = doc.get("sample")
    if not isinstance(published, bool):
        errors.append(f"{label}: published must be true or false")
    if not isinstance(sample, bool):
        errors.append(f"{label}: sample must be true or false")
    if sample is True and published is True:
        errors.append(f"{label}: a sample batch must not be published")

    batch = doc.get("batchMonth")
    batch_end = None
    if isinstance(batch, str) and re.match(r"^\d{4}-(0[1-9]|1[0-2])$", batch):
        year, month = int(batch[:4]), int(batch[5:])
        batch_end = date(year, month, calendar.monthrange(year, month)[1])
        batch_start = date(year, month, 1)
        # A batch may be prepared late in the month before (e.g. the October
        # batch in late September), but no further ahead than next month.
        next_month = date(today.year + today.month // 12, today.month % 12 + 1, 1)
        if batch_start > next_month:
            errors.append(f"{label}: batchMonth {batch} is more than one month ahead")
        if published is True and (today - batch_end).days > WINDOW_DAYS:
            errors.append(f"{label}: published batch {batch} is more than 12 months old; publish a new batch")
    else:
        errors.append(f"{label}: batchMonth must be YYYY-MM")

    statements = doc.get("statements")
    if not isinstance(statements, list):
        errors.append(f"{label}: statements must be a list")
        statements = []

    ids = Counter()
    quotes = defaultdict(list)
    counts: dict[str, Counter] = defaultdict(Counter)
    for index, item in enumerate(statements):
        where = f"{label}: statements[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{where}: must be an object")
            continue
        sid = item.get("id")
        if isinstance(sid, str) and sid:
            where = f"{label}: {sid}"
        for key in FIELDS:
            value = item.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{where}: missing or empty {key}")
        for key in sorted(item.keys() - set(FIELDS)):
            errors.append(f"{where}: unknown field {key}")
        if isinstance(sid, str) and sid:
            ids[sid] += 1
            if not re.match(r"^[a-z0-9][a-z0-9-]{2,80}$", sid):
                errors.append(f"{where}: id must be lowercase letters, digits, and hyphens")

        topic = item.get("topicId")
        party = item.get("partyId")
        if topic not in topics:
            errors.append(f"{where}: unknown topicId {topic!r}")
        if party not in PARTIES:
            errors.append(f"{where}: unknown partyId {party!r}")
        if topic in topics and party in PARTIES:
            counts[topic][party] += 1

        url = item.get("sourceUrl")
        if isinstance(url, str) and not re.match(r"^https://[^\s]+$", url):
            errors.append(f"{where}: sourceUrl must be a single https:// link")

        quote = item.get("quote")
        if isinstance(quote, str) and quote.strip():
            quotes[" ".join(quote.split()).lower()].append(sid)
            if quote.strip()[0] in "\"“'" and quote.strip()[-1] in "\"”'":
                warnings.append(f"{where}: quote is wrapped in quotation marks; store the words only")

        said = _date(item.get("date"))
        checked = _date(item.get("verifiedAt"))
        if item.get("date") and said is None:
            errors.append(f"{where}: date must be a real YYYY-MM-DD date")
        if item.get("verifiedAt") and checked is None:
            errors.append(f"{where}: verifiedAt must be a real YYYY-MM-DD date")
        if said:
            if said > today:
                errors.append(f"{where}: date {said} is in the future")
            if batch_end:
                if said > batch_end:
                    errors.append(f"{where}: date {said} is after batch month {batch}")
                if (batch_end - said).days > WINDOW_DAYS:
                    errors.append(f"{where}: date {said} is more than 12 months before batch month {batch}")
            if published is True and (today - said).days > WINDOW_DAYS:
                errors.append(f"{where}: date {said} is more than 12 months old")
        if checked:
            if checked > today:
                errors.append(f"{where}: verifiedAt {checked} is in the future")
            if said and checked < said:
                errors.append(f"{where}: verifiedAt {checked} is before the statement date {said}")

        if sample is True:
            for key in ("speaker", "quote"):
                if "SAMPLE" not in str(item.get(key, "")):
                    errors.append(f"{where}: sample {key} must contain the word SAMPLE")
        elif sample is False and "SAMPLE" in " ".join(str(item.get(k, "")) for k in FIELDS):
            errors.append(f"{where}: contains SAMPLE in a real batch")

    for sid, n in ids.items():
        if n > 1:
            errors.append(f"{label}: id {sid} is used {n} times")
    for quote, owners in quotes.items():
        if len(owners) > 1:
            errors.append(f"{label}: the same quote appears in {owners}")

    covered = 0
    for topic in topics:
        per_party = counts.get(topic, Counter())
        present = {p: per_party[p] for p in PARTIES if per_party[p] > 0}
        if not present:
            warnings.append(f"{topic}: left out this month (allowed: all four parties or none)")
            continue
        covered += 1
        missing = [p for p in PARTIES if p not in present]
        if missing:
            errors.append(f"{topic}: no statement for {missing}; every topic needs all four parties")
        if len(set(present.values())) > 1:
            detail = ", ".join(f"{p} {n}" for p, n in present.items())
            errors.append(f"{topic}: parties have different numbers of statements ({detail}); each party needs the same count")
        too_many = [p for p, n in present.items() if n > MAX_PER_PARTY]
        if too_many:
            errors.append(f"{topic}: more than {MAX_PER_PARTY} statements for {too_many}")

    if covered == 0:
        errors.append(f"{label}: no topics; a batch needs at least one topic with all four parties")

    summary = (f"{label}: batch {batch}, published={published}, sample={sample}, "
               f"{len(statements)} statement(s) across {covered} of {len(topics)} topic(s)")
    return errors, warnings, summary


def main(argv: list[str]) -> int:
    args = list(argv)
    today = None
    if "--today" in args:
        at = args.index("--today")
        today = date.fromisoformat(args[at + 1])
        del args[at:at + 2]
    path = Path(args[0]) if args else DEFAULT_FILE
    errors, warnings, summary = validate(path, today=today)
    if summary:
        print(summary)
    for message in warnings:
        print("WARN ", message)
    for message in errors:
        print("ERROR", message)
    print("RESULT:", "CLEAN" if not errors else f"{len(errors)} error(s)", f"({len(warnings)} warning(s))")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
