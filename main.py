import os
import pickle
import time
from typing import Any, Dict, List, Tuple, Union
import cv2
import dearpygui.dearpygui as dpg

import logic
import checker
import draw_helper
import util

split_width = lambda x: control_window_w // x - 5 * x

control_window_w = 350
control_window_h = 600

image_window_w = 1300
image_window_h = 600


pos_offset_x = control_window_w - 20

current_state = {
    "empty_space_list": 0,
    "anchor_pos_list": 0,
    "draw_dict": {
        "shape": {
            "entrance_location_list": lambda *args, **kwargs: draw_helper.draw_circle(radius=5, color=(255, 30, 200, 255), fill=(255, 30, 200, 255), *args, **kwargs),
            "empty_space_list": lambda *args, **kwargs: draw_helper.draw_circle(radius=5, color=(255, 0, 0, 255), fill=(255, 0, 0, 255), *args, **kwargs),
            "anchor_pos_list": lambda *args, **kwargs: draw_helper.draw_circle(radius=5, color=(0, 0, 255, 255), fill=(0, 0, 255, 255), *args, **kwargs),
            "overlap_space_list": lambda *args, **kwargs: draw_helper.draw_hexagon(point_num=6, radius=25, color=(255, 255, 0, 255), *args, **kwargs),
            "object_car": lambda *args, **kwargs: draw_helper.draw_rectangle(color=(0, 255, 255, 255), *args, **kwargs),
            "object_other": lambda *args, **kwargs: draw_helper.draw_rectangle(color=(255, 255, 255, 255), *args, **kwargs),
        },
    },
}

object_data = []
draw_tag_set = set([])

img_widget_tag = "image_widget"
status_widget_tag = "status_text_widget"


def list_seleted_handler(tag):
    global current_state

    current_state[tag] = dpg.get_value(tag)


def remove_list_item_handler(source_dict: Dict[str, List[Any]], list_tag: str):
    item = dpg.get_value(list_tag)
    source_list = source_dict[list_tag]
    if item in source_list:
        item_idx = source_list.index(item)
        update_pos_list(list_tag, item, True)
        dpg.configure_item(list_tag, items=source_list)

        if len(source_list) > 0:
            if item_idx >= len(source_list):
                item_idx = len(source_list) - 1

            current_select_item = source_list[item_idx]
            current_state[list_tag] = current_select_item
            dpg.configure_item(list_tag, default_value=current_select_item)


def add_and_load_resized_image(image_path: str, small_window_w: Union[int, None] = None, small_window_h: Union[int, None] = None):
    global prev_image_path, is_image_widget_init, img_w, img_h

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
        import yolo_helper

        object_data = yolo_helper.use_yolo(image_path)[0]

    for cls, (x, y, w, h) in object_data:
        cls = cls if cls == "car" else "other"
        draw_tag = f"object_{cls}_{x}_{y}_{w}_{h}"
        func = current_state["draw_dict"]["shape"][f"object_{cls}"]
        func(x, y, x + w, y + h, thickness=5, tag=draw_tag, parent=img_widget_tag)

    overlap_space_list_refresh()


def add_point(sender, data):
    btn_type, _ = data

    if 0 <= btn_type <= 2:
        x, y = tuple(map(int, dpg.get_mouse_pos()))
        x -= 8
        y -= 8

        if btn_type == 0:
            list_tag = "empty_space_list"
        elif btn_type == 1:
            list_tag = "anchor_pos_list"
        elif btn_type == 2:
            list_tag = "entrance_location_list"

        update_pos_list(list_tag, (x, y), False)
        dpg.configure_item(list_tag, items=logic.data_dict[list_tag])

        source_list = logic.data_dict[list_tag]
        current_select_item = source_list[len(source_list) - 1]
        current_state[list_tag] = current_select_item
        dpg.configure_item(list_tag, default_value=current_select_item)


def update_pos_list(list_tag: str, obj: Union[str, Tuple[int, int]], is_delete: bool = False):
    global current_state

    if isinstance(obj, str):
        obj = tuple(map(int, obj.split(",")))

    x, y = obj
    draw_tag = f"{list_tag}_{x}_{y}"

    if is_delete:
        dpg.delete_item(item=draw_tag)
        draw_tag_set.remove(draw_tag)

        idx = logic.data_dict[list_tag].index(f"{x}, {y}")
        del logic.data_dict[list_tag][idx]
    else:
        func = current_state["draw_dict"]["shape"][list_tag]
        func(x, y, thickness=5, tag=draw_tag, parent=img_widget_tag)
        draw_tag_set.add(draw_tag)

        logic.data_dict[list_tag].append(f"{x}, {y}")

    overlap_space_list_refresh()

    empty_space_list = logic.data_dict["empty_space_list"]
    overlap_space_list = logic.data_dict["overlap_space_list"]
    dpg.configure_item(status_widget_tag, default_value=f"총 공간: {len(empty_space_list)}\n- 차량 존재: {len(overlap_space_list)}\n= 빈 공간: {len(empty_space_list) - len(overlap_space_list)}")


