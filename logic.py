import os
import pickle
from typing import List, Tuple

import checker

data_dict = {
    "entrance_location_list": [],
    "empty_space_list": [],
    "anchor_pos_list": [],
    "overlap_space_list": [],
}


def overlap_space_list_refresh(obj_data: List[Tuple[str, Tuple[int, int, int, int]]]):
    empty_space_list = data_dict["empty_space_list"]
    overlap_space_list = data_dict["overlap_space_list"]

    overlap_space_list.clear()
    for data in obj_data:
        cls, (x, y, w, h) = data

        for empty_space in empty_space_list:
            empty_space_pos = tuple(map(int, empty_space.split(",")))
            if checker.check_coord_overlap((x, y, w, h), empty_space_pos):
                overlap_space_list.append((cls, empty_space_pos))


def save_data(filepath="data.pickle"):
    global data_dict

    save_data = {
        "empty_space_list": data_dict["empty_space_list"],
        "anchor_pos_list": data_dict["anchor_pos_list"],
    }

    with open(filepath, "wb") as f:
        pickle.dump(save_data, f)


def load_data(filepath="data.pickle"):
    global data_dict

    if not os.path.exists(filepath):
        return

    with open(filepath, "rb") as f:
        load_data = pickle.load(f)

    data_dict["empty_space_list"].extend(load_data["empty_space_list"])
    data_dict["anchor_pos_list"].extend(load_data["anchor_pos_list"])


def clear_data():
    global data_dict

    data_dict["empty_space_list"].clear()
    data_dict["anchor_pos_list"].clear()
