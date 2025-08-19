"""
Converts an areas.wotw file into a set_rules function.

Run `parse_rules()` to extract the rules from the `areas.wotw` file.
See https://github.com/ori-community/wotw-seedgen/tree/main/wotw_seedgen to get this file.
"""

import re
from typing import Pattern
from collections import Counter

# %% Data and global variables

# TODO rename glitches, can_open_door, change combat, change resource function

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
            "SpearJump": ["Spear"], }

# Glitches that can be used infinitely (and only use one skill)
inf_glitches = {"RemoveKillPlane": "free",
                "HammerBreak": "Hammer",
                "LaunchSwap": "Launch",
                "FlashSwap": "Flash",
                "GrenadeJump": "Grenade",
                "GrenadeCancel": "Grenade",
                "BowCancel": "Bow",
                "PauseHover": "free",
                "GlideJump": "Glide", }

# Glitches that can be used infinitely, and use two skills
other_glitches = {"WaveDash": "can_wavedash(s, player)",
                  "HammerJump": "can_hammerjump(s, player)",
                  "SwordJump": "can_swordjump(s, player)",
                  "GlideHammerJump": "can_glidehammerjump(s, player)", }


# %% Text initialisations

header = ("\"\"\"\n"
          "Generated file, do not edit manually.\n\n"
          "See https://github.com/Satisha10/APworld_wotw_extractors for the code.\n"
          "Generated with `extract_rules.py`.\n"
          "\"\"\"\n\n\n")

imports = ("from .Rules_Functions import *\n"
           "from worlds.generic.Rules import add_rule\n\n"
           "from typing import TYPE_CHECKING\n"
           "if TYPE_CHECKING:\n"
           "    from BaseClasses import MultiWorld\n"
           "    from .Options import WotWOptions\n\n\n")

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


def conv_refill() -> None:
    """Get the refill type (to add before the region name) and update the data tables."""
    global refill_type
    current = refills[anchor]
    if "=" in path_name:
        value = int(path_name[-1])
        if path_name[:-2] == "Health":
            if current[0] == 0:
                refills.update({anchor: (value, current[1], current[2])})
                refill_events.append(f"H.{anchor}")
            refill_type = "H."
        if path_name[:-2] == "Energy":
            if current[1] == 0:
                refills.update({anchor: (current[0], value, current[2])})
                refill_events.append(f"E.{anchor}")
            refill_type = "E."
    elif path_name == "Checkpoint":
        refills.update({anchor: (current[0], current[1], 1)})
        refill_events.append(f"C.{anchor}")
        refill_type = "C."
    elif path_name == "Full":
        refills.update({anchor: (current[0], current[1], 2)})
        refill_events.append(f"F.{anchor}")
        refill_type = "F."
    else:
        raise ValueError(f"{path_name} is not a valid refill type (at anchor {anchor}).")


def convert() -> None:
    """Convert the data given by the arguments into an add_rule function, and add it to the right difficulty."""
    global anchor, path_type, path_name, list_rules, entrances, refill_type, difficulty, req, glitched, health_req
    global and_req, or_req, and_requirements, or_requirements
    global or_skills0, or_skills1, or_resource0, or_resource1, or_glitch0, or_glitch1
    global target_area

    glitched = False

    # Reset the global values
    or_skills0 = []
    or_skills1 = []
    or_resource0 = []
    or_resource1 = []
    or_glitch0 = []
    or_glitch1 = []
    and_requirements = []
    or_requirements = []

    health_req = 0
    and_req = []
    or_req = []

    target_area = ""

    if path_type == "conn" and "." in path_name:  # Gets the requirements when entering a new area.
        dot_position = path_name.find(".")
        f_area = path_name[:dot_position]
        if "." in anchor:
            dot_position = anchor.find(".")
            i_area = anchor[:dot_position]  # Extracts the name of the starting area
        else:
            i_area = ""
        if i_area != f_area:
            target_area = f_area

    if path_type == "refill":
        path_name = refill_type + anchor

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
        parse_and()
        append_rule()

    elif len(or_req) == 1:
        order_or(or_req[0])
        or_skills0, or_glitch0, or_resource0 = or_requirements
        parse_and()
        append_rule()

    elif len(or_req) == 2:  # Two chains of or
        order_or(or_req[0])
        or_skills0, or_glitch0, or_resource0 = or_requirements
        order_or(or_req[1])
        or_skills0, or_glitch0, or_resource0 = or_requirements

        # Swaps the two chains if it is more efficient to split the second resource chain
        if len(or_resource0) > len(or_resource1):
            (or_skills0, or_glitch0, or_resource0, or_skills1, or_glitch1,
             or_resource1) = (or_skills1, or_glitch1, or_resource1, or_skills0, or_glitch0, or_resource0)

        for req in or_glitch0:
            and_req.append(req)
            parse_and()
            and_req.remove(req)
            append_rule()


