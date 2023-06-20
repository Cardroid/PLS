import math
import dearpygui.dearpygui as dpg

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
