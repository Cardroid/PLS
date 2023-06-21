import os
import pickle
import time
from typing import Any, Dict, List, Literal, Tuple, Union
import cv2
import dearpygui.dearpygui as dpg

from global_var import global_data_dict
import logic
import checker
import draw_helper
import pathfinder
import theme
import util


# 컨트롤 창 가로, 세로
control_window_w = 350
control_window_h = 750

# 이미지 가로, 세로
image_window_w = 1300
image_window_h = 600


# 현재 상태 저장용 사전
current_state = {
    "yolo_model_name": "YOLOv8x",
    "entrance_location_list": 0,
    "anchor_pos_list": 0,
    "anchor_pos_list": 0,
    "edge_list": 0,
    "edge_buffer": None,
    "draw_dict": {
        "shape": {
            "entrance_location_list": lambda *args, **kwargs: draw_helper.draw_circle(
                radius=5, color=draw_helper.get_color("entrance_location_list"), fill=(255, 30, 200, 255), *args, **kwargs
            ),
            "empty_space_list": lambda *args, **kwargs: draw_helper.draw_circle(radius=5, color=draw_helper.get_color("empty_space_list"), fill=(255, 0, 0, 255), *args, **kwargs),
            "anchor_pos_list": lambda *args, **kwargs: draw_helper.draw_circle(radius=5, color=draw_helper.get_color("anchor_pos_list"), fill=(0, 0, 255, 255), *args, **kwargs),
            "edge_list": lambda *args, **kwargs: dpg.draw_line(color=draw_helper.get_color("edge_list"), *args, **kwargs),
            "overlap_space_list": lambda *args, **kwargs: draw_helper.draw_polygon(point_num=6, radius=25, color=draw_helper.get_color("overlap_space_list"), *args, **kwargs),
            "object_car": lambda *args, **kwargs: draw_helper.draw_rectangle(color=draw_helper.get_color("object_car"), *args, **kwargs),
            "object_other": lambda *args, **kwargs: draw_helper.draw_rectangle(color=draw_helper.get_color("object_other"), *args, **kwargs),
        },
    },
}
# 그리드 뷰 (위젯 상태 저장용)
is_path_pixel_scale_grid_view = False

# 인식된 물체 저장용 리스트
object_data = []

# 이미지 그래픽 부모 위젯 Tag
img_widget_tag = "image_widget"
# 결과 및 과정 표시 텍스트 위젯 Tag
status_widget_tag = "status_text_widget"


def list_seleted_handler(list_tag: str):
    """리스트 선택 동작 처리

    Args:
        list_tag (str): 리스트 Tag
    """

    global current_state

    current_state[list_tag] = dpg.get_value(list_tag)


def remove_list_item_handler(list_tag: str):
    """리스트 아이템 제거 처리

    Args:
        list_tag (str): 항목을 제거할 리스트 Tag
    """
    item = dpg.get_value(list_tag)
    source_list = global_data_dict[list_tag]
    if item in source_list:
        item_idx = source_list.index(item)
        if list_tag == "edge_list":
            update_edge(item, True)
        else:
            update_pos_list(list_tag, item, True)
        dpg.configure_item(list_tag, items=source_list)

        if len(source_list) > 0:
            if item_idx >= len(source_list):
                item_idx = len(source_list) - 1

            current_select_item = source_list[item_idx]
            current_state[list_tag] = current_select_item
            dpg.configure_item(list_tag, default_value=current_select_item)


def add_and_load_resized_image(image_path: str, small_window_w: Union[int, None] = None, small_window_h: Union[int, None] = None) -> Tuple[Union[int, str], int, int]:
    """이미지 로드 처리 (리사이징)

    Args:
        image_path (str): 이미지 경로
        small_window_w (Union[int, None], optional): 이미지 가로 사이즈 (None일 경우, 원본 사이즈 사용). Defaults to None.
        small_window_h (Union[int, None], optional): 이미지 세로 사이즈 (None일 경우, 원본 사이즈 사용). Defaults to None.

    Returns:
        Tuple[Union[int, str], int, int]: 이미지 Tag, 이미지 가로 사이즈, 이미지 세로 사이즈
    """

    global prev_image_path, img_w, img_h

    if "prev_image_path" not in globals() or prev_image_path != image_path:
        img_tag = "image_input_tag"

        image = cv2.imread(image_path)

        texture = util.convert_cv_to_dpg(
            image,
            small_window_w,
            small_window_h,
        )

        img_w = image.shape[1] if small_window_w is None else small_window_w
        img_h = image.shape[0] if small_window_h is None else small_window_h

        with dpg.texture_registry(show=False):
            dpg.add_raw_texture(
                img_w,
                img_h,
                texture,
                tag=img_tag,
                format=dpg.mvFormat_Float_rgb,
            )

        prev_image_path = image_path

    return img_tag, img_w, img_h


