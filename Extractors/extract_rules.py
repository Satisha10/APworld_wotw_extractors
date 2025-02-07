"""
Converts an areas.wotw file into a set_rules function.

Run `parse_rules()` to extract the rules from the `areas.wotw` file.
See https://github.com/ori-community/wotw-seedgen/tree/main/wotw_seedgen to get this file.
"""

from typing import Dict, List
import os
import re
from collections import Counter

# %% Data and global variables

# Enemy data
ref_en = {"Mantis": (32, ["Free"]),
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

name_convert: Dict[str, str] = {  # Translation of the item names
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
}


# Regular expressions used for parsing
com = re.compile(" *#")  # Detects comments
sp = re.compile("^ *")  # Used for indents
col = re.compile(" .*:")  # name between space and colon
tra = re.compile(" *$")  # Trailing space
sep = re.compile(" at ")
typ = re.compile("^ {2}[a-z]+ ")  # Detects the type of the path
nam = re.compile(" [a-zA-Z.=0-9]+:")  # Name of the object
dif = re.compile("^[a-z]+, ")  # extracts the difficulty of the path
ref = re.compile("[a-zA-Z=0-9]+$")  # Extracts the refill type if it has no colon

en_skills = ["Bow", "Grenade", "Flash", "Sentry", "Shuriken", "Spear", "Blaze"]  # Skills that require energy

# Things that require a specific treatment
combat_name = ["BreakWall", "Combat", "Boss"]

# Skills that can be used infinitely (note: Regenerate is here because of how the logic is written)
inf_skills = ["Sword", "Double Jump", "Regenerate", "Dash", "Bash", "Grapple", "Glide", "Flap", "Water Dash",
              "Burrow", "Launch", "Clean Water", "Water Breath", "Hammer", "free"]

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
            "SpearJump": ["Spear"]}

# Glitches that can be used infinitely (and only use one skill)
inf_glitches = {"RemoveKillPlane": "free",
                "HammerBreak": "Hammer",
                "LaunchSwap": "Launch",
                "FlashSwap": "Flash",
                "GrenadeJump": "Grenade",
                "GrenadeCancel": "Grenade",
                "BowCancel": "Bow",
                "PauseHover": "free",
                "GlideJump": "Glide"}

# Glitches that can be used infinitely, and use two skills
other_glitches = ["WaveDash", "HammerJump", "SwordJump", "GlideHammerJump"]


# %% Text initialisations

header = ("\"\"\"\n"
          "Generated file, do not edit manually.\n\n"
          "See https://github.com/Satisha10/APworld_wotw_extractors for the code.\n"
          "Generated with `extract_rules.py` by running `parse_rules()`.\n"
          "\"\"\"\n\n\n")

imports = "from .Rules_Functions import *\n\n"

# %% Functions for extracting rules


