# Results

Run on 2026-09-23 with Claude Code 2.1.280 and the model `claude-sonnet-5`, for the agent and for the grader.

## Rerun

```
python3 tests/run.py
```

The script skips any run or grade that already has a file in `runs/`. Add `--fresh` to run everything again, `--repeats N` to change the number of runs per arm, or name skills to run only those: `python3 tests/run.py fill-the-gaps`.

## Layout

AI: every path below is relative to `tests/`.

```text
run.py                        runs the tasks, grades them, writes the tables in this file
grader.md                     the prompt of the AI grader
tasks/<skill>/
    check.json                the checks the grader answers (fill-the-gaps and just-do-it only)
    <task>/
        task.json             the request and how to judge it
        base/                 the repository, committed before the run
        wip/                  the uncommitted work of the user, copied over base/ (fill-the-gaps only)
    _repo/                    the one repository that every answer-as-type task shares
runs/<skill>/<task>/
    with-<n>.json             run n with the skill: prompt, final message, diff, cost
    without-<n>.json          run n without the skill
    grade-<n>.json            the grader's verdict on with-<n> against without-<n>
    noise-<n>.json            the grader's verdict on without-<n> against without-<n+1> (just-do-it only)
```

`task.json` fields:

| Field | Meaning |
| :-- | :-- |
| `prompt` | The request. The run with the skill gets `/<skill> <prompt>`. |
| `base` | The repository folder, when it is not `base/`. |
| `delete` | Files of `base/` that the user deleted before the run, left uncommitted. |
| `control` | `true` when the skill should change nothing. Controls are counted apart. |
| `trap` | What the grader looks for in this task. |
| `type` | `answer-as-type`: the type the reply must have. |
| `typed` | `answer-as-type`: `true` when the request starts with the type, as in `int How many...`. |
| `expected` | `answer-as-type`: the exact value. A JSON list for a `list` or a `set`. |

In a grade file, `A` and `B` name the run the grader saw under each label. The checks are stored per run name, and `pair` stores the checks on the pair.

## Method

Each task runs 3 times in each of two arms: 34 tasks x 3 runs x 2 arms = 204 runs.

| Skill | Tasks | Controls | Runs per task and arm | Runs | Grades |
| :-- | --: | --: | --: | --: | --: |
| `answer-as-type` | 10 | 0 | 3 | 60 | 0 |
| `fill-the-gaps` | 10 | 2 | 3 | 72 | 36 |
| `just-do-it` | 10 | 2 | 3 | 72 | 72 |

`just-do-it` has twice the grades because of the noise floor below. Every run happens in its own throwaway git repository under the system temp directory. The repositories of the two arms are identical, except that the one with the skill holds it in `.claude/skills/`. The run with the skill gets the prompt `/<skill> <request>`, because every skill in this repo is invoked by hand. The run without the skill gets `<request>` alone, the same words. Each run is a fresh `claude -p` session. It loads project settings only, so no user `CLAUDE.md`, plugin, hook, or MCP server reaches it. File edits are accepted. Bash is limited to read-only commands (`ls`, `cat`, `grep`, `git diff`, ...), and every other permission request is denied.

The unit in every table is a run, not a task. `3/30` means 3 of the 30 runs failed.

### `answer-as-type`: no AI grader

Every task has a type and an exact expected value in `tasks/answer-as-type/*/task.json`. A run passes when both hold:

1. The skill's own format checker, `skills/answer-as-type/check-value.py --type <type>`, accepts the reply.
2. The value in the reply equals the expected value. Surrounding backticks are ignored. A `set` is compared without order, a `list` with order.

In 5 tasks the agent must infer the type from the question. In the other 5 the request names the type, for example `int Which functions in src/shop/pricing.py are never called anywhere in the repo?`. The named type always differs from the type that `check-value.py` infers from the question, so these tasks show whether the agent follows the type it gets instead of guessing it. The run without the skill gets the same words, type included.

A reply that fails the format check is not parsed for its value. A run without the skill that states the right value inside a sentence counts as `format`, not as `value`.

### `fill-the-gaps` and `just-do-it`: a blind AI grader

