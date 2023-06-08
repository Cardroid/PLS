import os
import imgui
import glfw
import pygame
import OpenGL.GL as gl
from imgui.integrations.glfw import GlfwRenderer


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
        global texture_id, img_width, img_height

        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            self.impl.process_inputs()
            imgui.new_frame()
            imgui.set_next_window_size(400, 600)
            imgui.set_next_window_position(5, 5)
            imgui.begin("Main window", True)

            imgui.text("검출")

            if imgui.button("물체 검출"):
                print(f"String: {self.string}")
                print(f"Float: {self.f}")

            imgui.show_test_window()

            imgui.end()

            imgui.set_next_window_size(img_width, img_height + 50)
            imgui.set_next_window_position(410, 5)

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
                imgui.begin_tooltip()
                region_sz = 32.0
                region_x = imgui.get_mouse_position().x - pos.x - region_sz * 0.5
                if region_x < 0.0:
                    region_x = 0.0
                elif region_x > img_width - region_sz:
                    region_x = img_width - region_sz
                region_y = imgui.get_mouse_position().y - pos.y - region_sz * 0.5
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

            imgui.end()

            imgui.render()

            gl.glClearColor(*self.backgroundColor)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)

            self.impl.render(imgui.get_draw_data())
            glfw.swap_buffers(self.window)

        self.impl.shutdown()
        glfw.terminate()


if __name__ == "__main__":
    global texture_id, img_width, img_height

    window = impl_glfw_init("PLS - Parking Lot Service")

    image_path = "images/image01.png"

    texture_id, img_width, img_height = load_image(image_path)

    gui = GUI(window)
