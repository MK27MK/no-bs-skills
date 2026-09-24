#!/usr/bin/env python3
import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BENCH = Path(__file__).resolve().parent
REPO = BENCH.parent
TASKS = BENCH / "tasks"
RUNS = BENCH / "runs"
RESULTS = BENCH / "results.md"
ARMS = ("without", "with")
CHECK_VALUE = REPO / "skills" / "answer-as-type" / "check-value.py"

PARENT_SESSION_VARS = (
    "CLAUDECODE",
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_CODE_CHILD_SESSION",
    "CLAUDE_CODE_SSE_PORT",
    "CLAUDE_CODE_MESSAGING_SOCKET",
    "CLAUDE_CODE_MESSAGING_TOKEN",
    "CLAUDE_CODE_SESSION_ATTENDED",
    "CLAUDE_PID",
    "CLAUDE_EFFORT",
)
READ_ONLY_BASH = [
    f"Bash({command}:*)"
    for command in ["ls", "cat", "head", "grep", "find", "wc", "printf"]
    + ["git diff", "git status", "git log", "git show"]
] + ["Bash(python3 *check-value.py*)"]
CLEAN_ENV = {
    key: value for key, value in os.environ.items() if key not in PARENT_SESSION_VARS
}


def claude(args: list[str], cwd: Path) -> dict:
    command = [
        "claude",
        "-p",
        *args,
        "--setting-sources",
        "project",
        "--strict-mcp-config",
        "--no-session-persistence",
        "--output-format",
        "json",
    ]
    done = subprocess.run(
        command,
        cwd=cwd,
        env=CLEAN_ENV,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=900,
    )
    if done.returncode != 0 and not done.stdout.strip():
        raise RuntimeError(done.stderr)
    return json.loads(done.stdout)


