import math
import dearpygui.dearpygui as dpg


def draw_circle(x, y, radius, **kwargs):
    dpg.draw_circle((x, y), radius, **kwargs)


def draw_rectangle(x, y, dx, dy, **kwargs):
    dpg.draw_rectangle((x, y), (dx, dy), **kwargs)


def draw_hexagon(x, y, radius, point_num: int, **kwargs):
    points = []

    for i in range(point_num):
        angle = 2 * math.pi * i / point_num
        i_x = math.cos(angle) * radius
        i_y = math.sin(angle) * radius
        points.append((x + i_x, y + i_y))

    dpg.draw_polyline(points, closed=True, **kwargs)
