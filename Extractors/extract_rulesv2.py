"""
Converts an areas.wotw file into a set_rules function.

Run `parse_rules()` to extract the rules from the `areas.wotw` file.
See https://github.com/ori-community/wotw-seedgen/tree/main/wotw_seedgen to get this file.
"""

import os
import re
from typing import Pattern
from collections import Counter

# %% Data and global variables

# TODO probably best to just rework the whole code for better quality
# TODO fix typing
# TODO entrance rando
# TODO rename glitches, can_open_door, change combat, change resource function
# TODO use global variables (for list_rules...) and make it into a script

# Enemy data
ref_en: dict[str, tuple[int, list[str]]] = {
    "Mantis": (32, ["Free"]),
    "Slug": (13, ["Free"]),
    "WeakSlug": (12, ["Free"]),
    "BombSlug": (1, ["Ranged"]),
    "CorruptSlug": (1, ["Ranged"]),
    "SneezeSlug": (32, ["Dangerous"]),
    "ShieldSlug": (24, ["Free"]),
    "Lizard": (24, ["Free"]),
    "Bat": (32, ["Bat", "Aerial", "Ranged"]),
    "Hornbug": (40, ["Dangerous", "Shielded"]),
    "Skeeto": (20, ["Aerial"]),
    "SmallSkeeto": (8, ["Aerial"]),
    "Bee": (24, ["Aerial"]),
    "Nest": (25, ["Aerial"]),
    "Fish": (10, ["Free"]),
    "Waterworm": (20, ["Free"]),
    "Crab": (32, ["Dangerous"]),
    "SpinCrab": (32, ["Dangerous"]),
    "Tentacle": (40, ["Ranged"]),
    "Balloon": (1, ["Free"]),
    "Miner": (40, ["Dangerous"]),
    "MaceMiner": (60, ["Dangerous"]),
    "ShieldMiner": (60, ["Dangerous", "Shielded"]),
    "CrystalMiner": (80, ["Dangerous"]),
    "ShieldCrystalMiner": (50, ["Dangerous", "Shielded"]),
    "Sandworm": (20, ["Sand"]),
    "Spiderling": (12, ["Free"]),
}

name_convert: dict[str, str] = {  # Translation of the item names
    "DoubleJump": "Double Jump",
    "WaterDash": "Water Dash",
    "WaterBreath": "Water Breath",
    "TripleJump": "Triple Jump",
    "Water": "Clean Water",
    "BurrowsTP": "Midnight Burrows TP",
    "DenTP": "Howl's Den TP",
    "EastPoolsTP": "Central Luma TP",
    "DepthsTP": "Mouldwood Depths TP",
    "WellspringTP": "Wellspring TP",
    "ReachTP": "Baur's Reach TP",
    "HollowTP": "Kwolok's Hollow TP",
    "WestWoodsTP": "Woods Entrance TP",
    "EastWoodsTP": "Woods Exit TP",
    "WestWastesTP": "Feeding Grounds TP",
    "EastWastesTP": "Central Wastes TP",
    "OuterRuinsTP": "Outer Ruins TP",
    "WillowTP": "Willow's End TP",
    "MarshTP": "Inkwater Marsh TP",
    "GladesTP": "Glades TP",
    "WestPoolsTP": "Luma Boss TP",
    "InnerRuinsTP": "Inner Ruins TP",
    "ShriekTP": "Shriek TP",
    "Ore": "Gorlek Ore",
}


# Regular expressions used for parsing
r_comment = re.compile(" *#")  # Detects comments
r_indent = re.compile("^ *")  # Used for indents
r_colon = re.compile(" .*:")  # name between space and colon
r_trailing = re.compile(" *$")  # Trailing space
r_separate = re.compile(" at ")
r_type = re.compile("^[a-z]+ ")  # Detects the type of the path
r_name = re.compile(" [a-zA-Z.=0-9]+:")  # Name of the object
r_difficulty = re.compile("^[a-z]+[,:]")  # extracts the difficulty of the path
r_refill = re.compile(" [a-zA-Z=0-9]+$")  # Extracts the refill type if it has no colon

en_skills = ["Bow", "Grenade", "Flash", "Sentry", "Shuriken", "Spear", "Blaze"]  # Skills that require energy

# Things that require a specific treatment
combat_name = ["BreakWall", "Combat", "Boss"]