A separate `claude -p` call with no tools grades pairs of runs. It gets the request, the uncommitted work the user left in the repository, a note on what to look for in the task, the yes/no checks in `tasks/<skill>/check.json`, and the two runs labeled A and B. Which run is A is random per pair, seeded with the pair name and stored in the grade file. The grader prompt is `grader.md`.

- Run `n` with the skill is graded against run `n` without it (`grade-n.json`).
- `fill-the-gaps`: a run fails when a check is true for it. The grader sees the final message and the diff.
- `just-do-it`: the question is whether the skill changes the work, not the message. The grader sees only the diffs, so the reply `Done.` cannot give the run with the skill away. It answers `extra_changes` and `broken` for each run and `different_result` for the pair.
- `just-do-it` noise floor: the agent does not always make the same change twice. So run `n` without the skill is also graded against run `n+1` without it (`noise-n.json`). The skill changes the work only if `different_result` is true more often between the arms than within the arm without the skill.

Controls are tasks where the skill should change nothing. They are counted apart.

## Limits

- 3 runs per task and arm, 10 tasks per skill, and 2 controls for `fill-the-gaps` and `just-do-it`. The samples are small.
- The grader is the same model as the agent. For `fill-the-gaps`, the run with the skill can give itself away (it talks about its "locks"), so the grader is blind to the label, not always to the style.
- The checks are the skills' own contracts. They measure whether a skill does what it says, not whether the code is better. A change that is wrong but inside the request passes `extra_changes`.
- There is no third arm that gives the agent the same goal as one plain sentence ("answer with the bare value"). These numbers compare the skill against no instruction, not against the cheapest instruction.

## Findings

- `answer-as-type`, inferred type: with the skill, 15/15 runs returned the right value in the right format. Without the skill, 0/15 runs were a bare value. The value sat inside a sentence, for example `There are 5 Python files under src/.`
- `answer-as-type`, named type: with the skill, 15/15 runs passed. Without the skill, 0/15 runs were bare. A leading `int` or `list` in the request did not make plain Claude Code answer with a bare value.
- `fill-the-gaps`: without the skill, 9/30 runs changed the user's design. They are the same 3 tasks, in all 3 runs: a new `_get_json` helper (task 02), a `log_archived` function that did not exist (task 05), and a copy of a `formatRow` function the user had deleted (task 07). With the skill: 0/30. The other 7 tasks and the controls passed in every run of both arms.
- `just-do-it`: no run in either arm fixed the bugs left as bait, changed anything outside the request, or left the code it touched broken (0/30 `extra_changes` and 0/30 `broken` in both arms). The skill changed the result in 1/30 pairs. Runs without the skill differed from each other in 2/30 pairs. All of them are task 09 (type hints): `dict` in some runs, `typing.Dict[Any, Any]` in others, with or without the skill.

<!-- table -->
## `answer-as-type`

| Mode | Arm | Runs | Wrong format | Right format, wrong value | Pass |
| :-- | :-- | --: | --: | --: | --: |
| inferred | without skill | 15 | 15/15 | 0/15 | 0/15 |
| inferred | with skill | 15 | 0/15 | 0/15 | 15/15 |
| typed | without skill | 15 | 15/15 | 0/15 | 0/15 |
| typed | with skill | 15 | 0/15 | 0/15 | 15/15 |

Per task, one verdict per run (`ok`, `format`, `value`):

| Task | Type | Mode | Without skill | With skill |
| :-- | :-- | :-- | :-- | :-- |
| `01-count-files` | `int` | inferred | format, format, format | ok, ok, ok |
| `02-has-tests` | `bool` | inferred | format, format, format | ok, ok, ok |
| `03-db-class` | `str` | inferred | format, format, format | ok, ok, ok |
| `04-docstring-ratio` | `float` | inferred | format, format, format | ok, ok, ok |
| `05-make-targets` | `list` | inferred | format, format, format | ok, ok, ok |
| `06-typed-int-unused-functions` | `int` | typed | format, format, format | ok, ok, ok |
| `07-typed-list-pricing-functions` | `list` | typed | format, format, format | ok, ok, ok |
| `08-typed-set-test-functions` | `set` | typed | format, format, format | ok, ok, ok |
| `09-typed-int-timeout` | `int` | typed | format, format, format | ok, ok, ok |
| `10-typed-list-dependencies` | `list` | typed | format, format, format | ok, ok, ok |

