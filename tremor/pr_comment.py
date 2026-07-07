def build_comment(changed_urn, ranked):
    if not ranked:
        return None

    lines = [
        f"### Tremor: downstream risk for `{changed_urn.split(',')[1] if ',' in changed_urn else changed_urn}`",
        "",
        f"This PR touches an asset with {len(ranked)} downstream dependency(ies) flagged as worth a look before merge.",
        "",
        "| Risk | Asset | Type | Owner |",
        "|------|-------|------|-------|",
    ]

    for score, entity in ranked:
        name = entity.get("name") or entity.get("dashboardId") or entity.get("urn")
        etype = entity.get("type", "Dataset")
        owners = entity.get("ownership", {}).get("owners", []) if entity.get("ownership") else []
        owner_names = ", ".join(
            o.get("owner", {}).get("username", "unowned") for o in owners
        ) or "unowned"
        lines.append(f"| {score} | {name} | {etype} | {owner_names} |")

    lines.append("")
    lines.append("_Tremor scores based on ownership, criticality tags, and recent quality signal health in DataHub. Full lineage graph is in DataHub if you want to dig further._")
    return "\n".join(lines)