# Skills that can be used infinitely (note: Regenerate is here because of how the logic is written)
# The energy skills are also there because they are sometimes without a number of uses specified
inf_skills = ["Sword",
              "Double Jump",
              "Regenerate",
              "Dash",
              "Bash",
              "Grapple",
              "Glide",
              "Flap",
              "Water Dash",
              "Burrow",
              "Launch",
              "Clean Water",
              "Water Breath",
              "Hammer",
              "free",
              "Bow",
              "Grenade",
              "Flash",
              "Sentry",
              "Shuriken",
              "Spear",
              "Blaze",]

# Glitches that use resources
glitches = {"ShurikenBreak": ["Shuriken"],
            "SentryJump": ["Sentry"],
            "SwordSJump": ["Sword", "Sentry"],
            "HammerSJump": ["Hammer", "Sentry"],
            "SentryBurn": ["Sentry"],
            "SentryBreak": ["Sentry"],
            "SpearBreak": ["Spear"],
            "SentrySwap": ["Sentry"],
            "BlazeSwap": ["Blaze"],
            "GrenadeRedirect": ["Grenade"],
            "SentryRedirect": ["Sentry"],
            "SpearJump": ["Spear"],}

# Glitches that can be used infinitely (and only use one skill)
inf_glitches = {"RemoveKillPlane": "free",
                "HammerBreak": "Hammer",
                "LaunchSwap": "Launch",
                "FlashSwap": "Flash",
                "GrenadeJump": "Grenade",
                "GrenadeCancel": "Grenade",
                "BowCancel": "Bow",
                "PauseHover": "free",
                "GlideJump": "Glide",}

# Glitches that can be used infinitely, and use two skills
other_glitches = {"WaveDash": "can_wavedash(s, player)",
                  "HammerJump": "can_hammerjump(s, player)",
                  "SwordJump": "can_swordjump(s, player)",
                  "GlideHammerJump": "can_glidehammerjump(s, player)",}



# %% Text initialisations

header = ("\"\"\"\n"
          "Generated file, do not edit manually.\n\n"
          "See https://github.com/Satisha10/APworld_wotw_extractors for the code.\n"
          "Generated with `extract_rules.py` by running `parse_rules()`.\n"
          "\"\"\"\n\n\n")

imports = "from .Rules_Functions import *\n\n"

# %% Helpers

def try_group(regex: Pattern[str], text: str, begin=0, end=0) -> str:
    """Return the result for search, sliced between begin and end. Raise an error if no match is found."""
    match = regex.search(text)
    if match is None:
        raise RuntimeError(f"Could not find a match for {text} with {regex.pattern}.")
    if begin is None:
        begin = 0
    if end == 0:
        end = len(match.group()) + 1
    return match.group()[begin: end]


def try_end(regex: Pattern[str], text: str) -> int:
    """Return the end position of the match. Raise an error if nomatch is found."""
    match = regex.search(text)
    if match is None:
        raise RuntimeError(f"Could not find a match for {text} with {regex.pattern}.")
    return match.end()


def req_area(area: str, diff: int) -> tuple[bool, int]:
    """
    Return the requirement for entering an area.

    Returns if Regenerate is needed, and the amount of health required.
    """
    area_data = {"MidnightBurrows": (25, False),
                 "EastHollow": (20, False),
                 "WestHollow": (20, False),
                 "WestGlades": (20, False),
                 "OuterWellspring": (25, False),
                 "InnerWellspring": (25, False),
                 "WoodsEntry": (40, True),
                 "WoodsMain": (40, True),
                 "LowerReach": (40, True),
                 "UpperReach": (40, True),
                 "UpperDepths": (40, True),
                 "LowerDepths": (40, True),
                 "PoolsApproach": (25, True),
                 "EastPools": (40, True),
                 "UpperPools": (40, True),
                 "WestPools": (40, True),
                 "LowerWastes": (50, True),
                 "UpperWastes": (50, True),
                 "WindtornRuins": (50, True),
                 "WeepingRidge": (60, True),
                 "WillowsEnd": (60, True),
                 }

    if area in (None, "MarshSpawn", "HowlsDen", "MarshPastOpher", "GladesTown"):
        return False, 0
    if diff >= 5:  # Unsafe
        return False, 0
    if diff >= 1:
        if area_data[area][1]:  # Kii, Gorlek
            return True, 0
        return False, 0

    if area_data[area][1]:  # Moki
        return True, area_data[area][0]
    return False, area_data[area][0]