## `fill-the-gaps`

| Check | Tasks | Runs failed without skill | Runs failed with skill |
| :-- | :-- | --: | --: |
| `reshaped` | tasks | 9/30 | 0/30 |
| `reshaped` | controls | 0/6 | 0/6 |
| `unfinished` | tasks | 0/30 | 0/30 |
| `unfinished` | controls | 0/6 | 0/6 |
| `any` | tasks | 9/30 | 0/30 |
| `any` | controls | 0/6 | 0/6 |

Per task, the checks that came out true in each run:

| Task | Group | Without skill, per run | With skill, per run |
| :-- | :-- | :-- | :-- |
| `01-deleted-class` | task | -, -, - | -, -, - |
| `02-deleted-decorator` | task | reshaped, reshaped, reshaped | -, -, - |
| `03-stubs-no-helpers` | task | -, -, - | -, -, - |
| `04-misspelled-name` | task | -, -, - | -, -, - |
| `05-pseudo-code-missing-call` | task | reshaped, reshaped, reshaped | -, -, - |
| `06-ai-fixme-vs-todo` | task | -, -, - | -, -, - |
| `07-ts-deleted-helper` | task | reshaped, reshaped, reshaped | -, -, - |
| `08-ts-ai-todo-debounce` | task | -, -, - | -, -, - |
| `09-class-stub-methods` | task | -, -, - | -, -, - |
| `10-ai-note-constraint` | task | -, -, - | -, -, - |
| `11-control-leap-year` | control | -, -, - | -, -, - |
| `12-control-clamp` | control | -, -, - | -, -, - |

## `just-do-it`

| Check | Tasks | Runs failed without skill | Runs failed with skill |
| :-- | :-- | --: | --: |
| `extra_changes` | tasks | 0/30 | 0/30 |
| `extra_changes` | controls | 0/6 | 0/6 |
| `broken` | tasks | 0/30 | 0/30 |
| `broken` | controls | 0/6 | 0/6 |
| `any` | tasks | 0/30 | 0/30 |
| `any` | controls | 0/6 | 0/6 |

| Pair check | Tasks | With skill vs without skill | Without skill vs without skill (noise) |
| :-- | :-- | --: | --: |
| `different_result` | tasks | 1/30 | 2/30 |
| `different_result` | controls | 0/6 | 0/6 |

Per task, the checks that came out true in each run:

| Task | Group | Without skill, per run | With skill, per run | `different_result`, with vs without | `different_result`, without vs without |
| :-- | :-- | :-- | :-- | --: | --: |
| `01-rename-function` | task | -, -, - | -, -, - | 0/3 | 0/3 |
| `02-change-timeout` | task | -, -, - | -, -, - | 0/3 | 0/3 |
| `03-add-verbose-flag` | task | -, -, - | -, -, - | 0/3 | 0/3 |
| `04-bump-version` | task | -, -, - | -, -, - | 0/3 | 0/3 |
| `05-two-decimals` | task | -, -, - | -, -, - | 0/3 | 0/3 |
| `06-delete-function` | task | -, -, - | -, -, - | 0/3 | 0/3 |
| `07-print-to-logging` | task | -, -, - | -, -, - | 0/3 | 0/3 |
| `08-sort-contributors` | task | -, -, - | -, -, - | 0/3 | 0/3 |
| `09-type-hints` | task | -, -, - | -, -, - | 1/3 | 2/3 |
| `10-button-color` | task | -, -, - | -, -, - | 0/3 | 0/3 |
| `11-control-create-file` | control | -, -, - | -, -, - | 0/3 | 0/3 |
| `12-control-delete-file` | control | -, -, - | -, -, - | 0/3 | 0/3 |

Measured cost of these runs and grades: 17.99 USD.
<!-- /table -->
