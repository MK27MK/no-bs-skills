# No-bs skills

These agent skills are meant for pragmatic programmers. I actually use them and I'm actively improving them.

## Why this repo?

- LLM answers are packed with buzzwords, and the one useful sentence is a needle in a haystack. I want the agent to do the work I assigned. The implications and the consequences are mine to reason about, until a real AGI shows up and it does me dirty.

<p align="center">
    <img src="assets/wall-e-chair.png" width="420" alt="A human reclining in a hover chair while Wall-E does the work">
</p>

- I don't like the shape the human-agent interaction usually takes: *human stops thinking* -> prompt -> the agent's plan (and no matter how much context engineering you do, unless you are building a calculator that plan hides serious holes) -> 500 to 1000+ lines of horrifying code.

## Which skill should I pick?

- You know how to code but you're lazy, or you want to iterate fast $\Rightarrow$ [`fill-the-gaps`](#fill-the-gaps)
- You don't know how to code **something** but you're eager to learn $\Rightarrow$ [`add-didactic-comments`](#add-didactic-comments)
- You want a plan you can act on, or a straight explanation of a codebase $\Rightarrow$ [`no-bs-answer`](#no-bs-answer)
- You have one narrow question and want one narrow answer $\Rightarrow$ [`answer-as-type`](#answer-as-type)

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

To try the skills without installing, clone the repo and start Claude Code with `claude --plugin-dir ./no-bs-skills`.

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

#### `no-bs-answer`

The actual information in an answer is too often buried under lines and lines of AI padding. You have a question with a practical answer, and you don't want to wade through remarks built on assumptions, which are built on guesses, which are built on nothing at all.

Use this skill to:

- Get a step-by-step plan: you want to fix a bug or implement something.
- Ask about a codebase: here the agent replies with a plain explanation and skips the plan.

#### `answer-as-type`

Ask the agent precise questions that can be answered as if they
were functions. The agent sticks to the "data type" of the answer and says nothing more.

Useful when you have a non-trivial question that still has a simple answer.

> Example: **Picking a license**
>
> The agent had reminded me the repo was missing a license, so I asked:
>
> ```
> me: "/answer-as-type str which license do I pick?"
> agent: "MIT"
> ```
