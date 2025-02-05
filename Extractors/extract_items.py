"""
Extracts the list of items and locations in Ori and the Will of the Wisps.

The data is extracted from the `Items_data.csv` and `loc_data.csv` files.
See https://github.com/ori-community/wotw-seedgen/tree/main/wotw_seedgen for loc_data.csv.
"""


import os
# base_id = int(prefix + "0000000000000000000000000000000000", 2)


def extract_items(override=False):
    """Extract the data and writes a file with the item table and the item groups."""
    if os.path.exists("./Items.py"):
        if override:
            print("Warning: File replaced")
        else:
            raise FileExistsError("The file `Items.py` already exists. Use `override=True` to override it.")

    prefix = "101111110010101001"
    store = []  # Stores the IDs to check for duplicates

    header = ("\"\"\"\n"
              "Generated file, do not edit manually.\n\n"
              "See https://github.com/Satisha10/AP_world_wotw_extractors for the code.\n"
              "Generated with `extract_items.py` by running `extract_items()`.\n"
              "\"\"\"\n\n\n"
              "from BaseClasses import ItemClassification\n\n")

    with open("./Items_data.csv", "r") as file:
        temp = file.readlines()

    item_txt = header + "item_table = {  # The tuple contains the amount, the classification, the ID\n"

    for line in temp[1:]:
        data = line.split(",")
        item_id = compute_id(prefix, data[3], data[4], data[5])
        if item_id in store:
            raise ValueError(f"{item_id} duplicated.\n"
                             f"Group = {data[4]}, State = {data[5]},  Item = {data[0]}")
        store.append(item_id)
        item_txt += f"    \"{data[0]}\": ({int(data[1])}, ItemClassification.{data[2]}, {item_id}),\n"
    item_txt = item_txt[:-2]
    item_txt += "\n    }\n\n\n"

    item_txt += ('group_table = {\n'
                 '    "skills": ["Sword", "Double Jump", "Regenerate", "Bow", "Dash", "Bash", "Grapple", "Glide", "Flap", "Grenade",\n'
                 '               "Flash", "Water Dash", "Burrow", "Launch", "Clean Water", "Water Breath", "Hammer", "Sentry",\n'
                 '               "Shuriken", "Spear", "Blaze"],\n'
                 '    "collectibles": ["Health Fragment", "Energy Fragment", "Keystone", "Ore", "Shard Slot", "Ancestral Light 1",\n'
                 '               "Ancestral Light 2"],\n'
                 '    "spirit_light": ["1 Spirit Light", "50 Spirit Light", "100 Spirit Light", "200 Spirit Light"],\n'
                 '    "shards": ["Overcharge", "Triple Jump", "Wingclip", "Bounty", "Swap", "Magnet", "Splinter", "Reckless", "Quickshot",\n'
                 '               "Resilience", "Light Harvest", "Vitality", "Life Harvest", "Energy Harvest", "Energy (Shard)",\n'
                 '               "Life Pact", "Last Stand", "Sense", "Ultra Bash", "Ultra Grapple", "Overflow", "Thorn", "Catalyst",\n'
                 '               "Turmoil", "Sticky","Finesse", "Spirit Surge", "Lifeforce", "Deflector", "Fracture", "Arcing"],\n'
                 '    "teleporters": ["Midnight Burrows TP", "Howl\'s Den TP", "Central Luma TP", "Mouldwood Depths TP",\n'
                 '                    "Wellspring TP", "Baur\'s Reach TP", "Kwolok\'s Hollow TP", "Woods Entrance TP", "Woods Exit TP",\n'
                 '                    "Feeding Grounds TP", "Central Wastes TP", "Outer Ruins TP", "Willow\'s End TP",\n'
                 '                    "Inkwater Marsh TP", "Glades TP"],\n'
                 '    "extra_tp": ["Luma Boss TP", "Inner Ruins TP", "Shriek TP"],\n'
                 '    "weapon_upgrades": ["Exploding Spear", "Hammer Shockwave", "Static Shuriken", "Charge Blaze", "Rapid Sentry"],\n'
                 '    "bonus": ["Health Regeneration", "Energy Regeneration", "Extra Double Jump", "Extra Air Dash", "Blaze Efficiency",\n'
                 '              "Spear Efficiency", "Shuriken Efficiency", "Sentry Efficiency", "Bow Efficiency", "Regenerate Efficiency",\n'
                 '              "Flash Efficiency", "Grenade Efficiency"],\n'
                 '    "bonus+": ["Rapid Sword", "Rapid Hammer", "Rapid Spear", "Rapid Grenade", "Quickshot Upgrade", "Rapid Regenerate",\n'
                 '               "Melting Bow", "Melting Blaze", "Melting Sword", "Melting Hammer", "Melting Spear", "Melting Shuriken",\n'
                 '               "Uncharged Bashnades", "Extra Grenade", "Splinter Grenade", "Unlimited Sentries", "Sentry Burst Upgrade",\n'
                 '               "Sentry Fire Rate", "Extra Shurikens", "Splinter Shurikens", "Bashable Shurikens"],\n'
                 '    "skill_upgrades": ["Jumpgrade", "Skill Velocity"]\n'
                 '    }\n')

    with open("Items.py", "w") as file:
        file.write(item_txt)
        print("The file Items.py has been successfully created.")


