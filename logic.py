import os
import pickle
from typing import List, Tuple

import checker
from global_var import global_data_dict

SAVE_DATA_KEYS = ["entrance_location_list", "path_pixel_scale", "empty_space_list", "anchor_pos_list"]


def overlap_space_list_refresh(obj_data: List[Tuple[str, Tuple[int, int, int, int]]]):
    """빈자리 및 물체 사이의 겹침 처리

    Args:
        obj_data (List[Tuple[str, Tuple[int, int, int, int]]]): 물체 데이터 (물체종류, (좌상단 X, 좌상단 Y, 너비, 높이))
    """

    empty_space_list = global_data_dict["empty_space_list"]
    overlap_space_list = global_data_dict["overlap_space_list"]

    overlap_space_list.clear()

    for data in obj_data:
        cls, (x, y, w, h) = data

        for empty_space in empty_space_list:
            empty_space_pos = tuple(map(int, empty_space.split(",")))
            if checker.check_coord_overlap((x, y, w, h), empty_space_pos):
                overlap_space_list.append((cls, empty_space_pos))


def save_data(filepath="data.pickle"):
    """데이터 저장 처리

    Args:
        filepath (str, optional): 파일 경로. Defaults to "data.pickle".
    """

    save_data = {}

    for key in SAVE_DATA_KEYS:
        save_data[key] = global_data_dict[key]

    with open(filepath, "wb") as f:
        pickle.dump(save_data, f)


def load_data(filepath="data.pickle"):
    """데이터 로드 처리

    Args:
        filepath (str, optional): 파일 경로. Defaults to "data.pickle".
    """

    if not os.path.exists(filepath):
        return

    with open(filepath, "rb") as f:
        load_data = pickle.load(f)

    for key in SAVE_DATA_KEYS:
        try:
            datas = global_data_dict[key]

            if isinstance(datas, list):
                datas.clear()
                datas.extend(load_data[key])

        except Exception as ex:
            print(f"데이터 로드 오류 발생!")
            print(ex)


def clear_data():
    """데이터 초기화"""

    for data in global_data_dict.values():
        data.clear()
    global_data_dict["path_pixel_scale"].extend([30, 30])