def refresh_draw():
    global current_state, object_data

    for draw_tag in draw_tag_set:
        dpg.delete_item(item=draw_tag)

    draw_tag_set.clear()

    for list_tag in ["empty_space_list", "anchor_pos_list"]:
        data_list = logic.data_dict[list_tag]
        func = current_state["draw_dict"]["shape"][list_tag]

        for data in data_list:
            obj = tuple(map(int, data.split(",")))
            x, y = obj
            draw_tag = f"{list_tag}_{x}_{y}"

            func(x, y, thickness=5, tag=draw_tag, parent=img_widget_tag)
            draw_tag_set.add(draw_tag)

        dpg.configure_item(list_tag, items=data_list)

    overlap_space_list_refresh()

    empty_space_list = logic.data_dict["empty_space_list"]
    overlap_space_list = logic.data_dict["overlap_space_list"]
    dpg.configure_item(status_widget_tag, default_value=f"총 공간: {len(empty_space_list)}\n- 차량 존재: {len(overlap_space_list)}\n= 빈 공간: {len(empty_space_list) - len(overlap_space_list)}")


def overlap_space_list_refresh():
    global current_state, object_data

    list_tag = "overlap_space_list"

    overlap_space_list = logic.data_dict[list_tag]

    for overlap_space in overlap_space_list:
        dpg.delete_item(item=f"{list_tag}_{overlap_space[1]}")

    empty_space_list = logic.data_dict["empty_space_list"]
    func = current_state["draw_dict"]["shape"][list_tag]

    overlap_space_list.clear()
    for data in object_data:
        cls, (x, y, w, h) = data

        for empty_space in empty_space_list:
            empty_space_pos = tuple(map(int, empty_space.split(",")))
            if checker.check_coord_overlap((x, y, w, h), empty_space_pos):
                draw_tag = f"{list_tag}_{empty_space_pos}"
                overlap_space_list.append((cls, empty_space_pos))

                func(empty_space_pos[0], empty_space_pos[1], thickness=5, tag=draw_tag, parent=img_widget_tag)


def app(image_path: str):
    global img_widget_tag, status_widget_tag

    dpg.create_context()

    with dpg.font_registry():
        with dpg.font(os.path.join("fonts", "D2Coding.ttc"), 20) as font1:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Korean)

    dpg.set_global_font_scale(0.8)
    dpg.bind_font(font1)

    with dpg.window(label="Control Window", width=control_window_w, height=control_window_h):
        empty_space_list = logic.data_dict["empty_space_list"]
        anchor_pos_list = logic.data_dict["anchor_pos_list"]
        overlap_space_list = logic.data_dict["overlap_space_list"]

        with dpg.collapsing_header(label="전처리", default_open=True):
            with dpg.group(horizontal=True, width=100):
                with dpg.group():
                    dpg.add_text("빈 자리 좌표")
                    dpg.add_listbox(empty_space_list, callback=lambda: list_seleted_handler("empty_space_list"), tag="empty_space_list")
                    dpg.add_button(label="제거", callback=lambda: remove_list_item_handler(logic.data_dict, "empty_space_list"))

                with dpg.group():
                    dpg.add_text("앵커 좌표")
                    dpg.add_listbox(anchor_pos_list, callback=lambda: list_seleted_handler("anchor_pos_list"), tag="anchor_pos_list")
                    dpg.add_button(label="제거", callback=lambda: remove_list_item_handler(logic.data_dict, "anchor_pos_list"))

                with dpg.group():
                    dpg.add_text("입구 좌표")
                    dpg.add_listbox(anchor_pos_list, callback=lambda: list_seleted_handler("entrance_location_list"), tag="entrance_location_list")
                    dpg.add_button(label="제거", callback=lambda: remove_list_item_handler(logic.data_dict, "entrance_location_list"))

        with dpg.collapsing_header(label="물체검출", default_open=True):
            dpg.add_button(label="초기화", callback=lambda: detect_object("Clear"))

            with dpg.group(horizontal=True):
                dpg.add_button(label="YOLO 적용", callback=lambda: detect_object("YOLO"))
                # dpg.add_button(label="SVM", callback=lambda: detect_object("SVM"))

        with dpg.collapsing_header(label="결과", default_open=True):
            dpg.add_text(f"총 공간: {len(empty_space_list)}\n- 차량 존재: {len(overlap_space_list)}\n= 빈 공간: {len(empty_space_list) - len(overlap_space_list)}", tag=status_widget_tag)

        with dpg.collapsing_header(label="기타", default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_button(label="저장", callback=lambda: (logic.save_data()))
                dpg.add_button(label="불러오기", callback=lambda: (logic.clear_data(), logic.load_data(), refresh_draw()))
                dpg.add_button(label="초기화", callback=lambda: (logic.clear_data(), refresh_draw()))

    with dpg.window(label="Image Window", width=image_window_w, height=control_window_h, pos=(control_window_w + 5, 0)):
        img_tag, img_w, img_h = add_and_load_resized_image(image_path)

        with dpg.drawlist(width=img_w, height=img_h, tag=img_widget_tag):
            dpg.draw_image(img_tag, pmin=(0, 0), pmax=(img_w, img_h))

        img_widget_tag_handler = f"{img_widget_tag}_handler"

        with dpg.item_handler_registry(tag=img_widget_tag_handler):
            dpg.add_item_clicked_handler(callback=add_point)

        dpg.bind_item_handler_registry(img_widget_tag, img_widget_tag_handler)

    dpg.create_viewport(title="PLS - Parking Lot Service", width=1700, height=800)

    dpg.show_metrics()
    dpg.show_debug()
    dpg.show_font_manager()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    image_path = "images/image01.png"
    app(image_path)
