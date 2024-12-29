"""
Create a data set with the uber group/state for all locations, in C++ syntax.

The data is extracted from the `loc_data.csv` file.
See https://github.com/ori-community/wotw-seedgen/tree/main/wotw_seedgen to get this file.
"""

import os


def extract_loc(override=False):
    """Extract the data from `loc_data.csv` and write a file with the location set."""
    if os.path.exists("./Locations_map.h"):
        if override:
            print("Warning: File replaced")
        else:
            raise FileExistsError("The file `Locations_map.h` already exists. Use `override=True` to override it.")

    with open("./loc_data.csv", "r") as file:
        temp = file.readlines()

    loc_txt = "        const std::unordered_set<core::api::uber_states::UberState> m_locations_map = {\n"

    for line in temp[1:]:
        data = line.split(", ")
        loc_txt += f"            core::api::uber_states::UberState({data[5]}, {data[7]}),\n"
    loc_txt = loc_txt[:-2]
    loc_txt += "\n        };\n"

    with open("Locations_map.h", "w") as file:
        file.write(loc_txt)
        print("The file Locations_map.h has been successfully created.")