def write_files() -> None:
    """Write the extracted data into output files."""
    ent_txt = header + "entrance_table: list[str] = [\n"
    for entrance in entrances:
        ent_txt += f"    \"{entrance}\",\n"
    ent_txt = ent_txt[:-2]
    ent_txt += "\n    ]\n"

    ref_txt = header + "refills: dict[str, tuple[int, int, int]] = {  # key: region name. Tuple: [health restored, energy restored, refill type]\n"
    ref_txt += "    # For refill type: 0 is no refill, 1 is Checkpoint, 2 is Full refill.\n"
    for region, info in refills.items():
        ref_txt += f"    \"{region}\": {info},\n"
    ref_txt = ref_txt[:-2]
    ref_txt += ("\n    }\n\n"
                "refill_events: list[str] = [\n")
    for refill_name in refill_events:
        ref_txt += f"    \"{refill_name}\",\n"
    ref_txt = ref_txt[:-2]
    ref_txt += "\n    ]\n"

    door_txt = header + "doors_vanilla: list[tuple[str, str]] = [  # Vanilla door connections\n"
    for door in doors_vanilla:
        door_txt += f"    {door},\n"
    door_txt = door_txt[:-2]
    door_txt += "\n    ]\n\n\n"
    door_txt += "doors_map: dict[str, int] = {  # Mapping to door ID\n"
    for door, value in doors_map.items():
        door_txt += f"    \"{door}\": {value},\n"
    door_txt = door_txt[:-2]
    door_txt += "\n    }\n"

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
    with open("DoorData.py", "w") as w_file:
        w_file.write(door_txt)
        print("The file `DoorData.py` has been successfully created.")


def parse_and() -> None:
    """Parse the list of requirements in the `and` chain, and returns the processed information."""
    and_skills = []  # Stores inf_skills
    and_other = []  # Stores other requirements (that often have their own event)
    damage_and = []  # Stores damage boosts
    combat_and = []  # Stores combat damage to inflict, as a list of each damage to do + the type of combat
    # The type of combat can be ranged, wall
    en_and = []  # Stores energy weapon used
    global glitched, difficulty, and_req
    global and_requirements

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
            current_req = inf_glitches[elem]
            if current_req not in and_skills and current_req != "free":
                and_skills.append(current_req)
        elif elem in glitches.keys():
            glitched = True
            value = int(value)
            current_req = glitches[elem]
            for index, skill in enumerate(current_req):
                if elem == "ShurikenBreak" and difficulty == 5:
                    combat_and.append([value * 2, "Shuriken"])
                elif elem == "ShurikenBreak":
                    combat_and.append([value * 3, "Shuriken"])
                elif elem == "SentryBreak":
                    combat_and.append([value * 6.25, "Shuriken"])
                elif index == len(current_req) - 1:
                    en_and += [skill] * value
                else:
                    if current_req not in and_skills and current_req != "free":
                        and_skills.append(current_req)

        elif requirement in inf_skills:  # Check on requirement to catch the energy skills without the =
            if requirement not in and_skills and requirement != "free":
                and_skills.append(requirement)
        elif elem in en_skills:
            value = int(value)
            en_and += [elem] * value
        elif elem == "Damage":
            value = int(value)
            damage_and.append(value)
        elif elem in combat_name:
            deal_damage, danger = combat_req(elem, value)
            combat_and += deal_damage
            and_skills += danger
        elif "Keystone" in elem or "Ore" in elem or "SpiritLight" in elem:  # Case of an event, or keystone, or spirit light, or ore
            and_other.append(requirement)
        else:  # Case of an event
            and_skills.append(elem)
    and_requirements = (and_skills, and_other, damage_and, combat_and, en_and)  # Update


