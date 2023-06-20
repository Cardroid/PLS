from typing import Tuple


def check_coord_overlap(box_xywh: Tuple[float, float, float, float], point_xy: Tuple[float, float]) -> bool:
    """사각형 좌표와 점 좌표의 겹침 체크

    Args:
        box_xywh (Tuple[float, float, float, float]): 사각형 좌표 (좌상단 좌표(X, Y) 및 사각형의 크기(가로, 세로))
        point_xy (Tuple[float, float]): 점 좌표 (X, Y)

    Returns:
        bool: 겹칠 경우 True 아닐 경우, False
    """
    p_x, p_y = point_xy
    b_x, b_y, b_w, b_h = box_xywh

    if b_x <= p_x <= b_x + b_w and b_y <= p_y <= b_y + b_h:
        return True
    return False
