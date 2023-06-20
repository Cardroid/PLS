from typing import Any, Optional, Union
import cv2
import numpy as np

try:
    import dearpygui.dearpygui as dpg
except:
    pass


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


def dpg_set_value(tag: Union[int, str], value: Any):
    """위젯의 값 변경 처리 (위젯이 없을 경우, 변경 안함)

    Args:
        tag (Union[int, str]): 위젯 Tag
        value (Any): 값
    """

    if widget_check(tag):
        dpg.set_value(tag, value)


def widget_check(tag: Union[int, str]):
    """위젯 존재 및 사용가능 여부 체크

    Args:
        tag (Union[int, str]): 위젯 Tag

    Returns:
        _type_: 존재 및 사용 가능 여부
    """

    if dpg.does_item_exist(tag):
        try:
            return dpg.is_item_ok(tag)
        except:
            return False
    else:
        return False