def detect_object(method_type: str):
    """물체 인식 처리

    Args:
        method_type (str): 물체인식 방법
    """

    global object_data

    for cls, (x, y, w, h) in object_data:
        cls = cls if cls == "car" else "other"

        draw_tag = f"object_{cls}_{x}_{y}_{w}_{h}"
        dpg.delete_item(item=draw_tag)

    print(f"{method_type.upper()} running...")
    method_type = method_type.lower()

    if method_type == "clear":
        object_data.clear()
    elif method_type == "yolo":
        print("lib loading...")
        import yolo_helper

        print("inferring...")
        object_data = yolo_helper.use_yolo(image_path, current_state["yolo_model_name"].lower() + ".pt")[0]

    for cls, (x, y, w, h) in object_data:
        cls = cls if cls == "car" else "other"
        draw_tag = f"object_{cls}_{x}_{y}_{w}_{h}"
        func = current_state["draw_dict"]["shape"][f"object_{cls}"]
        func(x, y, x + w, y + h, thickness=3, tag=draw_tag, parent=img_widget_tag)

    overlap_space_list_refresh()


def select_yolo_model_handler(sender: Union[int, str], data: str):
    """YOLO 모델 변경 콤보박스 위젯 콜백 처리

    Args:
        sender (Union[int, str]): 위젯 Tag
        data (str): 모델 이름
    """
    current_state["yolo_model_name"] = data


def add_point(sender: Union[int, str], data: Tuple[int, int]):
    """좌표 추가 처리

    Args:
        sender (Union[int, str]): 이벤트가 발생한 위젯의 Tag
        data (Tuple[int, int]): 마우스 데이터
    """

    btn_type, _ = data

    if 0 <= btn_type <= 2:
        x, y = tuple(map(int, dpg.get_mouse_pos()))
        x -= 8
        y -= 8

        if btn_type == 0:
            if dpg.is_key_down(dpg.mvKey_Shift):
                list_tag = "edge_list"
            else:
                list_tag = "empty_space_list"
        elif btn_type == 1:
            list_tag = "anchor_pos_list"
        elif btn_type == 2:
            list_tag = "entrance_location_list"

        if list_tag == "edge_list":
            update_edge((x, y))
        else:
            update_pos_list(list_tag, (x, y), False)

            dpg.configure_item(list_tag, items=global_data_dict[list_tag])

            source_list = global_data_dict[list_tag]
            if 0 < len(source_list):
                current_select_item = source_list[len(source_list) - 1]
                current_state[list_tag] = current_select_item
                dpg.configure_item(list_tag, default_value=current_select_item)


def update_edge(pos: Union[str, Tuple[int, int]], is_delete: bool = False):
    """간선 추가

    Args:
        pos (Union[str, Tuple[int, int]]): 현재의 정점 위치
        is_delete (bool, optional): 삭제 옵션. Defaults to False.
    """
    list_tag = "edge_list"

    if is_delete:
        idx = global_data_dict[list_tag].index(pos)
        del global_data_dict[list_tag][idx]

        draw_edge()
    else:
        temp_pos = None
        min_distance = None
        for anchor_pos in global_data_dict["anchor_pos_list"]:
            x, y = pos
            ax, ay = tuple(map(int, anchor_pos.split(",")))
            distance = pathfinder.calculate_distance(ax, ay, x, y, mode="euclidean")

            if min_distance is None or distance < min_distance:
                temp_pos = (ax, ay)
                min_distance = distance
        pos = temp_pos

        if current_state["edge_buffer"] is None:
            current_state["edge_buffer"] = pos
        else:
            bx, by = current_state["edge_buffer"]
            x, y = pos

            if bx != x or by != y:
                current_state["edge_buffer"] = None

                global_data_dict[list_tag].append(f"{bx}, {by} - {x}, {y}")

                draw_edge()


def draw_edge():
    """간선 그래픽 처리"""

    list_tag = "edge_list"

    edge_list: List[str] = global_data_dict[list_tag]
    draw_widget_tag = f"{list_tag}_widget_tag"

    func = current_state["draw_dict"]["shape"][list_tag]

    if util.widget_check(draw_widget_tag):
        dpg.delete_item(draw_widget_tag)

    with dpg.draw_node(tag=draw_widget_tag, parent=img_widget_tag):
        for edge in edge_list:
            bpos, apos = edge.split("-")
            bx, by = tuple(map(int, bpos.split(",")))
            ax, ay = tuple(map(int, apos.split(",")))

            func(p1=(bx, by), p2=(ax, ay))

    dpg.configure_item(list_tag, items=global_data_dict[list_tag])

    source_list = global_data_dict[list_tag]
    if 0 < len(source_list):
        current_select_item = source_list[len(source_list) - 1]
        current_state[list_tag] = current_select_item
        dpg.configure_item(list_tag, default_value=current_select_item)