def parse_rules(override=False):
    """Parse an areas.wotw file, and creates `Rules.py` containing the rules, and `Entrances.py` for the entrances."""
    if os.path.exists("./Rules.py"):
        if override:
            print("Warning: File `Rules.py` replaced")
        else:
            raise FileExistsError("The file `Rules.py` already exists. Use `override=True` to override it.")
    if os.path.exists("./Entrances.py"):
        if override:
            print("Warning: File `Entrances.py` replaced")
        else:
            raise FileExistsError("The file `Entrances.py` already exists. Use `override=True` to override it.")
    if os.path.exists("./Refills.py"):
        if override:
            print("Warning: File `Refills.py` replaced")
        else:
            raise FileExistsError("The file `Refills.py` already exists. Use `override=True` to override it.")

    with open("./areas.wotw", "r") as file:
        temp = file.readlines()

    # Moki, Gorlek, Kii and Unsafe rules respectively
    M = (header + imports + "from worlds.generic.Rules import add_rule\n\n\n"
         "def set_moki_rules(world, player, options):\n"
         "    \"\"\"Moki (or easy, default) rules.\"\"\"\n")
    G = ("\n\ndef set_gorlek_rules(world, player, options):\n"
         "    \"\"\"Gorlek (or medium) rules.\"\"\"\n")
    Gg = ("\n\ndef set_gorlek_glitched_rules(world, player, options):\n"
          "    \"\"\"Gorlek (or medium) rules with glitches\"\"\"\n")
    K = ("\n\ndef set_kii_rules(world, player, options):\n"
         "    \"\"\"Kii (or hard) rules\"\"\"\n")
    Kg = ("\n\ndef set_kii_glitched_rules(world, player, options):\n"
          "    \"\"\"Kii (or hard) rules with glitches.\"\"\"\n")
    U = ("\n\ndef set_unsafe_rules(world, player, options):\n"
         "    \"\"\"Unsafe rules.\"\"\"\n")
    Ug = ("\n\ndef set_unsafe_glitched_rules(world, player, options):\n"
          "    \"\"\"Unsafe rules with glitches.\"\"\"\n")

    L_rules: List[str] = [M, G, Gg, K, Kg, U, Ug]
    entrances = []
    refills = {}  # Contains the refill info per region as a list: [health, energy, type]
    refill_events = []  # Stores all the names given to the refill events.

    # Variables
    anc = ""  # Name of the current anchor
    diff = 0  # Difficulty of the path
    req2 = ""  # Requirements from second indent
    req3 = ""  # Requirements from third indent
    req4 = ""  # Requirements from fourth indent
    ref_type = ""  # Refill type (energy, health, checkpoint or full)
    p_type = ""  # Type of the path
    p_name = ""  # Name of the location/region/event accessed by the path

    c_diff = {"moki": 0, "gorlek": 1, "kii": 3, "unsafe": 5}

    for i, p in enumerate(temp):  # line number is only used for debug
        m = com.search(p)  # Removes the comments
        if m:
            p = p[:m.start()]
        m = tra.search(p)  # Removes the trailing spaces
        if m:
            p = p[:m.start()]
        if p == "":
            continue

        m = sp.match(p)  # Counts the indents
        if m is None:
            ind = 0
        else:
            ind = (m.end() + 1) // 2

        if ind == 0:
            if "anchor" in p:
                name = col.search(p).group()[1:-1]
                s = sep.search(name)
                if s:
                    anc = name[:s.start()]
                else:
                    anc = name
                refills.setdefault(anc, [0, 0, 0])
            else:
                anc = ""

        elif ind == 1:
            if not anc:
                continue
            if "nospawn" in p or "tprestriction" in p:  # TODO: manage these if spawn anywhere implemented
                continue
            p_type = typ.search(p).group()[2:-1]  # Connection type
            if p_type not in ("conn", "state", "pickup", "refill", "quest"):
                raise ValueError(f"{p_type} (line {i}) is not an appropriate path type.\n\"{p}\"")
            if p_type == "refill":
                if ":" in p:
                    p_name = nam.search(p).group()[1:-1]
                    ref_type, refills, refill_events = conv_refill(p_name, anc, refills, refill_events)
                else:
                    p_name = ref.search(p).group()
                    ref_type, refills, refill_events = conv_refill(p_name, anc, refills, refill_events)
                    convert(anc, p_type, p_name, L_rules, entrances, ref_type, 0, "free")
            else:
                p_name = nam.search(p).group()[1:-1]  # Name

            if "free" in p:
                L_rules, entrances = convert(anc, p_type, p_name, L_rules, entrances, ref_type, 0, "free")

        elif ind == 2:
            if not anc:
                continue
            if p[-1] == ":":
                if p[4:] in ("moki:", "gorlek:", "kii:", "unsafe:"):
                    diff = c_diff[p[4:-1]]
                    req2 = ""
                elif "moki" in p or "gorlek" in p or "kii" in p or "unsafe" in p:
                    s = dif.search(p[4:])
                    diff = c_diff[s.group()[:-2]]
                    req2 = p[s.end() + 4:-1]
                else:
                    raise ValueError(f"Input on line {i} is invalid.\n\"{p}\"")

            elif ": " in p:
                if "moki:" in p or "gorlek:" in p or "kii:" in p or "unsafe:" in p:
                    start = p.find(": ")
                    diff = c_diff[p[4:start]]
                    req = p[start + 2:]
                    L_rules, entrances = convert(anc, p_type, p_name, L_rules, entrances, ref_type, diff, req)
                else:
                    s = dif.search(p[4:])
                    diff = c_diff[s.group()[:-2]]
                    req = p[s.end() + 4:]
                    req = req.replace(":", ",")
                    L_rules, entrances = convert(anc, p_type, p_name, L_rules, entrances, ref_type, diff, req)
            else:
                raise ValueError(f"Input on line {i} is invalid.\n\"{p}\"")

        elif ind == 3:
            if not anc:
                continue
            if p[-1] == ":":
                req3 = p[6:-1]
            else:
                req3 = ""
                if req2:
                    req = req2 + ", " + p[6:]
                else:
                    req = p[6:]
                L_rules, entrances = convert(anc, p_type, p_name, L_rules, entrances, ref_type, diff, req)

        elif ind == 4:
            if not anc:
                continue
            if p[-1] == ":":
                req4 = p[8:-1]
            else:
                req4 = ""
                req = ""
                if req2:
                    req += req2 + ", "
                if req3:
                    req += req3 + ", "
                req += p[8:]
                L_rules, entrances = convert(anc, p_type, p_name, L_rules, entrances, ref_type, diff, req)

        elif ind == 5:
            if not anc:
                continue
            req = ""
            if req2:
                req += req2 + ", "
            if req3:
                req += req3 + ", "
            if req4:
                req += req4 + ", "
            req += p[10:]
            L_rules, entrances = convert(anc, p_type, p_name, L_rules, entrances, ref_type, diff, req)

        else:
            raise NotImplementedError(f"Too many indents ({ind}) on line {i}.\n{p}")

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
    for name in refill_events:
        ref_txt += f"    \"{name}\",\n"
    ref_txt = ref_txt[:-2]
    ref_txt += "\n    ]\n"

    with open("Rules.py", "w") as file:
        for i in range(7):
            file.write(L_rules[i])
        print("The file `Rules.py` has been successfully created.")
    with open("Entrances.py", "w") as file:
        file.write(ent_txt)
        print("The file `Entrances.py` has been successfully created.")
    with open("Refills.py", "w") as file:
        file.write(ref_txt)
        print("The file `Refills.py` has been successfully created.")


