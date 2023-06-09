import os
import pickle
import imgui
import glfw
import pygame
import time
import OpenGL.GL as gl
from imgui.integrations.glfw import GlfwRenderer
import checker
import yolo_helper

split_width = lambda x: control_panel_width // x - 5 * x

control_panel_width = 400
control_panel_height = 600

empty_space_list = []
empty_space_list_current = -1

anchor_pos_list = []
anchor_pos_list_current = -1

overlap_space_list = []

yolo_data = []


def impl_glfw_init(window_name, width=1700, height=800):
    if not glfw.init():
        print("Could not initialize OpenGL context")
        exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    window = glfw.create_window(int(width), int(height), window_name, None, None)
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        exit(1)

    return window


def load_image(image_name):
    image = pygame.image.load(image_name)
    textureSurface = pygame.transform.flip(image, False, True)

    textureData = pygame.image.tostring(textureSurface, "RGBA", 1)

    width = textureSurface.get_width()
    height = textureSurface.get_height()

    texture = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
    gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, textureData)

    return texture, width, height


def save_data(filepath="data.pickle"):
    global empty_space_list, anchor_pos_list

    save_data = {
        "empty_space_list": empty_space_list,
        "anchor_pos_list": anchor_pos_list,
    }

    with open(filepath, "wb") as f:
        pickle.dump(save_data, f)


def load_data(filepath="data.pickle"):
    global empty_space_list, anchor_pos_list

    if not os.path.exists(filepath):
        return

    with open(filepath, "rb") as f:
        load_data = pickle.load(f)

    empty_space_list.extend(load_data["empty_space_list"])
    anchor_pos_list.extend(load_data["anchor_pos_list"])


def create_control_panel():
    global control_panel_width, control_panel_height
    global texture_id, img_width, img_height, image_path
    global empty_space_list, empty_space_list_current
    global anchor_pos_list, anchor_pos_list_current
    global overlap_space_list
    global yolo_data

    imgui.set_next_window_size(control_panel_width, control_panel_height)
    imgui.set_next_window_position(5, 5)
    imgui.begin("Main window", True)

    imgui.push_item_width(split_width(2))
    imgui.begin_group()
    imgui.text(f"빈 자리 좌표 ({len(empty_space_list)})")
    empty_space_changed, empty_space_list_current = imgui.listbox(
        label="##빈 자리 좌표",
        current=empty_space_list_current,
        items=empty_space_list,
        height_in_items=3,
    )
    if imgui.button("제거##빈 자리 좌표") and empty_space_list_current >= 0:
        del empty_space_list[empty_space_list_current]
        if empty_space_list_current >= len(empty_space_list):
            empty_space_list_current = len(empty_space_list) - 1
    imgui.end_group()
    imgui.same_line()
    imgui.begin_group()
    imgui.text(f"앵커 좌표 ({len(anchor_pos_list)})")
    anchor_pos_changed, anchor_pos_list_current = imgui.listbox(
        label="##앵커 좌표",
        current=anchor_pos_list_current,
        items=anchor_pos_list,
        height_in_items=3,
    )
    if imgui.button("제거##앵커 좌표") and anchor_pos_list_current >= 0:
        del anchor_pos_list[anchor_pos_list_current]
        if anchor_pos_list_current >= len(anchor_pos_list):
            anchor_pos_list_current = len(anchor_pos_list) - 1
    imgui.end_group()
    imgui.pop_item_width()

    imgui.text("\n물체 검출")

    if imgui.button("YOLO 적용"):
        print(f"YOLO running...")
        yolo_data = yolo_helper.use_yolo(image_path)[0]
    # imgui.same_line()
    # if imgui.button("SVM 적용"):
    #     print(f"SVM running...")

    imgui.text(f"\n총 공간: {len(empty_space_list)}\n- 차량 존재: {len(overlap_space_list)}\n= 빈 공간: {len(empty_space_list) - len(overlap_space_list)}")

    imgui.text("\n저장 및 불러오기")

    if imgui.button("저장"):
        save_data()
    imgui.same_line()
    if imgui.button("불러오기"):
        load_data()

    imgui.end()