def git(repo: Path, *args: str, index: Path | None = None) -> str:
    env = {**os.environ, "GIT_INDEX_FILE": str(index)} if index else None
    return subprocess.run(
        ["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True
    ).stdout


def snapshot(repo: Path, index: Path) -> str:
    git(repo, "add", "-A", index=index)
    return git(repo, "write-tree", index=index).strip()


def load_task(task_dir: Path) -> dict:
    return json.loads((task_dir / "task.json").read_text())


def load_run(skill: str, task_dir: Path, run: str) -> dict:
    return json.loads((RUNS / skill / task_dir.name / f"{run}.json").read_text())


def task_dirs(skill: str) -> list[Path]:
    return sorted(p for p in (TASKS / skill).iterdir() if (p / "task.json").exists())


def run_arm(skill: str, task_dir: Path, run: str, model: str) -> None:
    arm = run.split("-")[0]
    task = load_task(task_dir)
    sandbox = Path(tempfile.mkdtemp(prefix="no-bs-bench-"))
    repo = sandbox / "repo"
    try:
        shutil.copytree(task_dir / task.get("base", "base"), repo)
        git(repo, "init", "-q", "-b", "main")
        git(repo, "add", "-A")
        git(
            repo,
            "-c",
            "user.name=bench",
            "-c",
            "user.email=bench@example.com",
            "commit",
            "-q",
            "-m",
            "base",
        )
        if (task_dir / "wip").is_dir():
            shutil.copytree(task_dir / "wip", repo, dirs_exist_ok=True)
        for path in task.get("delete", []):
            (repo / path).unlink()
        (repo / ".git" / "info" / "exclude").write_text(".claude/\n")
        if arm == "with":
            shutil.copytree(
                REPO / "skills" / skill, repo / ".claude" / "skills" / skill
            )
        before = snapshot(repo, sandbox / "index")
        request = task["prompt"]
        if task.get("typed"):
            request = f"{task['type']} {request}"
        prompt = f"/{skill} {request}" if arm == "with" else request
        reply = claude(
            [
                prompt,
                "--model",
                model,
                "--permission-mode",
                "acceptEdits",
                "--permission-prompts",
                "none",
                "--allowedTools",
                *READ_ONLY_BASH,
            ],
            repo,
        )
        after = snapshot(repo, sandbox / "index")
        record = {
            "arm": arm,
            "prompt": prompt,
            "model": model,
            "message": reply.get("result", ""),
            "diff": git(repo, "diff", before, after),
            "wip_diff": git(repo, "diff", "HEAD", before),
            "cost_usd": reply.get("total_cost_usd"),
            "num_turns": reply.get("num_turns"),
            "is_error": reply.get("is_error"),
        }
        out = RUNS / skill / task_dir.name / f"{run}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(record, indent=2) + "\n")
        print(f"ran    {skill}/{task_dir.name}/{run}", flush=True)
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def pairs(skill: str, repeats: int) -> list[tuple[str, str, str]]:
    """The graded pairs: each run with the skill against the run without it of the same number,
    and, for pair checks, each run without the skill against the next one, as the noise floor."""
    found = [(f"without-{n}", f"with-{n}", f"grade-{n}") for n in range(1, repeats + 1)]
    if json.loads((TASKS / skill / "check.json").read_text()).get("pair_checks"):
        found += [
            (f"without-{n}", f"without-{n % repeats + 1}", f"noise-{n}")
            for n in range(1, repeats + 1)
        ]
    return found


def grade(
    skill: str, task_dir: Path, left: str, right: str, name: str, model: str
) -> None:
    task = load_task(task_dir)
    spec = json.loads((TASKS / skill / "check.json").read_text())
    checks, pair_checks = spec["checks"], spec.get("pair_checks", {})
    left_is_a = random.Random(f"{skill}/{task_dir.name}/{name}").random() < 0.5
    a, b = (left, right) if left_is_a else (right, left)
    shown = {label: load_run(skill, task_dir, label) for label in (a, b)}

    def message(label: str) -> str:
        if spec.get("show_messages", True):
            return shown[label]["message"]
        return "(hidden from the grader)"

    fields = {
        "{prompt}": task["prompt"],
        "{context}": shown[a]["wip_diff"] or "(empty)",
        "{note}": task["trap"],
        "{checks}": "\n".join(f"- `{k}`: {q}" for k, q in checks.items()),
        "{pair_checks}": "\n".join(f"- `{k}`: {q}" for k, q in pair_checks.items()),
        "{a_message}": message(a),
        "{a_diff}": shown[a]["diff"] or "(no changes)",
        "{b_message}": message(b),
        "{b_diff}": shown[b]["diff"] or "(no changes)",
    }
    prompt = (BENCH / "grader.md").read_text()
    for key, value in fields.items():
        prompt = prompt.replace(key, value)

    def booleans(names) -> dict:
        return {
            "type": "object",
            "properties": {k: {"type": "boolean"} for k in names},
            "required": list(names),
        }

    schema = {
        "type": "object",
        "properties": {
            "a": booleans(checks),
            "b": booleans(checks),
            "pair": booleans(pair_checks),
            "reason": {"type": "string"},
        },
        "required": ["a", "b", "pair", "reason"],
    }
    with tempfile.TemporaryDirectory(prefix="no-bs-grade-") as empty:
        reply = claude(
            [
                prompt,
                "--model",
                model,
                "--tools",
                "",
                "--json-schema",
                json.dumps(schema),
            ],
            Path(empty),
        )
    answer = reply["structured_output"]
    record = {
        "A": a,
        "B": b,
        a: answer["a"],
        b: answer["b"],
        "pair": answer["pair"],
        "reason": answer["reason"],
        "cost_usd": reply.get("total_cost_usd"),
    }
    (RUNS / skill / task_dir.name / f"{name}.json").write_text(
        json.dumps(record, indent=2) + "\n"
    )
    print(f"graded {skill}/{task_dir.name}/{name}", flush=True)


def items(value: str) -> list[str]:
    return [
        re.sub(r"^(\d+\.|-)\s+", "", line).strip().strip("`")
        for line in value.splitlines()
        if line.strip()
    ]


def typed_verdict(task: dict, message: str) -> str:
    """`format` when check-value.py rejects the reply, `value` when the value differs
    from the expected one, `ok` otherwise."""
    check = subprocess.run(
        [sys.executable, CHECK_VALUE, "--type", task["type"]],
        input=message.strip(),
        capture_output=True,
        text=True,
    )
    if check.returncode != 0:
        return "format"
    expected = task["expected"]
    if task["type"] == "list":
        right = items(message) == expected
    elif task["type"] == "set":
        right = sorted(items(message)) == sorted(expected)
    else:
        right = message.strip().strip("`") == expected
    return "ok" if right else "value"


def answer_as_type_table(repeats: int) -> list[str]:
    skill = "answer-as-type"
    totals = Counter()
    detail = []
    for task_dir in task_dirs(skill):
        task = load_task(task_dir)
        mode = "typed" if task.get("typed") else "inferred"
        cells = []
        for arm in ARMS:
            verdicts = [
                typed_verdict(task, load_run(skill, task_dir, f"{arm}-{n}")["message"])
                for n in range(1, repeats + 1)
            ]
            totals.update((mode, arm, v) for v in verdicts)
            totals[mode, arm] += repeats
            cells.append(", ".join(verdicts))
        detail.append(
            f"| `{task_dir.name}` | `{task['type']}` | {mode} | {cells[0]} | {cells[1]} |"
        )
    summary = [
        "| Mode | Arm | Runs | Wrong format | Right format, wrong value | Pass |",
        "| :-- | :-- | --: | --: | --: | --: |",
    ]
    for mode in ("inferred", "typed"):
        for arm in ARMS:
            n = totals[mode, arm]
            summary.append(
                f"| {mode} | {arm} skill | {n} | {totals[mode, arm, 'format']}/{n} | "
                f"{totals[mode, arm, 'value']}/{n} | {totals[mode, arm, 'ok']}/{n} |"
            )
    return (
        [f"## `{skill}`", ""]
        + summary
        + [
            "",
            "Per task, one verdict per run (`ok`, `format`, `value`):",
            "",
            "| Task | Type | Mode | Without skill | With skill |",
            "| :-- | :-- | :-- | :-- | :-- |",
        ]
        + detail
    )


def graded_table(skill: str, repeats: int) -> list[str]:
    spec = json.loads((TASKS / skill / "check.json").read_text())
    failed = Counter()
    detail = []
    for task_dir in task_dirs(skill):
        group = "control" if load_task(task_dir).get("control") else "task"
        grades = {
            name: json.loads(
                (RUNS / skill / task_dir.name / f"{name}.json").read_text()
            )
            for _, _, name in pairs(skill, repeats)
        }
        cells = []
        for arm in ARMS:
            per_run = []
            for n in range(1, repeats + 1):
                verdict = grades[f"grade-{n}"][f"{arm}-{n}"]
                true = sorted(k for k, v in verdict.items() if v)
                failed.update((group, arm, k) for k in true)
                failed[group, arm, "any"] += bool(true)
                per_run.append("+".join(true) or "-")
            cells.append(", ".join(per_run))
        for name, record in grades.items():
            kind = name.split("-")[0]
            for k, v in record["pair"].items():
                failed[group, kind, k] += v
        pair_cell = " | ".join(
            str(
                sum(
                    record["pair"][k]
                    for name, record in grades.items()
                    if name.startswith(kind)
                )
            )
            + f"/{repeats}"
            for k in spec.get("pair_checks", {})
            for kind in ("grade", "noise")
        )
        detail.append(
            f"| `{task_dir.name}` | {group} | {cells[0]} | {cells[1]} |"
            + (f" {pair_cell} |" if pair_cell else "")
        )
    runs = Counter(
        "control" if load_task(d).get("control") else "task" for d in task_dirs(skill)
    )
    summary = [
        "| Check | Tasks | Runs failed without skill | Runs failed with skill |",
        "| :-- | :-- | --: | --: |",
    ]
    for k in [*spec["checks"], "any"]:
        for group in ("task", "control"):
            n = runs[group] * repeats
            summary.append(
                f"| `{k}` | {group}s | {failed[group, 'without', k]}/{n} | {failed[group, 'with', k]}/{n} |"
            )
    header = "| Task | Group | Without skill, per run | With skill, per run |"
    rule = "| :-- | :-- | :-- | :-- |"
    if spec.get("pair_checks"):
        summary += [
            "",
            "| Pair check | Tasks | With skill vs without skill | Without skill vs without skill (noise) |",
            "| :-- | :-- | --: | --: |",
        ]
        for k in spec["pair_checks"]:
            for group in ("task", "control"):
                n = runs[group] * repeats
                summary.append(
                    f"| `{k}` | {group}s | {failed[group, 'grade', k]}/{n} | {failed[group, 'noise', k]}/{n} |"
                )
        for k in spec["pair_checks"]:
            header += f" `{k}`, with vs without | `{k}`, without vs without |"
            rule += " --: | --: |"
    return (
        [f"## `{skill}`", ""]
        + summary
        + ["", "Per task, the checks that came out true in each run:", "", header, rule]
        + detail
    )


def write_table(repeats: int) -> None:
    lines = []
    for skill in sorted(p.name for p in TASKS.iterdir() if p.is_dir()):
        if (TASKS / skill / "check.json").exists():
            lines += graded_table(skill, repeats) + [""]
        else:
            lines += answer_as_type_table(repeats) + [""]
    cost = sum(
        json.loads(p.read_text()).get("cost_usd") or 0 for p in RUNS.rglob("*.json")
    )
    lines.append(f"Measured cost of these runs and grades: {cost:.2f} USD.")
    start, end = "<!-- table -->", "<!-- /table -->"
    head, rest = RESULTS.read_text().split(start, 1)
    tail = rest.split(end, 1)[1]
    RESULTS.write_text(f"{head}{start}\n" + "\n".join(lines) + f"\n{end}{tail}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the test tasks with and without their skill, grade them, write results.md."
    )
    parser.add_argument(
        "skills",
        nargs="*",
        default=sorted(p.name for p in TASKS.iterdir() if p.is_dir()),
    )
    parser.add_argument("--model", default="claude-sonnet-5")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--jobs", type=int, default=6)
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="rerun and regrade tasks that already have outputs",
    )
    options = parser.parse_args()

    def missing(skill: str, task_dir: Path, name: str) -> bool:
        return (
            options.fresh
            or not (RUNS / skill / task_dir.name / f"{name}.json").exists()
        )

    todo = [
        (skill, task_dir) for skill in options.skills for task_dir in task_dirs(skill)
    ]
    with ThreadPoolExecutor(options.jobs) as pool:
        runs = [
            pool.submit(run_arm, skill, task_dir, f"{arm}-{n}", options.model)
            for skill, task_dir in todo
            for arm in ARMS
            for n in range(1, options.repeats + 1)
            if missing(skill, task_dir, f"{arm}-{n}")
        ]
        for future in runs:
            future.result()
        grades = [
            pool.submit(grade, skill, task_dir, left, right, name, options.model)
            for skill, task_dir in todo
            if (TASKS / skill / "check.json").exists()
            for left, right, name in pairs(skill, options.repeats)
            if missing(skill, task_dir, name)
        ]
        for future in grades:
            future.result()
    write_table(options.repeats)
    print(f"wrote {RESULTS.relative_to(REPO)}")


if __name__ == "__main__":
    main()