def convert(anc: str, p_type: str, p_name: str, L_rules: List[str], entrances: List[str], ref_type: str, diff: int,
            req: str) -> (List[str], List[str]):
    """
    Convert the data given by the arguments into an add_rule function, and add it to the right difficulty.

    Return the updated L_rules and entrances lists.
    anc: name of the starting anchor
    p_type: type of the element accessed by the rules (anchor, state, refill or item)
    p_name: name of the element accessed by the rules
    ref_type: type of the refill (full, checkpoint, health or energy)
    diff: difficulty of the path
    req: requirements to access the element
    """
    health_req = 0  # Requirement when entering a new area

    and_req = []
    or_req = []

    if p_type == "conn" and "." in p_name:  # Gets the requirements when entering a new area.
        s = p_name.find(".")
        f_area = p_name[:s]
        if "." in anc:
            s = anc.find(".")
            i_area = anc[:s]  # Extracts the name of the starting area
        else:
            i_area = ""
        if i_area != f_area:
            regen, health_req = req_area(f_area, diff)
            if regen:
                and_req.append("Regenerate")

    if p_type == "refill":
        p_name = ref_type + anc

    arrival = p_name
    conn_name = f"{anc}_to_{p_name}"
    if conn_name not in entrances:
        entrances.append(conn_name)

    s_req = req.split(", ")
    for elem in s_req:
        if " OR " in elem:
            or_req.append(elem.split(" OR "))
        else:
            and_req.append(elem)

    if len(or_req) == 0:
        and_requirements, glitched = parse_and(and_req, diff)
        L_rules = append_rule(and_requirements, "", "", "", health_req, diff, glitched, anc, arrival,
                              p_type, L_rules)

    elif len(or_req) == 1:
        or_skills0, or_glitch0, or_resource0 = order_or(or_req[0])

        for req in or_glitch0:
            and_req.append(req)
            and_requirements, glitched = parse_and(and_req, diff)
            and_req.remove(req)
            L_rules = append_rule(and_requirements, "", "", "", health_req, diff, True, anc, arrival,
                                  p_type, L_rules)
        if or_skills0:
            and_requirements, glitched = parse_and(and_req, diff)
            L_rules = append_rule(and_requirements, or_skills0, "", "", health_req, diff, glitched, anc,
                                  arrival, p_type, L_rules)
        if or_resource0:
            and_requirements, glitched = parse_and(and_req, diff)
            L_rules = append_rule(and_requirements, "", "", or_resource0, health_req, diff, glitched, anc,
                                  arrival, p_type, L_rules)

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
                and_requirements, glitched = parse_and(and_req, diff)
                and_req.remove(req)
                and_req.remove(req2)
                L_rules = append_rule(and_requirements, "", "", "", health_req, diff, True, anc, arrival,
                                      p_type, L_rules)
            if or_skills1:   # Case 0 glitched, 1 skill
                and_req.append(req)
                and_requirements, glitched = parse_and(and_req, diff)
                and_req.remove(req)
                L_rules = append_rule(and_requirements, "", or_skills1, "", health_req, diff, True, anc,
                                      arrival, p_type, L_rules)
            if or_resource1:  # Case 0 glitched, 1 resource
                and_req.append(req)
                and_requirements, glitched = parse_and(and_req, diff)
                and_req.remove(req)
                L_rules = append_rule(and_requirements, "", "", or_resource1, health_req, diff, True, anc,
                                      arrival, p_type, L_rules)

        for req in or_resource0:
            for req2 in or_glitch1:  # Case 0 resource, 1 glitched
                and_req.append(req)
                and_req.append(req2)
                and_requirements, glitched = parse_and(and_req, diff)
                and_req.remove(req)
                and_req.remove(req2)
                L_rules = append_rule(and_requirements, "", "", "", health_req, diff, True, anc, arrival,
                                      p_type, L_rules)
            if or_skills1:  # Case 0 resource, 1 skill
                and_req.append(req)
                and_requirements, glitched = parse_and(and_req, diff)
                and_req.remove(req)
                L_rules = append_rule(and_requirements, "", or_skills1, "", health_req, diff, glitched, anc,
                                      arrival, p_type, L_rules)
            if or_resource1:  # Case 0 resource, 1 resource
                and_req.append(req)
                and_requirements, glitched = parse_and(and_req, diff)
                and_req.remove(req)
                L_rules = append_rule(and_requirements, "", "", or_resource1, health_req, diff, glitched, anc,
                                      arrival, p_type, L_rules)

        for req2 in or_glitch1:  # Case 0 skill, 1 glitched
            and_req.append(req2)
            and_requirements, glitched = parse_and(and_req, diff)
            and_req.remove(req2)
            L_rules = append_rule(and_requirements, or_skills0, "", "", health_req, diff, True, anc, arrival,
                                  p_type, L_rules)
        if or_skills1:  # Case 0 skill, 1 skill
            and_requirements, glitched = parse_and(and_req, diff)
            L_rules = append_rule(and_requirements, or_skills0, or_skills1, "", health_req, diff, glitched, anc,
                                  arrival, p_type, L_rules)
        if or_resource1:  # Case 0 skill, 1 resource
            and_requirements, glitched = parse_and(and_req, diff)
            L_rules = append_rule(and_requirements, or_skills0, "", or_resource1, health_req, diff, glitched, anc,
                                  arrival, p_type, L_rules)

    return L_rules, entrances


