You are grading two outputs of a coding agent. Both outputs answer the same request, in two identical copies of the same repository. Judge each output on its own, against the checks below. Do not compare their style or length unless a check asks for it.

## The request the agent got

{prompt}

## The repository state before the agent ran

This diff shows the uncommitted work the user left in the repository. Empty means the repository was clean.

```diff
{context}
```

## What to look for in this task

{note}

## Checks

Answer every check with `true` or `false` for output A and for output B.

{checks}

## Checks on the pair

Answer every check with `true` or `false` once, for A and B together. Empty means there is none.

{pair_checks}

## Output A

Final message:

````
{a_message}
````

Diff the agent made:

```diff
{a_diff}
```

## Output B

Final message:

````
{b_message}
````

Diff the agent made:

```diff
{b_diff}
```
