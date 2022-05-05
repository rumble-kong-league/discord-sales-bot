import json
from typing import Dict


def get_kong_boosts(kong_id: int) -> Dict[str, int]:
    """For a given kong id, returns its boosts.

    Args:
        kong_id (int): Kong's id.

    Returns:
        Dict[str, int]: Kong's boosts.
    """

    meta_file = None

    with open(f"./meta/{kong_id}", "r", encoding="utf-8") as f:
        meta_file = json.loads(f.read())["attributes"]

    boosts = {}

    for item in meta_file:
        if "display_type" not in item:
            continue

        trait_type = item["trait_type"]

        if trait_type == "Vision":
            boosts["vision"] = int(item["value"])
        elif trait_type == "Defense":
            boosts["defense"] = int(item["value"])
        elif trait_type == "Shooting":
            boosts["shooting"] = int(item["value"])
        elif trait_type == "Finish":
            boosts["finish"] = int(item["value"])

    boosts["cumulative"] = sum(boosts.values())

    return boosts