def combat_req(need: str, value: str) -> (List[List[int | str]], List[str]):
    """Parse the combat requirement with the given enemies, returns the damage and type of combat."""
    damage = []
    dangers = []

    if need == "Combat":
        enemies = value.split("+")

        for elem in enemies:
            amount = 1
            if "EnergyRefill" in elem:
                amount = int(elem[0])
                damage.append([amount, "Refill"])
                continue
            if elem[1] == "x":
                amount = int(elem[0])
                elem = elem[2:]
            danger = ref_en[elem][1]
            damage_type = "Combat"
            damage += ([[ref_en[elem][0], damage_type]] * amount)
            for dan in danger:
                dan = "Combat." + dan
                if dan not in dangers and dan != "Combat.Free":
                    dangers.append(dan)

    elif need == "Boss":
        damage.append([int(value), "Boss"])

    elif need == "BreakWall":
        damage.append([int(value), "Wall"])

    return damage, dangers


def parse_and(and_req: List[str], diff: int) -> (List, bool):
    """Parse the list of requirements in the `and` chain, and returns the processed information."""
    and_skills = []  # Stores inf_skills
    and_other = []  # Stores other requirements (that often have their own event)
    damage_and = []  # Stores damage boosts
    combat_and = []  # Stores combat damage to inflict, as a list of each damage to do + the type of combat
    # The type of combat can be ranged, wall
    en_and = []  # Stores energy weapon used
    glitched = False

    for requirement in and_req:
        if "=" in requirement:
            elem, value = requirement.split("=")
        else:
            if requirement in name_convert.keys():
                requirement = name_convert[requirement]
            elem = requirement
            value = 0

        if elem in other_glitches:  # Handle the glitches
            glitched = True
            and_other.append(elem)
        elif elem in inf_glitches.keys():
            glitched = True
            req = inf_glitches[elem]
            if req not in and_skills and req != "free":
                and_skills.append(req)
        elif elem in glitches.keys():
            glitched = True
            value = int(value)
            req = glitches[elem]
            for i, skill in enumerate(req):
                if elem == "ShurikenBreak" and diff == 5:
                    combat_and.append([value * 2, "Shuriken"])
                elif elem == "ShurikenBreak":
                    combat_and.append([value * 3, "Shuriken"])
                elif elem == "SentryBreak":
                    combat_and.append([value * 6.25, "Shuriken"])
                elif i == len(req) - 1:
                    en_and += [skill] * value
                else:
                    if req not in and_skills and req != "free":
                        and_skills.append(req)

        elif elem in inf_skills:
            if elem not in and_skills and elem != "free":
                and_skills.append(elem)
        elif elem in en_skills:
            value = int(value)
            en_and += [elem] * value
        elif elem == "Damage":
            value = int(value)
            damage_and.append(value)
        elif elem in combat_name:
            deal_damage, danger = combat_req(elem, value)
            combat_and += deal_damage
            and_other += danger
        else:  # Case of an event, or keystone, or spirit light, or ore
            and_other.append(requirement)
    return (and_skills, and_other, damage_and, combat_and, en_and), glitched


