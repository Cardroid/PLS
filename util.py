import cv2
import numpy as np


def convert_cv_to_dpg(image, width, height):
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