def update_pos_list(list_tag: str, obj: Union[str, Tuple[int, int]], is_delete: bool = False):
    """좌표 업데이트 처리

    Args:
        list_tag (str): 추가할 좌표가 입력되어야 하는 리스트 Tag
        obj (Union[str, Tuple[int, int]]): 좌표 데이터 (x, y)
        is_delete (bool, optional): 삭제 옵션. Defaults to False.
    """

    global current_state

    if isinstance(obj, str):
        obj = tuple(map(int, obj.split(",")))

    x, y = obj

    if is_delete:
        idx = global_data_dict[list_tag].index(f"{x}, {y}")

        if list_tag == "anchor_pos_list":
            e_idxs = []
            for i, edge in enumerate(global_data_dict["edge_list"]):
                bpos, apos = edge.split("-")
                bx, by = tuple(map(int, bpos.split(",")))
                ax, ay = tuple(map(int, apos.split(",")))

                if bx == x and by == y or ax == x and ay == y:
                    e_idxs.append(i)

            e_idxs.reverse()
            for e_idx in e_idxs:
                del global_data_dict["edge_list"][e_idx]

        del global_data_dict[list_tag][idx]
    else:
        data = f"{x}, {y}"
        if data not in global_data_dict[list_tag]:
            global_data_dict[list_tag].append(data)

    refresh_draw()


def refresh_draw():
    """화면 그래픽 갱신 처리"""

    global current_state, object_data

    draw_widget_tag = "draw_point_tag"

    if util.widget_check(draw_widget_tag):
        dpg.delete_item(draw_widget_tag)

    with dpg.draw_node(tag=draw_widget_tag, parent=img_widget_tag):
        for list_tag in ["empty_space_list", "anchor_pos_list", "entrance_location_list"]:
            data_list = global_data_dict[list_tag]
            func = current_state["draw_dict"]["shape"][list_tag]

            for data in data_list:
                obj = tuple(map(int, data.split(",")))
                x, y = obj

                func(x, y, thickness=5)

            dpg.configure_item(list_tag, items=data_list)

    overlap_space_list_refresh()
    refresh_path_pixel_scale_axis()
    draw_edge()
    clear_path()


def refresh_select():
    """리스트 선택 갱신 처리"""

    global current_state

    for list_tag in ["empty_space_list", "anchor_pos_list", "entrance_location_list", "edge_list"]:
        source_list = global_data_dict[list_tag]
        if len(source_list) > 0:
            current_state[list_tag] = source_list[len(source_list) - 1]

            dpg.configure_item(list_tag, default_value=current_state[list_tag])


def overlap_space_list_refresh():
    """빈자리 및 물체 사이의 겹침 처리"""

    global current_state, object_data

    list_tag = "overlap_space_list"
    draw_widget_tag = f"{list_tag}_widget_tag"

    overlap_space_list = global_data_dict[list_tag]

    if util.widget_check(draw_widget_tag):
        dpg.delete_item(item=draw_widget_tag)

    func = current_state["draw_dict"]["shape"][list_tag]

    logic.overlap_space_list_refresh(object_data)

    with dpg.draw_node(tag=draw_widget_tag, parent=img_widget_tag):
        for cls, (x, y) in overlap_space_list:
            func(x, y, thickness=3, parent=draw_widget_tag)

    empty_space_list = global_data_dict["empty_space_list"]
    overlap_space_list = global_data_dict["overlap_space_list"]
    dpg.configure_item(status_widget_tag, default_value=f"총 공간: {len(empty_space_list)}\n- 차량 존재: {len(overlap_space_list)}\n= 빈 공간: {len(empty_space_list) - len(overlap_space_list)}")


def path_pixel_scale_grid_view_checkbox_handler():
    """축척 그리드 뷰 처리"""

    global is_path_pixel_scale_grid_view, img_w, img_h

    is_path_pixel_scale_grid_view = not is_path_pixel_scale_grid_view

    path_pixel_scale_grid_calculate()