def order_or(or_chain: List[str]) -> (List[str], List[str], List[str]):
    """Parse the list of requirements in the `or` chain, and categorize them."""
    or_skills = []  # Stores inf_skills
    or_glitch = []  # Stores the glitches
    or_resource = []  # Stores requirements that need resources

    for requirement in or_chain:
        if "=" in requirement:
            elem = requirement.split("=")[0]
        else:
            if requirement in name_convert.keys():
                requirement = name_convert[requirement]
            elem = requirement

        if elem in other_glitches or elem in inf_glitches.keys() or elem in glitches.keys():  # Handle the glitches
            or_glitch.append(requirement)

        elif elem in inf_skills:
            or_skills.append(requirement)
        elif elem in en_skills or elem in combat_name or elem == "Damage":
            or_resource.append(requirement)
        else:  # Case of an event
            or_skills.append(requirement)
    return or_skills, or_glitch, or_resource


def append_rule(and_requirements: List[List], or_skills0: str | List[str], or_skills1: str | List[str],
                or_resource: str | List[str], health: int, diff: int, glitched: bool, anc: str, arrival: str,
                p_type: str, L_rules: List[str]) -> List[str]:
    """
    Add the text to the rules list. Returns the updated L_rules.

    and_requirements contains requirements that must all be satisfied.
    or_skills0 contains a chain of skills, any can be satisfied. Same for or_skills1
    or_resource contains requirements that can cost resources. Any can be satisfied.
    health is the health requirement when entering a new area
    diff is the path difficulty
    glitched indicates if the path includes glitches
    anc is the name of the starting region
    arrival is the name of the connected region
    p_type is the type of the path (connection, or location/event)
    L_rules is the list containing the parsed data. It is modified and returned at the end
    """
    and_skills, and_other, damage_and, combat_and, en_and = and_requirements
    energy = []

    start_txt = f"    add_rule(world.get_entrance(\"{anc}_to_{arrival}\", player), lambda s: "
    req_txt = ""

    if p_type == "refill":
        # refill_type = arrival[0]
        arrival = anc

    # else:
    #     refill_type = ""

    if and_skills:
        temp_txt = ""
        if len(and_skills) == 1:
            temp_txt = f"s.has(\"{and_skills[0]}\", player)"
        else:
            for elem in and_skills:
                if temp_txt:
                    temp_txt += f", \"{elem}\""
                else:
                    temp_txt += f"s.has_all((\"{elem}\""
            temp_txt += "), player)"
        if req_txt:
            req_txt += " and " + temp_txt
        else:
            req_txt += temp_txt

    if and_other:
        for elem in and_other:
            if "Keystone" in elem:
                temp_txt = "can_keystones(s, player)"
            elif "=" in elem:
                name, amount = elem.split("=")
                amount = int(amount)
                if name == "SpiritLight":
                    if amount == 1200:  # Case of a shop item
                        temp_txt = "s.count(\"200 Spirit Light\", player) >= 6"
                    else:  # Case of a map from Lupo
                        temp_txt = "can_buy_map(s, player)"
                elif name == "Ore":
                    temp_txt = f"s.count(\"Ore\", player) >= {amount}"
                else:
                    raise ValueError(f"Invalid input: {elem}")
            else:
                temp_txt = f"s.has(\"{elem}\", player)"
            if req_txt:
                req_txt += " and " + temp_txt
            else:
                req_txt += temp_txt

    if or_skills0:
        temp_txt = ""
        if len(or_skills0) == 1:
            temp_txt = f"s.has(\"{or_skills0[0]}\", player)"
        else:
            for elem in or_skills0:
                if temp_txt:
                    temp_txt += f", \"{elem}\""
                else:
                    temp_txt += f"s.has_any((\"{elem}\""
            temp_txt += "), player)"
        if req_txt:
            req_txt += " and " + temp_txt
        else:
            req_txt += temp_txt

    if or_skills1:
        temp_txt = ""
        if len(or_skills1) == 1:
            temp_txt = f"s.has(\"{or_skills1[0]}\", player)"
        else:
            for elem in or_skills1:
                if temp_txt:
                    temp_txt += f", \"{elem}\""
                else:
                    temp_txt += f"s.has_any((\"{elem}\""
            temp_txt += "), player)"
        if req_txt:
            req_txt += " and " + temp_txt
        else:
            req_txt += temp_txt

    if health:
        if req_txt:
            req_txt += " and " + f"has_health({health}, s, player)"
        else:
            req_txt += f"has_health({health}, s, player)"

    if en_and:
        counter = Counter(en_and)
        for weapon in en_skills:
            amount = counter[weapon]
            if amount != 0:
                energy.append([weapon, amount])

    or_costs = []  # List of list, each element is a possibility. The first element of the lists codes the type of cost.
    for requirement in or_resource:
        if "=" in requirement:
            elem, value = requirement.split("=")
        else:
            elem = requirement
            value = 0
        if elem == "Combat":
            deal_damage, danger = combat_req(elem, value)
            or_costs.append([0, deal_damage, danger])
        elif elem in en_skills:
            or_costs.append([1, elem, int(value)])
        elif elem == "Damage":
            or_costs.append([2, int(value)])

    if damage_and or combat_and or en_and or or_costs:
        # temp_txt = (f"cost_all(s, player, ref_resource, options, \"{anc}\", \"{arrival}\", {damage_and}, {energy}, "
        #             f"{combat_and}, {or_costs}, \"{refill_type}\"")
        temp_txt = (f"cost_all(s, player, options, \"{anc}\", {damage_and}, {energy}, "
                    f"{combat_and}, {or_costs})")
        # if p_type in ("conn", "refill"):
        #     temp_txt += ", True)"  # Indicates if the resource table has to be updated
        # else:
        #     temp_txt += ", False)"
        if req_txt:
            req_txt += " and " + temp_txt
        else:
            req_txt += temp_txt

    # elif p_type in ("conn", "refill"):
    #     if req_txt:  # Indicates that the resource table has to be updated, but the path does not consume resource
    #         req_txt += " and " + f"no_cost(\"{anc}\", \"{arrival}\", s, player, ref_resource, \"{refill_type}\")"
    #     else:
    #         req_txt += f"no_cost(\"{anc}\", \"{arrival}\", s, player, ref_resource, \"{refill_type}\")"

    if req_txt:
        tot_txt = start_txt + req_txt + ", \"or\")\n"
    else:
        tot_txt = start_txt + "True, \"or\")\n"

    if glitched:
        diff += 1

    L_rules[diff] += tot_txt

    return L_rules


