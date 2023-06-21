import os
import pickle
import time
import cv2
from typing import Dict, List, Tuple, Union
from arduino import ArduinoManager

import checker
import pathfinder
from global_var import global_data_dict

SAVE_DATA_KEYS = ["entrance_location_list", "path_pixel_scale", "empty_space_list", "anchor_pos_list", "edge_list"]


def push_arduino():
    """경로 정보를 아두이노로 송신"""

    path_infos = global_data_dict["real_path_list"]
    path_msg_list = [msg for _, _, _, _, msg in path_infos]

    with ArduinoManager() as am:
        before_msg = ""
        for idx, path_msg in enumerate(path_msg_list):
            msg = f"{idx + 1:02d}:{path_msg}"
            print(f"[{msg}] 전송 중...")
            am.write(0, msg)
            am.write(1, before_msg)
            before_msg = msg
            time.sleep(3)

    print("전송 완료.")


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


def processing(frame, args: Dict[str, Union[str, int]]):
    print("Library loading...")
    import yolo_helper

    print("Inferring...")
    object_data = yolo_helper.use_yolo(frame, args["yolo_model_name"].lower() + ".pt")[0]

    for list_tag in ["empty_space_list", "anchor_pos_list", "entrance_location_list"]:
        data_list = global_data_dict[list_tag]

        for data in data_list:
            obj = tuple(map(int, data.split(",")))
            x, y = obj

            cv2.circle(frame, (x, y), 5, color=(0, 255, 0), thickness=5)

    print(f"감지된 물체: {len(object_data)}")

    overlap_space_list_refresh(object_data)

    entry_index = int(args["entry_index"])
    entry_pos = global_data_dict["entrance_location_list"][entry_index]

    print(f"입구 좌표: {entry_pos}")
    entry_pos = tuple(map(int, entry_pos.split(",")))

    distance, path = pathfinder.find_path(entry_pos, lambda *args, **kwargs: pathfinder.PathNode(*args, **kwargs), True)

    print(f"최단 거리: {distance}")

    global_data_dict["real_path_list"] = pathfinder.get_real_path(path)

    # 프레임 출력
    cv2.imshow("VideoFrame", frame)

    push_arduino()


def real_time_start(args: Dict[str, Union[str, int]]):
    """실시간 서비스 처리

    Args:
        args (Dict[str, Union[str, int]]): 인자값
    """

    print("전처리 데이터 로드 중...")
    load_data(args["savepath"])

    print("카메라 장치 로드 중...")
    # 캡쳐 장치 설정
    capture = cv2.VideoCapture(0)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, int(args["frame_width"]))
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, int(args["frame_height"]))

    while cv2.waitKey(33) < 0:  # 키 입력이 없을경우, 반복
        # 한 프레임을 카메라에서 가져옴
        ret, frame = capture.read()

        processing(frame, args)

    # 장치 해제
    capture.release()
    # 모든 창 닫기
    cv2.destroyAllWindows()