def extract_locs(override=False):
    """Extract the data and writes a file with the location table."""
    if os.path.exists("./Locations.py"):
        if override:
            print("Warning: File replaced")
        else:
            raise FileExistsError("The file `Locations.py` already exists. Use `override=True` to override it.")

    prefix = "101111110010101001"
    store = []  # Stores the IDs to check for duplicates

    header = ("\"\"\"\n"
              "Generated file, do not edit manually.\n\n"
              "See https://github.com/Satisha10/APworld_wotw_extractors for the code.\n"
              "Generated with `extract_items.py` by running `extract_locs()`.\n"
              "\"\"\"\n\n\n")

    with open("./loc_data.csv", "r") as file:
        temp = file.readlines()

    loc_txt = header + "loc_table = {\n"

    for line in temp[1:]:
        data = line.split(", ")
        loc_id = compute_id(prefix, "location", data[5], data[7], data[8])
        if loc_id in store:
            raise ValueError(f"{loc_id} duplicated.\n"
                             f"Group = {data[5]}, State = {data[7]}, Value = {data[8]}, Location = {data[0]}")
        store.append(loc_id)
        loc_txt += f"    \"{data[0]}\": {loc_id},\n"
    loc_txt = loc_txt[:-2]
    loc_txt += "\n    }\n"

    with open("Locations.py", "w") as file:
        file.write(loc_txt)
        print("The file Locations.py has been successfully created.")


def compute_id(pre, item_type, group, state, value=""):
    """
    Return the item ID according to its type, and its uberstate group and value.

    The protocol to compute the IDs is given in :
    https://github.com/ori-community/wotw-rando-client/blob/archipelago/projects/Randomizer/archipelago/archipelago_ids.h
    """
    assert int(group) <= 65535, f"group must be smaller than 65535 (is equal to {group})"
    assert int(state) <= 65535, f"state must be smaller than 65535 (is equal to {state})"
    if value:
        assert int(value) <= 255, f"state must be smaller than 255 (is equal to {value})"

    if item_type == "location":
        b_item_type = "00"
        if not value:
            value = "1"
    elif item_type == "item":
        b_item_type = "01"
        value = ""
    elif item_type == "resource":
        b_item_type = "10"
        value = ""
    elif item_type == "upgrade":
        b_item_type = "11"
        value = ""
    else:
        raise ValueError(f"{item_type} is not a valid type of item (must be location, item or resource).")

    b_group = bin(int(group))[2:]
    if item_type == "location":
        b_group = "0" * (8 - len(b_group[-8:])) + b_group[-8:]
    else:
        b_group = "0" * (16 - len(b_group)) + b_group

    b_state = bin(int(state))[2:]
    b_state = "0" * (16 - len(b_state)) + b_state

    if value:
        b_value = bin(int(value))[2:]
        b_value = "0" * (8 - len(b_value)) + b_value
    else:
        b_value = ""

    total = pre + b_item_type + b_group + b_state + b_value
    return int(total, 2)