def convert() -> None:
    """Convert the data given by the arguments into an add_rule function, and add it to the right difficulty."""
    global anchor, path_type, path_name, list_rules, entrances, refill_type, difficulty, req, glitched, arrival
    health_req = 0  # Requirement when entering a new area

    and_req = []
    or_req = []

    if path_type == "conn" and "." in path_name:  # Gets the requirements when entering a new area.
        dot_position = path_name.find(".")
        f_area = path_name[:dot_position]
        if "." in anchor:
            dot_position = anchor.find(".")
            i_area = anchor[:dot_position]  # Extracts the name of the starting area
        else:
            i_area = ""
        if i_area != f_area:
            regen, health_req = req_area(f_area, difficulty)
            if regen:
                and_req.append("Regenerate")

    if path_type == "refill":
        path_name = refill_type + anchor

    arrival = path_name
    conn_name = f"{anchor} -> {path_name}"
    if conn_name not in entrances:
        entrances.append(conn_name)

    s_req = req.split(", ")
    for elem in s_req:
        if " OR " in elem:
            or_req.append(elem.split(" OR "))
        else:
            and_req.append(elem)

    if len(or_req) == 0:
        and_requirements, glitched = parse_and(and_req, difficulty)
        list_rules = append_rule(and_requirements, "", "", "", health_req, difficulty, glitched, anchor, arrival,
                              list_rules)

    elif len(or_req) == 1:
        or_skills0, or_glitch0, or_resource0 = order_or(or_req[0])

        for req in or_glitch0:
            and_req.append(req)
            and_requirements, glitched = parse_and(and_req, difficulty)
            and_req.remove(req)
            list_rules = append_rule(and_requirements, "", "", "", health_req, difficulty, True, anchor, arrival,
                                  list_rules)
        if or_skills0:
            and_requirements, glitched = parse_and(and_req, difficulty)
            list_rules = append_rule(and_requirements, or_skills0, "", "", health_req, difficulty, glitched, anchor,
                                  arrival, list_rules)
        if or_resource0:
            and_requirements, glitched = parse_and(and_req, difficulty)
            list_rules = append_rule(and_requirements, "", "", or_resource0, health_req, difficulty, glitched, anchor,
                                  arrival, list_rules)

    elif len(or_req) == 2:
        or_skills0, or_glitch0, or_resource0 = order_or(or_req[0])
        or_skills1, or_glitch1, or_resource1 = order_or(or_req[1])

        # Swaps the two chains if it is more efficient to split the second resource chain
        if len(or_resource0) > len(or_resource1):
            (or_skills0, or_glitch0, or_resource0, or_skills1, or_glitch1,
             or_resource1) = (or_skills1, or_glitch1, or_resource1, or_skills0, or_glitch0, or_resource0)

        for req in or_glitch0:
            for req2 in or_glitch1:  # Case 0 glitched, 1 glitched
                and_req.append(req)
                and_req.append(req2)
                and_requirements, glitched = parse_and(and_req, difficulty)
                and_req.remove(req)
                and_req.remove(req2)
                list_rules = append_rule(and_requirements, "", "", "", health_req, difficulty, True, anchor, arrival,
                                      list_rules)
            if or_skills1:   # Case 0 glitched, 1 skill
                and_req.append(req)
                and_requirements, glitched = parse_and(and_req, difficulty)
                and_req.remove(req)
                list_rules = append_rule(and_requirements, "", or_skills1, "", health_req, difficulty, True, anchor,
                                      arrival, list_rules)
            if or_resource1:  # Case 0 glitched, 1 resource
                and_req.append(req)
                and_requirements, glitched = parse_and(and_req, difficulty)
                and_req.remove(req)
                list_rules = append_rule(and_requirements, "", "", or_resource1, health_req, difficulty, True, anchor,
                                      arrival, list_rules)

        for req in or_resource0:
            for req2 in or_glitch1:  # Case 0 resource, 1 glitched
                and_req.append(req)
                and_req.append(req2)
                and_requirements, glitched = parse_and(and_req, difficulty)
                and_req.remove(req)
                and_req.remove(req2)
                list_rules = append_rule(and_requirements, "", "", "", health_req, difficulty, True, anchor, arrival,
                                      list_rules)
            if or_skills1:  # Case 0 resource, 1 skill
                and_req.append(req)
                and_requirements, glitched = parse_and(and_req, difficulty)
                and_req.remove(req)
                list_rules = append_rule(and_requirements, "", or_skills1, "", health_req, difficulty, glitched, anchor,
                                      arrival, list_rules)
            if or_resource1:  # Case 0 resource, 1 resource
                and_req.append(req)
                and_requirements, glitched = parse_and(and_req, difficulty)
                and_req.remove(req)
                list_rules = append_rule(and_requirements, "", "", or_resource1, health_req, difficulty, glitched, anchor,
                                      arrival, list_rules)

        for req2 in or_glitch1:  # Case 0 skill, 1 glitched
            and_req.append(req2)
            and_requirements, glitched = parse_and(and_req, difficulty)
            and_req.remove(req2)
            list_rules = append_rule(and_requirements, or_skills0, "", "", health_req, difficulty, True, anchor, arrival,
                                  list_rules)
        if or_skills1:  # Case 0 skill, 1 skill
            and_requirements, glitched = parse_and(and_req, difficulty)
            list_rules = append_rule(and_requirements, or_skills0, or_skills1, "", health_req, difficulty, glitched, anchor,
                                  arrival, list_rules)
        if or_resource1:  # Case 0 skill, 1 resource
            and_requirements, glitched = parse_and(and_req, difficulty)
            list_rules = append_rule(and_requirements, or_skills0, "", or_resource1, health_req, difficulty, glitched, anchor,
                                  arrival, list_rules)


