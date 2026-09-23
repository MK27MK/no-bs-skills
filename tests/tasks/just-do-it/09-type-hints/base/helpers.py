def merge_dicts(base, override):
    for key, value in override.items():
        base[key] = value
    return base
