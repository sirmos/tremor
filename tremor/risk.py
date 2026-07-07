CRITICALITY_WEIGHTS = {"tier1": 40, "tier2": 20, "tier3": 5}
BI_PLATFORM_WEIGHTS = {"powerbi": 35, "tableau": 35, "looker": 35}


def _platform_from_urn(urn):
    if not urn:
        return None
    for platform in BI_PLATFORM_WEIGHTS:
        if f"dataPlatform:{platform}" in urn:
            return platform
    return None


def score_asset(entity):
    score = 10  # baseline for any downstream dependency

    platform = _platform_from_urn(entity.get("urn"))
    if platform:
        score += BI_PLATFORM_WEIGHTS[platform]  # user-facing BI surfaces hurt more when they break

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