def write_files() -> None:
    """Write the extracted data into output files."""
    # TODO Add a file for ER data.
    ent_txt = header + "\n" + "entrance_table = [\n"
    for entrance in entrances:
        ent_txt += f"    \"{entrance}\",\n"
    ent_txt = ent_txt[:-2]
    ent_txt += "\n    ]\n"

    ref_txt = header + "\n" + "refills = {  # key: region name. List: [health restored, energy restored, refill type]\n"
    ref_txt += "    # For refill type: 0 is no refill, 1 is Checkpoint, 2 is Full refill.\n"
    for region, info in refills.items():
        ref_txt += f"    \"{region}\": {info},\n"
    ref_txt = ref_txt[:-2]
    ref_txt += ("\n    }\n\n"
                "refill_events = [\n")
    for refill_name in refill_events:
        ref_txt += f"    \"{refill_name}\",\n"
    ref_txt = ref_txt[:-2]
    ref_txt += "\n    ]\n"

    with open("Rules.py", "w") as w_file:
        for j in range(7):
            w_file.write(list_rules[j])
        print("The file `Rules.py` has been successfully created.")
    with open("Entrances.py", "w") as w_file:
        w_file.write(ent_txt)
        print("The file `Entrances.py` has been successfully created.")
    with open("Refills.py", "w") as w_file:
        w_file.write(ref_txt)
        print("The file `Refills.py` has been successfully created.")

# %% Main script

with open("./areasv2.wotw", "r") as file:
    source_text = file.readlines()

# Moki, Gorlek, Kii and Unsafe rules respectively
moki = (header + imports + "from worlds.generic.Rules import add_rule\n\n\n"
     "def set_moki_rules(world, player, options):\n"
     "    \"\"\"Moki (or easy, default) rules.\"\"\"\n")
gorlek = ("\n\ndef set_gorlek_rules(world, player, options):\n"
     "    \"\"\"Gorlek (or medium) rules.\"\"\"\n")
gorlek_glitch = ("\n\ndef set_gorlek_glitched_rules(world, player, options):\n"
      "    \"\"\"Gorlek (or medium) rules with glitches\"\"\"\n")
kii = ("\n\ndef set_kii_rules(world, player, options):\n"
     "    \"\"\"Kii (or hard) rules\"\"\"\n")
kii_glitch = ("\n\ndef set_kii_glitched_rules(world, player, options):\n"
      "    \"\"\"Kii (or hard) rules with glitches.\"\"\"\n")
unsafe = ("\n\ndef set_unsafe_rules(world, player, options):\n"
     "    \"\"\"Unsafe rules.\"\"\"\n")
unsafe_glitch = ("\n\ndef set_unsafe_glitched_rules(world, player, options):\n"
      "    \"\"\"Unsafe rules with glitches.\"\"\"\n")

# Store the parsed text for each difficulty
list_rules: list[str] = [moki, gorlek, gorlek_glitch, kii, kii_glitch, unsafe, unsafe_glitch]
# Store the entrance names
entrances: list[str] = []
# Contain the refill info per region in a tuple: (health, energy, type)
refills: dict[str, tuple[int, int, int]] = {}
refill_events: list[str] = []  # Store all the names given to the refill events.

