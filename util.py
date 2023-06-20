from typing import Any, Optional, Union
import cv2
import numpy as np


def convert_cv_to_dpg(image: np.ndarray, width: Optional[int], height: Optional[int]) -> np.ndarray:
    """OpenCV로 로드된 이미지를 GUI의 택스쳐 데이터로 변환 처리

    Args:
        image (np.ndarray): 이미지 데이터
        width (Optional[int]): 가로 사이즈
        height (Optional[int]): 세로 사이즈

    Returns:
        np.ndarray: 텍스쳐 데이터
    """

    if width is not None and height is not None:
        dst_image = cv2.resize(image, (width, height))
    else:
        dst_image = image

    data = np.flip(dst_image, 2)
    data = data.ravel()
    data = np.asfarray(data, dtype="f")

    texture_data = np.true_divide(data, 255.0)

    return texture_data


def dpg_set_value(tag, value):
    import dearpygui.dearpygui as dpg

    if dpg.does_item_exist(tag):
        dpg.set_value(tag, value)
