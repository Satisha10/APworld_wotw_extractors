"""
Converts an areas.wotw file into a set_rules function.

Run `parse_rules()` to extract the rules from the `areas.wotw` file.
See https://github.com/ori-community/wotw-seedgen/tree/main/wotw_seedgen to get this file.
"""

import os
import re
from typing import Pattern, NamedTuple
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

# %% Main script

with open("./areasv2.wotw", "r") as file:
    text = file.readlines()

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
refills: dict[str, tuple[int, int, int]] = {}  # TODO enum type ?
refill_events: list[str] = []  # Store all the names given to the refill events.

# Variables
indent = 0  # Number of indents
anchor = ""  # Name of the current anchor
glitched = False  # Whether the current path involves glitches
arrival = ""  # Name of the connected anchor for a connection
difficulty = 0  # Difficulty of the path
req2 = ""  # Requirements from second indent
req3 = ""  # Requirements from third indent
req4 = ""  # Requirements from fourth indent
refill_type = ""  # Refill type (energy, health, checkpoint or full)
path_type = ""  # Type of the path (connection, pickup, refill)
path_name = ""  # Name of the location/region/event accessed by the path

convert_diff = {"moki": 0, "gorlek": 1, "kii": 3, "unsafe": 5}

for i, line in enumerate(text):  # Line number is only used for debug
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
                convert(anchor, path_type, path_name, list_rules, entrances, refill_type, 0, "free")
        else:
            path_name = try_group(r_name, line, 1, -1)  # Name

        if "free" in line:
            list_rules, entrances = convert(anchor, path_type, path_name, list_rules, entrances, refill_type, 0, "free")
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
            req3 = ""
            if req2:
                req = req2 + ", " + line
            else:
                req = line
            list_rules, entrances = convert(anchor, path_type, path_name, list_rules, entrances, refill_type, difficulty, req)

    elif indent == 4:
        if not anchor:  # Only happens with `requirement:` or `region`, ignore it
            continue
        if line[-1] == ":":
            req4 = line[:-1]
        else:
            req4 = ""
            req = ""
            if req2:
                req += req2 + ", "
            if req3:
                req += req3 + ", "
            req += line
            list_rules, entrances = convert(anchor, path_type, path_name, list_rules, entrances, refill_type, difficulty, req)

    elif indent == 5:
        if not anchor:  # Only happens with `requirement:` or `region`, ignore it
            continue
        req = ""
        if req2:
            req += req2 + ", "
        if req3:
            req += req3 + ", "
        if req4:
            req += req4 + ", "
        req += line
        list_rules, entrances = convert(anchor, path_type, path_name, list_rules, entrances, refill_type, difficulty, req)

    else:
        raise NotImplementedError(f"Too many indents ({indent}) on line {i}.\n{line}")
