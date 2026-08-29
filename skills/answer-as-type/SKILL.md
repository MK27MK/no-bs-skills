---
description: Answer as a return value, not as prose.
argument-hint: "type: bool | int | float | str | list | set | infer = infer"
arguments: [type]
disable-model-invocation: true
---

# Func

The user called a function. Return its value. Nothing else.

No preamble, no restatement of the question, no reasoning, no caveat, no unit, no trailing sentence.

- IF the answer needs work first (read files, run a command, count something), THEN do the work with tools, and return only the value.
- IF `type` is set, THEN return that type.
- IF `type` is not set, THEN infer it from the question, using the table below.
- IF the value cannot be computed, THEN return `None` and nothing else.

## Return types

| Type    | Format                                    | Infer it when the question asks for      |
| ------- | ----------------------------------------- | ---------------------------------------- |
| `bool`  | `true` or `false`                          | yes/no, is/are, does/do, can/should       |
| `int`   | bare digits: `5`                           | how many, count, index, line number       |
| `float` | bare decimal: `0.42`                       | ratio, percentage, average, duration      |
| `str`   | the bare string, no quotes                 | a name, a path, a command, a single value |
| `list`  | numbered markdown list                     | steps, an ordered procedure, a ranking    |
| `set`   | bullet markdown list                       | items where order carries no meaning      |

- `bool` is `true`/`false`, never `Yes`/`No`.
- `int` and `float` carry no unit, no thousands separator, no words. `5`, not `5 sub-agents`.
- `float` keeps the precision the question implies. Do not pad zeros.
- `list` and `set` items are values too: each one is short and bare, with no explanation attached.
- Order matters in a `list` and never in a `set`. IF unsure which, THEN return a `set`.
- NEVER wrap the value in a code fence unless the value is itself code.

## The check

Before you deliver the value, run `check-value.py` from this skill's folder. Give it the
value on stdin. IF `type` is set, THEN pass `--type`. IF `type` is not set, THEN pass
`--question` with the question of the user, and the script infers the type.

```
printf '%s' "$VALUE" | python3 <skill-folder>/check-value.py --type set
printf '%s' "$VALUE" | python3 <skill-folder>/check-value.py --question "two what?"
```

Exit 0 means the format holds. Exit 1 prints one finding per line. IF the script exits 1,
THEN rewrite the value and run it again. Deliver only a value that exits 0.

The script reads the format, not the truth. It cannot tell you that the value is correct.

## Examples

Q: did you edit any file outside `src/`?
```
false
```

Q: /func int how many sub-agents did you spawn during the session?
```
5
```

Q: which kind of return values does this skill implement?
```
- bool
- int
- float
- str
- list
- set
```

Q: how do I release a new version?
```
1. Bump the version in `pyproject.toml`.
2. Run `uv build`.
3. Tag the commit.
4. Push the tag.
```

## The follow-up

IF the user then asks why, or how, THEN explain in one or two sentences. Give the fact that produced the value. Do not repeat the value.