# Variables
indent = 0  # Number of indents
anchor = ""  # Name of the current anchor
glitched = False  # Whether the current path involves glitches
arrival = ""  # Name of the connected anchor for a connection
difficulty = 0  # Difficulty of the path
req = ""  # Full requirement
req1 = ""  # Requirements from first indent
req2 = ""  # Requirements from second indent
req3 = ""  # Requirements from third indent
req4 = ""  # Requirements from fourth indent
req5 = ""
refill_type = ""  # Refill type (energy, health, checkpoint or full)
path_type = ""  # Type of the path (connection, pickup, refill)
path_name = ""  # Name of the location/region/event accessed by the path
should_convert = False  # If True, convert is called to create a rule

convert_diff = {"moki": 0, "gorlek": 1, "kii": 3, "unsafe": 5}

for i, line in enumerate(source_text):  # Line number is only used for debug
    should_convert = False  # Reset the flag to false

    ## Parse the line text
    m = r_comment.search(line)  # Remove the comments
    if m:
        line = line[:m.start()]
    m = r_trailing.search(line)  # Remove the trailing spaces
    if m:
        line = line[:m.start()]
    if line == "":
        continue

    m = r_indent.match(line)  # Count the indents
    if m is None:
        indent = 0
    else:
        indent = (m.end() + 1) // 2
        line = line[m.end():]  # Remove the indents from the text

    if indent == 0:  # Always anchor, except for requirement or region (which are ignored)
        if "anchor" in line:
            name = try_group(r_colon, line, 1, -1)
            s = r_indent.search(name)
            if s:
                anchor = name[:s.start()]
            else:
                anchor = name
            refills.setdefault(anchor, (0, 0, 0))
        else:
            anchor = ""

    # TODO manage door
    elif indent == 1:
        if not anchor:  # Only happens with `requirement:` or `region`, ignore it
            continue
        if "nospawn" in line or "tprestriction" in line:  # TODO: manage these if spawn anywhere implemented
            continue
        path_type = try_group(r_type, line, end=-1)  # Connection type
        if path_type not in ("conn", "state", "pickup", "refill", "quest"):
            raise ValueError(f"{path_type} (line {i}) is not an appropriate path type.\n\"{line}\"")
        if path_type == "refill":
            if ":" in line:
                path_name = try_group(r_name, line, 1, -1)  # Checkpoint, Full, Energy=x...
                refill_type, refills, refill_events = conv_refill(path_name, anchor, refills, refill_events)
            else:
                path_name = try_group(r_refill, line, 1)  # Checkpoint, Full, Energy=x...
                refill_type, refills, refill_events = conv_refill(path_name, anchor, refills, refill_events)
                should_convert = True
                req1 = "free"
        else:
            path_name = try_group(r_name, line, 1, -1)  # Name

        if "free" in line:
            should_convert = True
            req1 = "free"
    # TODO cases id, target, enter
    elif indent == 2:  # When not a door, this contains the path difficulty
        if not anchor:  # Only happens with `requirement:` or `region`, ignore it
            continue
        path_diff = try_group(r_difficulty, line, end=-1)  # moki, gorlek, kii, unsafe
        difficulty = convert_diff[path_diff]
        req2 = line[try_end(r_difficulty, line):]  # Can be empty

    # TODO holds difficulty in case of a door
    elif indent == 3:
        if not anchor:  # Only happens with `requirement:` or `region`, ignore it
            continue
        if line[-1] == ":":
            req3 = line[:-1]
        else:
            req3 = line
            should_convert = True

    elif indent == 4:
        if not anchor:  # Only happens with `requirement:` or `region`, ignore it
            continue
        if line[-1] == ":":
            req4 = line[:-1]
        else:
            req4 = line
            should_convert = True

    elif indent == 5:
        if not anchor:  # Only happens with `requirement:` or `region`, ignore it
            continue
        req5 = line
        should_convert = True

    else:
        raise NotImplementedError(f"Too many indents ({indent}) on line {i}.\n{line}")

    if should_convert:
        req = req1
        if indent >= 2:
            req += req2
        if indent >= 3:
            req += req3
        if indent >= 4:
            req += req4
        if indent >= 5:
            req += req5
        convert()

write_files()

    ## Convert the parsed line into lists of requirements
