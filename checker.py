from typing import Tuple


def check_coord_overlap(box_xywh: Tuple[float, float, float, float], point_xy: Tuple[float, float]) -> bool:
    p_x, p_y = point_xy
    b_x, b_y, b_w, b_h = box_xywh

    if b_x <= p_x <= b_x + b_w and b_y <= p_y <= b_y + b_h:
        return True
    return False
