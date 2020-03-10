import sys
import glfw
from OpenGL.GL import *
import pyrr
import time

import context
import keyboard_handling
import mouse_handling


class TronWindow:
    def __init__(self, camera_id, **kwargs):
        self.id = len(context.main_context.windows)
        # OpenGL ID:
        self.opengl_id = None
        self.window_name = None
        self.window_width = None
        self.window_height = None
        self.aspect_ratio = None

        self.background_color_r = 0.0
        self.background_color_g = 0.0
        self.background_color_b = 0.0
        self.background_color_alpha = 1.0

        self.camera_list = []
        self.camera_list.append(camera_id)
        self.main_camera_iterator = 0

        self.create(**kwargs)

        context.main_context.load_shaders()

        def sample_function():
            pass

        self.user_function = sample_function

        self.time_pr = time.time_ns()
        self.total_ms = 0
        self.total_frames = 0

    def add_camera(self, camera_id):
        self.camera_list.append(camera_id)

    def choose_camera(self, **kwargs):
        it = kwargs.get('iterator', -1)

        if it != -1:
            self.main_camera_iterator = it

        camera_projection_matrix = pyrr.matrix44.create_perspective_projection_matrix(60.0, self.aspect_ratio, 0.001, 1000.0)
        context.main_context.cameras[self.camera_list[self.main_camera_iterator]].camera_projection_matrix = camera_projection_matrix
        #glfw.set_cursor_pos_callback(self.opengl_id, context.main_context.cameras[self.camera_list[self.main_camera_iterator]].mouse_callback)
        glfw.set_cursor_pos_callback(self.opengl_id, mouse_handling.mouse_callback)

    def create(self, **kwargs):
        self.window_width = kwargs.get('width', 800)
        self.window_height = kwargs.get('height', 600)
        self.window_name = kwargs.get('name', "My OpenGL window")
        self.opengl_id = glfw.create_window(self.window_width, self.window_height, self.window_name, None, None)

        glfw.set_window_size_callback(self.opengl_id, self.window_resize)
        glfw.set_key_callback(self.opengl_id, keyboard_handling.key_callback)
        #glfw.set_cursor_pos_callback(self.opengl_id, context.main_context.cameras[self.camera_list[self.main_camera_iterator]].mouse_callback)
        glfw.set_cursor_pos_callback(self.opengl_id, mouse_handling.mouse_callback)
        glfw.set_input_mode(self.opengl_id, glfw.CURSOR, glfw.CURSOR_DISABLED)

        if not self.opengl_id:
            print("(!) TRON FATAL ERROR: Failed to create b window")
            glfw.terminate()
            sys.exit(2)

        self.activate()
        glfw.swap_interval(1)

        self.window_resize(self.opengl_id, self.window_width, self.window_height)
        glClearColor(self.background_color_r, self.background_color_g,
                     self.background_color_b, self.background_color_alpha)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glfw.swap_buffers(self.opengl_id)

    def activate(self):
        glfw.make_context_current(self.opengl_id)

    def draw(self):
        self.time_pr = time.time_ns()

        context.main_context.current_window = self.id
        context.main_context.current_camera = self.camera_list[self.main_camera_iterator]

        self.activate()

        self.user_function()

        cam = context.main_context.cameras[self.camera_list[self.main_camera_iterator]]
        cam.process_keyboard()
        cam.process_camera()
        cam.camera_view_matrix = cam.get_view_matrix()

        # USER INTERACTION STATE
        mouse_handling.drop_state()
        glfw.poll_events()
        glClearColor(self.background_color_r, self.background_color_g,
                     self.background_color_b, self.background_color_alpha)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # ##########

        glCullFace(GL_FRONT)
        context.main_context.num_active_lights = 0
        for i in context.main_context.lights:
            if i.hided == 0:
                i.update_shade_map()
                context.main_context.num_active_lights += 1
        glCullFace(GL_BACK)

        # TODO: make this a debug mode switch =)
        if 1:
            glViewport(0, 0, self.window_width, self.window_height)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            for i in context.main_context.objects2D:
                i.draw()
            for i in context.main_context.objects:
                if i.hided == 0:
                    i.real_draw()

        glfw.swap_buffers(self.opengl_id)

        # TODO: make this not an exit, but just closing the window:
        if glfw.window_should_close(self.opengl_id):
            sys.exit(0)

        add = (time.time_ns() - self.time_pr) / 10**6
        self.total_ms += add
        self.total_frames += 1
        #print("TRON info: loop took ", add, " ms || AVG: ", self.total_ms/ self.total_frames)

    def window_resize(self, window, width, height):
        glViewport(0, 0, width, height)

        self.aspect_ratio = width / height

        camera_projection_matrix = pyrr.matrix44.create_perspective_projection_matrix(60.0, self.aspect_ratio, 0.001, 1000.0)

        context.main_context.cameras[self.camera_list[self.main_camera_iterator]].camera_projection_matrix = camera_projection_matrix