def combat_req(need: str, value: str) -> list[list[list[int | str]], list[str]]:
    """Parse the combat requirement with the given enemies, return the damage and type of combat."""
    damage: list[list[int | str]] = []
    dangers: list[str] = []

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


def order_or(or_chain: list[str]) -> None:
    """Parse the list of requirements in the `or` chain, and categorize them between skills and resources."""
    global or_requirements

    or_skills = []  # Store inf_skills (skills that don't require energy to use)
    or_glitch = []  # Store the glitches
    or_resource = []  # Store requirements that need resources

    for requirement in or_chain:
        if "=" in requirement:
            elem = requirement.split("=")[0]
        else:
            if requirement in name_convert.keys():
                requirement = name_convert[requirement]
            elem = requirement

        if elem in other_glitches or elem in inf_glitches.keys() or elem in glitches.keys():  # Handle the glitches
            or_glitch.append(requirement)

        elif requirement in inf_skills:  # Check on requirement to catch the energy skills without the =
            or_skills.append(requirement)
        elif elem in en_skills or elem in combat_name or elem == "Damage":
            or_resource.append(requirement)
        else:  # Case of an event
            or_skills.append(requirement)

        or_requirements = (or_skills, or_glitch, or_resource)


def append_rule() -> None:
    """Add the text to the rules list."""
    # TODO checker les glitch autrement qu'avec or_glitch ; séparer les cas avec ressource... ici
    global list_rules, difficulty
    and_skills, and_other, damage_and, combat_and, en_and = and_requirements
    energy = []

    start_txt = f"    add_rule(world.get_entrance(\"{anchor} -> {path_name}\", player), lambda s: "
    req_txt = ""

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
            if "Keystone=" in elem:
                temp_txt = f"can_open_door({path_name}, s, player)"
            elif "=" in elem:
                req_name, amount = elem.split("=")
                amount = int(amount)
                if req_name == "SpiritLight":
                    if amount == 1200:  # Case of a shop item
                        temp_txt = "can_buy_shop(s, player)"
                    else:  # Case of a map from Lupo
                        temp_txt = "can_buy_map(s, player)"
                elif req_name == "Ore":
                    temp_txt = f"s.count(\"Gorlek Ore\", player) >= {amount}"
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

    if target_area:
        if req_txt:
            req_txt += " and " + f"can_enter_area({target_area}, s, player, options)"
        else:
            req_txt += f"can_enter_area({target_area}, s, player, options)"

    if en_and:
        counter = Counter(en_and)
        for weapon in en_skills:
            amount = counter[weapon]
            if amount != 0:
                energy.append([weapon, amount])

    or_costs = []  # List of list, each element is a possibility. The first element of the lists codes the type of cost.
    for requirement in or_resource0:  # TODO rename, handle special cases
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
        temp_txt = (f"cost_all(s, player, options, \"{anchor}\", {damage_and}, {energy}, "  # TODO rename
                    f"{combat_and}, {or_costs}, {difficulty})")
        if req_txt:
            req_txt += " and " + temp_txt
        else:
            req_txt += temp_txt

    if req_txt:
        tot_txt = start_txt + req_txt + ", \"or\")\n"
    else:
        tot_txt = start_txt + "True, \"or\")\n"

    if glitched:
        difficulty_index = difficulty + 1
    else:
        difficulty_index = difficulty

    list_rules[difficulty_index] += tot_txt


def create_door_rules() -> None:
    """Add to list_rules and the entrances some connection rules for the doors."""
    global anchor, path_name, list_rules, entrances
    # Create the vanilla connection in one way
    list_rules[0] += f"    add_rule(world.get_entrance(\"{anchor} (Door) -> {path_name} (Door)\", player), lambda s: True)\n"
    # Link the door to the anchor (the connection from anchor to door can have a rule and is done in append_rule)
    list_rules[0] += f"    add_rule(world.get_entrance(\"{anchor} (Door) -> {anchor}\", player), lambda s: True)\n"
    entrances.append(f"{anchor} (Door) -> {path_name} (Door)")
    entrances.append(f"{anchor} (Door) -> {anchor}")