def path_pixel_scale_grid_calculate():
    """경로 그리드 계산, 그리기 및 경로 노드 생성 처리"""

    draw_widget_tag = "path_pixel_scale_grid_view"

    if util.widget_check(draw_widget_tag):
        dpg.delete_item(draw_widget_tag)

    path_pixel_scale_x, path_pixel_scale_y = global_data_dict["path_pixel_scale"]

    if path_pixel_scale_x <= 0 or path_pixel_scale_y <= 0:
        return

    if is_path_pixel_scale_grid_view:
        color = (0, 0, 0, 255)

        with dpg.draw_node(tag=draw_widget_tag, parent=img_widget_tag):
            for x in range(0, img_w, path_pixel_scale_x):
                dpg.draw_line((x, 0), (x, img_h), color=color, thickness=1)

            for y in range(0, img_h, path_pixel_scale_y):
                dpg.draw_line((0, y), (img_w, y), color=color, thickness=1)

        for y in range(0, img_h, path_pixel_scale_y):
            for x in range(0, img_w, path_pixel_scale_x):
                dx = x + path_pixel_scale_x
                dy = y + path_pixel_scale_y
                is_break = False

                for list_tag in ["empty_space_list", "anchor_pos_list", "entrance_location_list"]:
                    data_list = global_data_dict[list_tag]
                    color = draw_helper.get_color(list_tag, 30)
                    for s_data in data_list:
                        data = tuple(map(int, s_data.split(",")))
                        if checker.check_coord_overlap((x + 1, y + 1, dx - x, dy - y), data):
                            draw_helper.draw_rectangle(x + 1, y + 1, dx, dy, color=color, fill=color, parent=draw_widget_tag)
                            is_break = True
                            break
                        if is_break:
                            break
                    if is_break:
                        break


def path_pixel_scale_slider_handler(sender: Union[int, str], axis_type: str):
    """축척 슬라이드 위젯 값 변경 콜백 처리

    Args:
        sender (Union[int, str]): 호출한 위젯 Tag
        axis_type (str): 축 타입 ('X' or 'Y')
    """

    axis_idx = 0
    if axis_type == "y":
        axis_idx = 1

    global_data_dict["path_pixel_scale"][axis_idx] = dpg.get_value(sender)

    refresh_path_pixel_scale_axis()


def refresh_path_pixel_scale_axis():
    """경로 축척 축 그래픽 갱신"""

    for axis_idx, axis_type in enumerate(["x", "y"]):
        dpg.configure_item(f"{axis_type}_path_pixel_scale_slider_int", default_value=global_data_dict["path_pixel_scale"][axis_idx])

        draw_widget_tag = f"{axis_type}_axis_draw_widget"

        if util.widget_check(draw_widget_tag):
            dpg.delete_item(draw_widget_tag)

        value = global_data_dict["path_pixel_scale"][axis_idx]
        p2 = (value, 0) if axis_type == "x" else (0, value)
        color = (255, 0, 0, 255) if axis_type == "x" else (0, 0, 255, 255)
        dpg.draw_line((0, 0), p2, color=color, thickness=3, tag=draw_widget_tag, parent=img_widget_tag)

    path_pixel_scale_grid_calculate()


def find_path():
    """경로 탐색"""

    s_entry_pos = current_state["entrance_location_list"]
    entry_pos_x, entry_pos_y = tuple(map(int, s_entry_pos.split(",")))

    pathfinder.find_path((entry_pos_x, entry_pos_y), lambda *args, **kwargs: draw_helper.DrawPathNode(*args, **kwargs, draw_parent_tag=img_widget_tag))


def clear_path():
    """탐색된 경로 초기화"""

    pathfinder.nodes_clear()


