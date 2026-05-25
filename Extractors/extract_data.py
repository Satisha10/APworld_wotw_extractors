"""
Extracts the data on events (or states), regions (or anchors), and locations (or pickups).

The data is extracted from the `areas.wotw` and `loc_data.csv` files.
See https://github.com/ori-community/wotw-seedgen/tree/main/wotw_seedgen to get these files.
"""

import re
import os

com = re.compile(" *#")  # Detects comments
sp = re.compile("^ *")  # Used for indents
col = re.compile(" .*:")  # name between space and colon
tra = re.compile(" *$")  # Trailing space
sep = re.compile(" at ")


def extract_all(override=False):
    """Extract the data on events, regions and locations."""
    extract_events(override)
    extract_quests(override)
    extract_regions(override)


def extract_quests(override=False):
    """Extract the data from `areas.wotw` and write a file with the quest table."""
    if os.path.exists("./Quests.py"):
        if override:
            print("Warning: File replaced")
        else:
            raise FileExistsError("The file `Quests.py` already exists. Use `override=True` to override it.")

    header = (
        '"""\n'
        "Generated file, do not edit manually.\n\n"
        "See https://github.com/Satisha10/APworld_wotw_extractors for the code.\n"
        "Generated with `extract_data.py` by running `extract_quests()`.\n"
        '"""\n\n\n'
    )

    quests = []

    quest_txt = header + "quest_table = [\n"

    with open("./areas.wotw", "r") as file:
        temp = file.readlines()

    for p in temp:
        m = com.search(p)  # Removes the comments
        if m:
            p = p[: m.start()]
        m = tra.search(p)  # Removes the trailing spaces
        if m:
            p = p[: m.start()]
        if p == "":
            continue

        m = sp.match(p)  # Counts the indents
        if m is None:
            ind = 0
        else:
            ind = (m.end() + 1) // 2

        if ind == 1:
            if "pickup" in p or "quest" in p:
                name = col.search(p[2:]).group()[1:-1]
                if "quest" in p and name not in quests:
                    quests.append(name)

    for quest in quests:
        quest_txt += f'    "{quest}",\n'
    quest_txt = quest_txt[:-2]
    quest_txt += "\n    ]\n"

    with open("Quests.py", "w") as file:
        file.write(quest_txt)
        print("The file Quests.py has been successfully created.")


def extract_events(override=False):
    """Extract the data and write them as a table with the events."""
    if os.path.exists("./Events.py"):
        if override:
            print("Warning: File replaced")
        else:
            raise FileExistsError("The file `Events.py` already exists. Use `override=True` to override it.")

    header = (
        '"""\n'
        "Generated file, do not edit manually.\n\n"
        "See https://github.com/Satisha10/AP_world_wotw_extractors for the code.\n"
        "Generated with `extract_data.py` by running `extract_events()`.\n"
        '"""\n\n\n'
    )

    combat_events = [
        "Combat.Ranged",
        "Combat.Aerial",
        "Combat.Dangerous",
        "Combat.Shielded",
        "Combat.Bat",
        "Combat.Sand",
    ]

    other_events = [
        "BreakCrystal",
    ]

    events = combat_events + other_events

    event_txt = "event_table = [\n"

    with open("./areas.wotw", "r") as file:
        temp = file.readlines()

    for p in temp:
        m = com.search(p)  # Removes the comments
        if m:
            p = p[: m.start()]
        m = tra.search(p)  # Removes the trailing spaces
        if m:
            p = p[: m.start()]
        if p == "":
            continue

        m = sp.match(p)  # Counts the indents
        if m is None:
            ind = 0
        else:
            ind = (m.end() + 1) // 2

        if ind == 0:
            if "requirement" in p:
                name = col.search(p).group()[1:-1]
                if name not in events:
                    events.append(name)
            elif "region" in p:
                name = col.search(p).group()[1:-1]
                if name not in events:
                    events.append(f"danger_{name}")
        elif ind == 1:
            if "state" in p:
                name = col.search(p[2:]).group()[1:-1]
                if name not in events:
                    events.append(name)

    for event in events:
        event_txt += f'    "{event}",\n'

    event_txt = event_txt[:-2]
    event_txt += "\n    ]\n"

    with open("Events.py", "w") as file:
        file.write(header + event_txt)
        print("The file Events.py has been successfully created.")


def extract_regions(override=False):
    """Extract the data and write a file with the regions."""
    if os.path.exists("./Regions.py"):
        if override:
            print("Warning: File replaced")
        else:
            raise FileExistsError("The file `Regions.py` already exists. Use `override=True` to override it.")

    header = (
        '"""\n'
        "Generated file, do not edit manually.\n\n"
        "See https://github.com/Satisha10/AP_world_wotw_extractors for the code.\n"
        "Generated with `extract_data.py` by running `extract_regions()`.\n"
        '"""\n\n\n'
    )

    regions: dict[str, tuple[bool, int, int]] = {}
    previous_line_flag = False
    anc: str = ""
    x_coord, y_coord = 0, 0

    with open("./areas.wotw", "r") as file:
        temp = file.readlines()

    for line in temp:
        temp_txt = com.search(line)  # Removes the comments
        if temp_txt:
            line = line[: temp_txt.start()]
        temp_txt = tra.search(line)  # Removes the trailing spaces
        if temp_txt:
            line = line[: temp_txt.start()]
        if line == "":
            continue

        indent_txt = sp.match(line)  # Counts the indents
        if indent_txt is None:
            ind = 0
        else:
            ind = (indent_txt.end() + 1) // 2

        if previous_line_flag:  # Non-empty line after an anchor: check if 'nospawn' is there
            can_spawn = bool("nospawn" not in line and x_coord != 0)
            regions.setdefault(anc, (can_spawn, x_coord, y_coord))
            previous_line_flag = False

        if ind == 0:
            if "anchor" in line:
                previous_line_flag = True
                name = col.search(line).group()[1:-1]
                trimmed_txt = sep.search(name)
                if trimmed_txt:
                    anc = name[: trimmed_txt.start()]
                    coord = name[trimmed_txt.end():].split(",")  # Take the part after ' at ' and split the two coords
                    x_coord, y_coord = int(coord[0]), int(coord[1])
                else:
                    anc = name
                    x_coord, y_coord = 0, 0

    region_txt = header + "region_table: dict[str, tuple[bool, int, int]] = {\n"

    for region, data in regions.items():
        region_txt += f'    "{region}": {data},\n'

    region_txt = region_txt[:-2]
    region_txt += "\n    }\n"

    with open("Regions.py", "w") as file:
        file.write(region_txt)
        print("The file Regions.py has been successfully created.")