# %% Main script


with open("./areasv2.wotw", "r") as file:
    source_text = file.readlines()

# Moki, Gorlek, Kii and Unsafe rules respectively
moki = (header + imports + "def set_moki_rules(world: Multiworld, player: int, options: WotWOptions):\n"
        "    \"\"\"Moki (or easy, default) rules.\"\"\"\n")
gorlek = ("\n\ndef set_gorlek_rules(world: Multiworld, player: int, options: WotWOptions):\n"
          "    \"\"\"Gorlek (or medium) rules.\"\"\"\n")
gorlek_glitch = ("\n\ndef set_gorlek_glitched_rules(world: Multiworld, player: int, options: WotWOptions):\n"
                 "    \"\"\"Gorlek (or medium) rules with glitches\"\"\"\n")
kii = ("\n\ndef set_kii_rules(world: Multiworld, player: int, options: WotWOptions):\n"
       "    \"\"\"Kii (or hard) rules\"\"\"\n")
kii_glitch = ("\n\ndef set_kii_glitched_rules(world: Multiworld, player: int, options: WotWOptions):\n"
              "    \"\"\"Kii (or hard) rules with glitches.\"\"\"\n")
unsafe = ("\n\ndef set_unsafe_rules(world: Multiworld, player: int, options: WotWOptions):\n"
          "    \"\"\"Unsafe rules.\"\"\"\n")
unsafe_glitch = ("\n\ndef set_unsafe_glitched_rules(world: Multiworld, player: int, options: WotWOptions):\n"
                 "    \"\"\"Unsafe rules with glitches.\"\"\"\n")

# Store the parsed text for each difficulty
list_rules: list[str] = [moki, gorlek, gorlek_glitch, kii, kii_glitch, unsafe, unsafe_glitch]
# Store the entrance names
entrances: list[str] = []
# Contain the refill info per region in a tuple: (health, energy, type)
refills: dict[str, tuple[int, int, int]] = {}
refill_events: list[str] = []  # Store all the names given to the refill events.
doors_map: dict[str, int] = {}  # Mapping from door name to door ID
doors_vanilla: list[tuple[str, str]] = []  # Vanilla connections between the doors

# Global variables
indent = 0  # Number of indents
anchor = ""  # Name of the current anchor
glitched = False  # Whether the current path involves glitches
difficulty = 0  # Difficulty of the path
req = ""  # Full requirement
req1 = ""  # Requirements from first indent
req2 = ""  # Requirements from second indent
req3 = ""  # Requirements from third indent
req4 = ""  # Requirements from fourth indent
req5 = ""  # Requirements from fifth indent
refill_type = ""  # Refill type (energy, health, checkpoint or full)
path_type = ""  # Type of the path (connection, pickup, refill)
path_name = ""  # Name of the location/region/event accessed by the path
should_convert = False  # If True, convert is called to create a rule
is_door = False  # True while parsing a door
is_enter = False  # True when in an enter clause (when parsing the door rules)
door_id = 0
and_req: list[str] = []  # Stores the requirements form an and chain (i.e. coma separated requirements)
or_req: list[list[str]] = []  # Stores the requirements from each OR chain

and_requirements: tuple[list[str], list[str], list[str], list[str], list[str]] = ([], [], [], [], [])
or_requirements: tuple[list[str], list[str], list[str]] = ([], [], [])
or_skills0: list[str] = []
or_skills1: list[str] = []
or_resource0: list[str] = []
or_resource1: list[str] = []
or_glitch0: list[str] = []
or_glitch1: list[str] = []

target_area = ""  # Area of the path_name anchor

convert_diff = {"moki": 0, "gorlek": 1, "kii": 3, "unsafe": 5}