def conv_refill(p_name: str, anc: str, refills: Dict[str, List[int]],
                refill_events: List[str]) -> (str, Dict[str, List[int]], List[str]):
    """Return the refill type (to add before the region name) and updates the data tables."""
    current = refills[anc]
    if "=" in p_name:
        value = int(p_name[-1])
        if p_name[:-2] == "Health":
            if current[0] == 0:
                refills.update({anc: [value, current[1], current[2]]})
                refill_events.append(f"H.{anc}")
            return "H.", refills, refill_events
        if p_name[:-2] == "Energy":
            if current[1] == 0:
                refills.update({anc: [current[0], value, current[2]]})
                refill_events.append(f"E.{anc}")
            return "E.", refills, refill_events
    if p_name == "Checkpoint":
        refills.update({anc: [current[0], current[1], 1]})
        refill_events.append(f"C.{anc}")
        return "C.", refills, refill_events
    if p_name == "Full":
        refills.update({anc: [current[0], current[1], 2]})
        refill_events.append(f"F.{anc}")
        return "F.", refills, refill_events
    raise ValueError(f"{p_name} is not a valid refill type (at anchor {anc}).")


def req_area(area: str, diff: int) -> (bool, str):
    """
    Return the requirement for entering an area.

    Returns if Regenerate is needed, and the amount of health required.
    """
    M_dat = {"MidnightBurrows": (25, False), "EastHollow": (20, False), "WestHollow": (20, False),
             "WestGlades": (20, False), "OuterWellspring": (25, False), "InnerWellspring": (25, False),
             "WoodsEntry": (40, True), "WoodsMain": (40, True), "LowerReach": (40, True), "UpperReach": (40, True),
             "UpperDepths": (40, True), "LowerDepths": (40, True), "PoolsApproach": (25, True), "EastPools": (40, True),
             "UpperPools": (40, True), "WestPools": (40, True), "LowerWastes": (50, True), "UpperWastes": (50, True),
             "WindtornRuins": (50, True), "WeepingRidge": (60, True), "WillowsEnd": (60, True)}

    if area in (None, "MarshSpawn", "HowlsDen", "MarshPastOpher", "GladesTown"):
        return False, 0
    if diff >= 5:  # Unsafe
        return False, 0
    if diff >= 1:
        if M_dat[area][1]:  # Kii, Gorlek
            return True, 0
        return False, 0

    if M_dat[area][1]:  # Moki
        return True, M_dat[area][0]
    return False, M_dat[area][0]
