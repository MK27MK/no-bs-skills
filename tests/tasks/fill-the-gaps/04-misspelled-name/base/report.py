from stats import calcualte_avrage


def summary(scores: list[float]) -> str:
    return f"average: {calcualte_avrage(scores):.2f}"
