def top_players(scores: dict[str, int], limit: int) -> list[str]:
    # AI FIXME: best player first, ties broken by name
    ordered = sorted(scores, key=scores.get)
    return ordered[:limit]


def load_scores(path: str) -> dict[str, int]:
    # TODO: cache this, it's called on every request
    scores = {}
    with open(path) as handle:
        for line in handle:
            name, score = line.split(",")
            scores[name] = int(score)
    return scores
