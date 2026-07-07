CRITICALITY_WEIGHTS = {"tier1": 40, "tier2": 20, "tier3": 5}
TYPE_WEIGHTS = {"Dashboard": 30, "Dataset": 10}


def score_asset(entity):
    score = 0
    entity_type = entity.get("type", "Dataset")
    score += TYPE_WEIGHTS.get(entity_type, 10)

    tags = entity.get("tags", {}).get("tags", []) if entity.get("tags") else []
    for tag_wrapper in tags:
        tag_name = tag_wrapper.get("tag", {}).get("name", "").lower()
        for tier, weight in CRITICALITY_WEIGHTS.items():
            if tier in tag_name:
                score += weight

    health = entity.get("health")
    if health and any(h.get("status") == "FAIL" for h in (health if isinstance(health, list) else [health])):
        score += 25

    owners = entity.get("ownership", {}).get("owners", []) if entity.get("ownership") else []
    if not owners:
        score += 10  # unowned assets are riskier, nobody gets paged if it breaks

    return min(score, 100)


def rank_downstream(entities, threshold):
    scored = []
    for e in entities:
        s = score_asset(e)
        if s >= threshold:
            scored.append((s, e))
    return sorted(scored, key=lambda x: -x[0])