def create_image_view_panel():
    global control_panel_width, control_panel_height
    global texture_id, img_width, img_height, image_path
    global empty_space_list, empty_space_list_current
    global anchor_pos_list, anchor_pos_list_current
    global overlap_space_list
    global yolo_data

    imgui.set_next_window_size(img_width, img_height + 50)
    imgui.set_next_window_position(control_panel_width + 10, 5)
    imgui.begin("Image window", True)

    pos = imgui.get_cursor_screen_pos()
    imgui.image(
        texture_id=texture_id,
        width=img_width,
        height=img_height,
        uv0=(0, 0),
        uv1=(1, 1),
        tint_color=(255, 255, 255, 255),
        border_color=(255, 255, 255, 128),
    )
    if imgui.is_item_hovered():
        mouse_pos = imgui.get_mouse_position()

        if imgui.is_mouse_clicked(0):
            empty_space_list.append(f"{int(mouse_pos.x)}, {int(mouse_pos.y)}")
            empty_space_list_current = len(empty_space_list) - 1
        elif imgui.is_mouse_clicked(1):
            anchor_pos_list.append(f"{int(mouse_pos.x)}, {int(mouse_pos.y)}")
            anchor_pos_list_current = len(anchor_pos_list) - 1

        imgui.begin_tooltip()
        region_sz = 32.0
        region_x = mouse_pos.x - pos.x - region_sz * 0.5
        if region_x < 0.0:
            region_x = 0.0
        elif region_x > img_width - region_sz:
            region_x = img_width - region_sz
        region_y = mouse_pos.y - pos.y - region_sz * 0.5
        if region_y < 0.0:
            region_y = 0.0
        elif region_y > img_height - region_sz:
            region_y = img_height - region_sz
        zoom = 4.0
        imgui.text(f"Min: ({region_x}, {region_y})")
        imgui.text(f"Max: ({region_x + region_sz}, {region_y + region_sz})")

        uv0 = ((region_x) / img_width, (region_y) / img_height)
        uv1 = (
            (region_x + region_sz) / img_width,
            (region_y + region_sz) / img_height,
        )
        imgui.image(
            texture_id=texture_id,
            width=region_sz * zoom,
            height=region_sz * zoom,
            uv0=uv0,
            uv1=uv1,
            tint_color=(255, 255, 255, 255),
            border_color=(255, 255, 255, 128),
        )
        imgui.end_tooltip()

    draw_list = imgui.get_window_draw_list()
    for pos in empty_space_list:
        x, y = tuple(map(int, pos.split(",")))
        draw_list.add_circle_filled(x, y, 5, imgui.get_color_u32_rgba(0, 0, 1, 1))
    for pos in anchor_pos_list:
        x, y = tuple(map(int, pos.split(",")))
        draw_list.add_circle_filled(x, y, 5, imgui.get_color_u32_rgba(1, 0, 0, 1))

    overlap_space_list.clear()
    for data in yolo_data:
        cls = data[0]
        x, y, w, h = data[1]

        x += control_panel_width - 20

        if cls == "car":
            draw_list.add_rect(x, y, x + w, y + h, imgui.get_color_u32_rgba(0, 1, 0, 1), thickness=3)
        else:
            draw_list.add_rect(x, y, x + w, y + h, imgui.get_color_u32_rgba(1, 1, 1, 1), thickness=3)

        for empty_space in empty_space_list:
            empty_space_pos = tuple(map(int, empty_space.split(",")))
            if checker.check_coord_overlap((x, y, w, h), empty_space_pos):
                overlap_space_list.append(empty_space_pos)

    for x, y in overlap_space_list:
        draw_list.add_ngon(x, y, 30, imgui.get_color_u32_rgba(1, 1, 0, 1), 6, 5)

    imgui.end()


class GUI(object):
    def __init__(self, window):
        super().__init__()
        self.backgroundColor = (0, 0, 0, 1)
        self.window = window
        gl.glClearColor(*self.backgroundColor)
        imgui.create_context()
        self.impl = GlfwRenderer(self.window)

        io = imgui.get_io()
        io.fonts.clear()
        self.font = io.fonts.add_font_from_file_ttf(os.path.join("fonts", "D2Coding.ttc"), 20, glyph_ranges=io.fonts.get_glyph_ranges_korean())
        self.impl.refresh_font_texture()

        self.loop()

    def loop(self):
        global control_panel_width, control_panel_height
        global texture_id, img_width, img_height, image_path
        global empty_space_list, empty_space_list_current
        global anchor_pos_list, anchor_pos_list_current
        global overlap_space_list
        global yolo_data

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            self.impl.process_inputs()
            imgui.new_frame()

            # imgui.show_test_window()

            create_control_panel()

            create_image_view_panel()

            imgui.render()

            gl.glClearColor(*self.backgroundColor)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)

            self.impl.render(imgui.get_draw_data())
            glfw.swap_buffers(self.window)

            time.sleep(0.01)

        self.impl.shutdown()
        glfw.terminate()


if __name__ == "__main__":
    global texture_id, img_width, img_height, image_path

    window = impl_glfw_init("PLS - Parking Lot Service")

    image_path = "images/image01.png"

    texture_id, img_width, img_height = load_image(image_path)

    gui = GUI(window)