def app(image_path: str):
    """앱 실행 메인함수

    Args:
        image_path (str): 처리할 이미지 경로
    """

    global img_widget_tag, status_widget_tag, img_w, img_h

    dpg.create_context()

    with dpg.font_registry():
        with dpg.font(os.path.join("fonts", "D2Coding.ttc"), 16) as font1:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Korean)

    dpg.bind_font(font1)

    with dpg.window(label="Image Window", width=image_window_w, height=control_window_h, pos=(control_window_w + 5, 0)):
        img_tag, img_w, img_h = add_and_load_resized_image(image_path)
        with dpg.drawlist(width=img_w, height=img_h, tag=img_widget_tag):
            dpg.draw_image(img_tag, pmin=(0, 0), pmax=(img_w, img_h))
            dpg.draw_line((0, 0), (global_data_dict["path_pixel_scale"][0], 0), color=(255, 0, 0, 255), thickness=3, tag="x_axis_draw_widget")
            dpg.draw_line((0, 0), (0, global_data_dict["path_pixel_scale"][1]), color=(0, 0, 255, 255), thickness=3, tag="y_axis_draw_widget")

        img_widget_tag_handler = f"{img_widget_tag}_handler"

        with dpg.item_handler_registry(tag=img_widget_tag_handler):
            dpg.add_item_clicked_handler(callback=add_point)

        dpg.bind_item_handler_registry(img_widget_tag, img_widget_tag_handler)

    with dpg.window(label="Control Window", width=control_window_w, height=control_window_h):
        empty_space_list = global_data_dict["empty_space_list"]
        anchor_pos_list = global_data_dict["anchor_pos_list"]
        overlap_space_list = global_data_dict["overlap_space_list"]
        edge_list = global_data_dict["edge_list"]

        with dpg.collapsing_header(label="전처리", default_open=True):
            with dpg.group(horizontal=True, width=100):
                with dpg.group():
                    dpg.add_text("빈 자리 좌표")
                    dpg.add_listbox(empty_space_list, callback=lambda: list_seleted_handler("empty_space_list"), tag="empty_space_list")
                    dpg.add_button(label="제거", callback=lambda: remove_list_item_handler("empty_space_list"))

                with dpg.group():
                    dpg.add_text("앵커 좌표")
                    dpg.add_listbox(anchor_pos_list, callback=lambda: list_seleted_handler("anchor_pos_list"), tag="anchor_pos_list")
                    dpg.add_button(label="제거", callback=lambda: remove_list_item_handler("anchor_pos_list"))

                with dpg.group():
                    dpg.add_text("입구 좌표")
                    dpg.add_listbox(anchor_pos_list, callback=lambda: list_seleted_handler("entrance_location_list"), tag="entrance_location_list")
                    dpg.add_button(label="제거", callback=lambda: remove_list_item_handler("entrance_location_list"))

        with dpg.collapsing_header(label="물체검출", default_open=True):
            dpg.add_button(label="초기화", callback=lambda: detect_object("Clear"))

            with dpg.group(horizontal=True):
                dpg.add_button(label="YOLO 적용", callback=lambda: detect_object("YOLO"))
                # dpg.add_button(label="SVM", callback=lambda: detect_object("SVM"))

                dpg.add_combo(["YOLOv8n", "YOLOv8s", "YOLOv8m", "YOLOv8l", "YOLOv8x"], default_value=current_state["yolo_model_name"], callback=select_yolo_model_handler)

        with dpg.collapsing_header(label="경로탐색", default_open=True):
            dpg.add_checkbox(
                label="그리드 뷰",
                callback=lambda: path_pixel_scale_grid_view_checkbox_handler(),
            )
            with dpg.group(width=200):
                dpg.add_slider_int(
                    label="1m 픽셀 축척 (X)",
                    min_value=5,
                    max_value=img_w,
                    callback=lambda s, d: path_pixel_scale_slider_handler(s, "x"),
                    default_value=global_data_dict["path_pixel_scale"][0],
                    tag="x_path_pixel_scale_slider_int",
                )
                dpg.add_slider_int(
                    label="1m 픽셀 축척 (Y)",
                    min_value=5,
                    max_value=img_h,
                    callback=lambda s, d: path_pixel_scale_slider_handler(s, "y"),
                    default_value=global_data_dict["path_pixel_scale"][1],
                    tag="y_path_pixel_scale_slider_int",
                )

            with dpg.group():
                dpg.add_text("간선 좌표")
                dpg.add_listbox(edge_list, callback=lambda: list_seleted_handler("edge_list"), tag="edge_list")
                dpg.add_button(label="제거", callback=lambda: remove_list_item_handler("edge_list"))

            with dpg.group(horizontal=True):
                dpg.add_button(label="실행", callback=lambda: find_path())
                dpg.add_button(label="초기화", callback=lambda: clear_path())

        with dpg.collapsing_header(label="결과", default_open=True):
            dpg.add_text(f"총 공간: {len(empty_space_list)}\n- 차량 존재: {len(overlap_space_list)}\n= 빈 공간: {len(empty_space_list) - len(overlap_space_list)}", tag=status_widget_tag)

        with dpg.collapsing_header(label="기타", default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_button(label="저장", callback=lambda: (logic.save_data()))
                dpg.add_button(label="불러오기", callback=lambda: (logic.clear_data(), logic.load_data(), refresh_select(), refresh_draw()))
                dpg.add_button(label="초기화", callback=lambda: (logic.clear_data(), refresh_draw()))

    dpg.create_viewport(title="PLS - Parking Lot Service", width=1700, height=800)

    # dpg.show_metrics()

    dpg.bind_theme(theme.create_theme_imgui_dark())

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    image_path = "images/image01.png"
    app(image_path)