for i, line in enumerate(source_text):  # Line number is only used for debug
    should_convert = False  # Reset the flag to false

    # Parse the line text
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
        if is_enter:  # When in parsing a door connection, there is one extra indent, it is easier to remove it there
            if indent < 3:  # Exited from enter clause, so set it to false
                is_enter = False
            else:  # Remove the extra indent to avoid adding new cases
                indent -= 1

    if indent == 0:  # Always anchor, except for requirement or region (which are ignored)
        req1, req2, req3, req4, req5 = "", "", "", "", ""
        if "anchor" in line:
            name = try_group(r_colon, line, 1, -1)
            s = r_separate.search(name)  # Detect and remove the ` at <coord>` part if it exists.
            if s:
                anchor = name[:s.start()]
            else:
                anchor = name
            refills.setdefault(anchor, (0, 0, 0))
        else:
            anchor = ""

    elif indent == 1:
        req1, req2, req3, req4, req5 = "", "", "", "", ""
        difficulty = 0  # Reset the difficulty to moki
        if not anchor:  # Only happens with `requirement:` or `region`, ignore it
            continue
        if "nospawn" in line or "tprestriction" in line:
            continue
        if line == "door:":
            path_type = "conn"
            is_door = True
            continue
        is_door = False
        path_type = try_group(r_type, line, end=-1)  # Connection type
        if path_type not in ("conn", "state", "pickup", "refill", "quest"):
            raise ValueError(f"{path_type} (line {i}) is not an appropriate path type.\n\"{line}\"")
        if path_type == "refill":
            if ":" in line:
                path_name = try_group(r_name, line, 1, -1)  # Checkpoint, Full, Energy=x...
                conv_refill()
            else:
                path_name = try_group(r_refill, line, 1)  # Checkpoint, Full, Energy=x...
                conv_refill()
                should_convert = True
                req1 = "free"
        else:
            path_name = try_group(r_name, line, 1, -1)  # Name

        if "free" in line:
            should_convert = True
            req1 = "free"

    elif indent == 2:  # When not a door, this contains the path difficulty
        req2, req3, req4, req5 = "", "", "", ""
        if not anchor:  # Only happens with `requirement:` or `region`, ignore it
            continue
        if is_door:
            if "id:" in line:
                door_id = int(line[4:])
            elif "target:" in line:
                path_name = line[8:]
                path_type = "conn"
                doors_vanilla.append((anchor + " (Door)", path_name + " (Door)"))
                doors_map.setdefault(anchor + " (Door)", door_id)
                create_door_rules()
                path_name = anchor + " (Door)"  # To connect the anchor to the door, the rest is done in create_door_rules
            elif "free" in line:  # Case of a free door connection
                should_convert = True
                req1 = "free"
                req2 = ""
            else:  # Case of line == "enter:", the rules are in the next lines
                is_enter = True
                is_door = False
        else:
            path_diff = try_group(r_difficulty, line, end=-1)  # moki, gorlek, kii, unsafe
            difficulty = convert_diff[path_diff]
            req2 = line[try_end(r_difficulty, line) + 1:]  # Can be empty
            if req2:
                if req2[-1] == ":":
                    req2 = req2[:-1]
                else:
                    should_convert = True

    elif indent == 3:
        req3, req4, req5 = "", "", ""
        if not anchor:  # Only happens with `requirement:` or `region`, ignore it
            continue
        if line[-1] == ":":
            req3 = line[:-1]
        else:
            req3 = line
            should_convert = True

    elif indent == 4:
        req4, req5 = "", ""
        if not anchor:  # Only happens with `requirement:` or `region`, ignore it
            continue
        if line[-1] == ":":
            req4 = line[:-1]
        else:
            req4 = line
            should_convert = True

    elif indent == 5:
        req5 = ""
        if not anchor:  # Only happens with `requirement:` or `region`, ignore it
            continue
        req5 = line
        should_convert = True

    else:
        raise NotImplementedError(f"Too many indents ({indent}) on line {i}.\n{line}")

    if should_convert:
        req = req1
        if indent >= 2:
            if req and req2:  # req1 can be empty, same for req2
                req += f", {req2}"
            elif req2:  # Case where req1 empty, req2 non empty
                req = req2
        if indent >= 3:
            if req:
                req += f", {req3}"
            else:
                req = req3
        if indent >= 4:
            req += f", {req4}"
        if indent >= 5:
            req += f", {req5}"
        req = req.replace(":", ",")  # In some cases, a colon is used in place of a coma, regroup the two cases
        convert()

write_files()

# Convert the parsed line into lists of requirements
