import math
from typing import Tuple
import dearpygui.dearpygui as dpg

import util
import pathfinder


# 색 사전
COLOR_DICT = {
    "entrance_location_list": (255, 30, 200),
    "empty_space_list": (255, 0, 0),
    "anchor_pos_list": (0, 0, 255),
    "overlap_space_list": (255, 255, 0),
    "object_car": (0, 255, 255),
    "object_other": (255, 255, 255),
}


class DrawPathNode(pathfinder.PathNode):
    """그래픽 그리기 기능이 있는 PathNode"""

    def __init__(self, x: int, y: int, node_type: str, draw_parent_tag) -> None:
        super().__init__(x, y, node_type)

        self.draw_tag = f"{node_type}_{x}_{y}"
        self.draw_parent_tag = draw_parent_tag

    def __del__(self):
        if util.widget_check(self.draw_tag):
            dpg.delete_item(self.draw_tag)


def get_color(list_tag: str, alpha=255) -> Tuple[int, int, int, int]:
    """리스트 Tag에 맞는 색 가져오기

    Args:
        list_tag (str): 리스트 Tag
        alpha (int, optional): 알파값 (투명도). Defaults to 255.

    Returns:
        Tuple[int, int, int, int]: (Red, Green, Blue, Alpha)
    """

    global COLOR_DICT

    return (*COLOR_DICT[list_tag], alpha)


def draw_circle(x: int, y: int, radius: int, **kwargs):
    """원 그래픽 그리기

    Args:
        x (int): 중앙 좌표 X
        y (int): 중앙 좌표 Y
        radius (int): 반지름
    """

    dpg.draw_circle((x, y), radius, **kwargs)


def draw_rectangle(x: int, y: int, dx: int, dy: int, **kwargs):
    """사각형 그래픽 그리기

    Args:
        x (int): 좌상단 X
        y (int): 좌상단 Y
        dx (int): 우하단 X
        dy (int): 우하단 Y
    """

    dpg.draw_rectangle((x, y), (dx, dy), **kwargs)


def draw_polygon(x: int, y: int, radius: int, point_num: int, **kwargs):
    """다각형 그래픽 그리기

    Args:
        x (int): 중앙 좌표 X
        y (int): 중앙 좌표 Y
        radius (int): 반지름
        point_num (int): 다각형의 꼭짓점 개수
    """
    points = []

    for i in range(point_num):
        angle = 2 * math.pi * i / point_num
        i_x = math.cos(angle) * radius
        i_y = math.sin(angle) * radius
        points.append((x + i_x, y + i_y))

    dpg.draw_polyline(points, closed=True, **kwargs)
