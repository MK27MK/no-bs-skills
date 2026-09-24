#!/usr/bin/env python3
"""Report the format faults of a value that `func` is about to return.

The value comes in on stdin. `--type` names the return type. Without `--type`,
`--question` gives the question, and the type comes from the question with the
patterns of `TYPE_OF_QUESTION`. Exit 0 means the value carries the format of
its type. Exit 1 prints one finding per line and the value goes back for a
rewrite.
"""

import argparse
import re
import sys

NONE_VALUE = re.compile(r"^None$")
BOOL_VALUE = re.compile(r"^(true|false)$")
INT_VALUE = re.compile(r"^-?\d+$")
FLOAT_VALUE = re.compile(r"^-?\d+(\.\d+)?$")
STR_VALUE = re.compile(r"^\S.*\S$|^\S$")
LIST_ITEM = re.compile(r"^(?P<number>\d+)\. (?P<item>\S.*)$")
SET_ITEM = re.compile(r"^- (?P<item>\S.*)$")

CODE_FENCE = re.compile(r"^\s*```")
QUOTED = re.compile(r"^([\"'])(?P<inner>.*)\1$")
THOUSANDS_SEPARATOR = re.compile(r"^-?\d{1,3}([,_]\d{3})+")
TRAILING_PROSE = re.compile(r"[.!?]$")

MAX_ITEM_WORDS = 12

ARTICLE_OF_TYPE = {
    "int": "an",
    "bool": "a",
    "float": "a",
    "str": "a",
    "list": "a",
    "set": "a",
}

TYPE_OF_QUESTION = (
    (
        re.compile(
            r"^\s*(is|are|was|were|does|do|did|can|should|has|have)\b", re.IGNORECASE
        ),
        "bool",
    ),
    (
        re.compile(
            r"\b(how many|how much|count of|line number|index of)\b", re.IGNORECASE
        ),
        "int",
    ),
    (
        re.compile(
            r"\b(ratio|percentage|average|share of|fraction|duration)\b", re.IGNORECASE
        ),
        "float",
    ),
    (
        re.compile(
            r"\b(steps|procedure|ranking|in which order|how do i)\b", re.IGNORECASE
        ),
        "list",
    ),
    (
        re.compile(
            r"\b(two|three|four|both|which ones|what are|name the)\b", re.IGNORECASE
        ),
        "set",
    ),
)


def name_with_article(kind: str) -> str:
    return f"{ARTICLE_OF_TYPE[kind]} {kind}"


def infer_type(question: str) -> str:
    """The return type that the wording of the question asks for."""
    first_word = question.split(maxsplit=1)[:1]
    if first_word and first_word[0] in CHECK_OF_TYPE:
        return first_word[0]
    for pattern, name in TYPE_OF_QUESTION:
        if pattern.search(question):
            return name
    return "str"


def check_scalar(pattern: re.Pattern, name: str, shape: str, value: str) -> list[str]:
    if "\n" in value:
        return [
            f"{name_with_article(name)} is one line, and this value has {value.count(chr(10)) + 1}"
        ]
    if pattern.match(value):
        return []
    return [f"{name_with_article(name)} reads {shape}, and this value reads `{value}`"]


def check_str(value: str) -> list[str]:
    findings = []
    if "\n" in value:
        findings.append("a str is one line, and this value has more than one")
    quoted = QUOTED.match(value)
    if quoted:
        findings.append(f"a str carries no quotes: write `{quoted.group('inner')}`")
    if TRAILING_PROSE.search(value) and len(value.split()) > 1:
        findings.append("a str is a bare value, and this value ends as a sentence")
    if not STR_VALUE.match(value):
        findings.append("a str carries no leading or trailing space")
    return findings


def check_items(pattern: re.Pattern, name: str, shape: str, value: str) -> list[str]:
    """The findings of a `list` or a `set`: the shape of every line, then the width."""
    findings = []
    lines = value.splitlines()
    numbers = []
    for line in lines:
        match = pattern.match(line)
        if match is None:
            findings.append(
                f"{name_with_article(name)} item reads {shape}, and this line reads `{line}`"
            )
            continue
        item = match.group("item")
        if TRAILING_PROSE.search(item):
            findings.append(
                f"{name_with_article(name)} item carries no explanation: `{item}`"
            )
        if len(item.split()) > MAX_ITEM_WORDS:
            findings.append(
                f"{name_with_article(name)} item runs to {MAX_ITEM_WORDS} words at most: `{item}`"
            )
        if name == "list":
            numbers.append(int(match.group("number")))
    if name == "list" and numbers and numbers != list(range(1, len(numbers) + 1)):
        findings.append(
            f"a list numbers its items 1 to {len(numbers)}, and this one reads {numbers}"
        )
    return findings


CHECK_OF_TYPE = {
    "bool": lambda value: check_scalar(BOOL_VALUE, "bool", "`true` or `false`", value),
    "int": lambda value: check_scalar(INT_VALUE, "int", "bare digits", value),
    "float": lambda value: check_scalar(FLOAT_VALUE, "float", "a bare decimal", value),
    "str": check_str,
    "list": lambda value: check_items(LIST_ITEM, "list", "`1. item`", value),
    "set": lambda value: check_items(SET_ITEM, "set", "`- item`", value),
}


def find_faults(kind: str, value: str) -> list[str]:
    if NONE_VALUE.match(value):
        return []
    findings = []
    if CODE_FENCE.match(value) and kind != "str":
        findings.append(f"{name_with_article(kind)} carries no code fence")
        value = "\n".join(
            line for line in value.splitlines() if not CODE_FENCE.match(line)
        ).strip()
    if kind in ("int", "float") and THOUSANDS_SEPARATOR.match(value):
        findings.append(
            f"{name_with_article(kind)} carries no thousands separator: `{value}`"
        )
        return findings
    findings.extend(CHECK_OF_TYPE[kind](value))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--type", choices=sorted(CHECK_OF_TYPE))
    parser.add_argument("--question", default="")
    arguments = parser.parse_args()
    value = sys.stdin.read().strip()
    kind = arguments.type or infer_type(arguments.question)
    findings = find_faults(kind, value)
    if not findings:
        return 0
    print(f"The value below is not {name_with_article(kind)}. Return the {kind} alone.")
    print("\n".join(f"- {finding}" for finding in findings))
    return 1


if __name__ == "__main__":
    sys.exit(main())
