# No-bs skills

These agent skills are meant for pragmatic programmers. I actually use them and I'm actively improving them.

## Why this repo?

- LLM answers are packed with buzzwords, and the one useful sentence is a needle in a haystack. I want the agent to do the work I assigned. The implications and the consequences are mine to reason about, until a real AGI shows up and it does me dirty.

<p align="center">
    <img src="assets/wall-e-chair.png" width="420" alt="A human reclining in a hover chair while Wall-E does the work">
</p>

- I don't like the shape the human-agent interaction usually takes: *human stops thinking* -> prompt -> the agent's plan (and no matter how much context engineering you do, unless you are building a calculator that plan hides serious holes) -> 500 to 1000+ lines of horrifying code.

## Which skill should I pick?

I...

- Know how to code but I'm lazy, or I want to iterate fast $\Rightarrow$ [`fill-the-gaps`](#fill-the-gaps)
- Don't know how to code **something** but I'm eager to learn $\Rightarrow$ [`add-didactic-comments`](#add-didactic-comments)
- Want a plan I can act on, or a straight explanation of a codebase $\Rightarrow$ [`no-bs-answer`](#no-bs-answer)
- Have one narrow question and want one narrow answer $\Rightarrow$ [`answer-as-type`](#answer-as-type)
- Want the agent to execute and shut up $\Rightarrow$ [`just-do-it`](#just-do-it)
- Don't want to take the agent's word for it $\Rightarrow$ [`back-your-claims`](#back-your-claims)

## Install

In Claude Code, register this repo as a plugin marketplace, then install the plugin from it:

```
/plugin marketplace add MK27MK/no-bs-skills
/plugin install no-bs-skills@no-bs-skills
```

Run `/reload-plugins` if the install summary asks for it. The skills are namespaced under the plugin name:

```
/no-bs-skills:no-bs-answer how does the auth middleware decide who is logged in?
```

## Skills

### Coding skills

#### `fill-the-gaps`

Use this to leave work half-written on purpose. Bare signatures, empty
classes, pseudo code, deleted calls, and `AI TODO` / `AI FIXME` / `AI NOTE`
markers all count as instructions: you write the code that says what the
software must be, and the agent writes the code that makes it run.

This skill takes two optional arguments, both `y` (yes) by default:

- `lock_definitions`: the agent writes no new function, class, or method. It
  fills the gaps with the definitions the tree already holds, and deletes any
  call whose definition is missing.
- `lock_names`: the agent keeps every name as you wrote it, even one it thinks
  is wrong.

> Example: **New feature or new project**
>
> You sketch the shape: the signatures you want to call, the empty classes that
> name the concepts, a few lines of pseudo code for the tricky part. Then you
> run the skill with both locks on. You get an implementation that matches the
> shape you drew.
>
> Advantages: at modeling a domain and shaping an architecture, the pragmatic
> programmer beats even a frontier model. The sketch is the guard-rail: you keep
> the decisions you are better at, and the agent gets the mechanical work it is
> better at.

> Example: **Refactor**
>
> You are dealing with badly written code. You delete what has to go, drop an
> `AI FIXME [optional_details]` comment on what stays but is wrong, and leave the callers pointing at
> nothing. Run with `lock_definitions: n` when the rewrite needs new pieces, and
> `lock_names: n` when the old names are part of the problem.

#### `add-didactic-comments`

Use this while learning an API. Point the agent at some files, name the topics
(`TanStack Query`, `Pandas`, ...), and it comments every call belonging to those topics,
saying what the call does to your data and linking the docs for the exact symbol.

It touches comments only, and it stops if you have unstaged changes.

### No-edit skills

These skills can read the repo but cannot change it.

#### `answer-as-type`

Ask the agent precise questions that can be answered as if they
were functions. The agent sticks to the "data type" of the answer and says nothing more.

Useful when you have a non-trivial question that still has a simple answer.

Name the return type with the first word of the request: `bool`, `int`, `float`, `str`,
`list`, or `set`. Leave it out and the agent infers it from the question. A type you name is
final: `int` on a question about items returns how many they are.

> Example: **Picking a license**
>
> The agent had reminded me the repo was missing a license, so I asked:
>
> ```
> me: "/no-bs-skills:answer-as-type str which license do I pick?"
> agent: "MIT"
> ```

> Example from the [tests](#tests): **a type you name**
>
> ```
> me: "int What is the HTTP timeout in src/shop/client.py?"
> agent without the skill: "The HTTP timeout is **10 seconds** — `TIMEOUT_SECONDS = 10` at
> `src/shop/client.py:3`, used in the `httpx.get` call at line 7."
> agent with the skill: "10"
> ```

#### `no-bs-answer`

The actual information in an answer is too often buried under lines and lines of AI padding. You have a question with a practical answer, and you don't want to wade through remarks built on assumptions, which are built on guesses, which are built on nothing at all.

Use this skill to:

- Get a step-by-step plan: you want to fix a bug or implement something.
- Ask about a codebase: here the agent replies with a plain explanation and skips the plan.

### Behavior skills

These skills change how the agent works and answers, whatever the task is.

#### `just-do-it`

Use this when you know exactly what you want. The agent does what you asked,
nothing else, makes sure the change works, and answers `Done.` with no remarks attached.

#### `back-your-claims`

Use this when the answer matters. Every claim the agent makes must be followed
by a link (on the web) or a clickable path (local) to a reliable, human-written
resource. No assumptions.

## Tests

Each task runs 3 times with headless Claude Code (`claude -p`, model `claude-sonnet-5`) in
each of two arms: in a throwaway git repository with the skill in `.claude/skills/`, and in
an identical repository without it. Both arms get the same request. The unit is a run, so
`9/30` means 9 of 30 runs.

| Skill | A run fails when | How it is checked | Failed without the skill | Failed with the skill |
| :-- | :-- | :-- | --: | --: |
| `answer-as-type`, type inferred | The reply is not the bare value in the expected type, or the value is wrong | The skill's `check-value.py` and an exact expected value | 15/15 | 0/15 |
| `answer-as-type`, type named in the request | Same | Same | 15/15 | 0/15 |
| `fill-the-gaps` | The agent adds, renames, or brings back a definition the user did not ask for | A blind AI grader | 9/30 | 0/30 |
| `just-do-it` | The diff changes anything the request did not ask for, or leaves the code it touched broken | A blind AI grader, shown the diffs only | 0/30 | 0/30 |

For `just-do-it`, the question is whether the skill changes the work. The grader compared
each run with the skill to a run without it: the results differed in 1/30 pairs. Two runs
without the skill differed from each other in 2/30 pairs, which is the noise floor. All of
them are type hints written as `dict` or as `typing.Dict`.

The checks are each skill's own contract. They measure whether a skill does what it says,
not whether the code is better. The baseline is no instruction at all: nothing here compares
a skill with one plain sentence in the prompt.

The tasks, the grader prompt, every raw output, and the full results are in
[`tests/`](tests/). [`tests/results.md`](tests/results.md) has the
[folder layout](tests/results.md#layout), the method, its limits, and the verdict of
every run. To run it again (it needs Claude Code logged in):

```
python3 tests/run.py
```
