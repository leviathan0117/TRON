import sys
import glfw
from OpenGL.GL import *
import pyrr
import time
import math

import shader_handling
import context
import structure_handling
import object_handling
import file_handling
import light_handling
import keyboard_handling

from file_handling import TronFileHandler
from object_handling import TronObject
from context import main_context
from light_handling import TronDirectionalLight


class TronCamera:
    def __init__(self):
        self.id = len(context.main_context.cameras)

        self.camera_pos = pyrr.Vector3([0.0, 0.0, 0.0])
        self.camera_front = pyrr.Vector3([0.0, 0.0, -1.0])
        self.camera_up = pyrr.Vector3([0.0, 1.0, 0.0])
        self.camera_right = pyrr.Vector3([1.0, 0.0, 0.0])

        self.mouse_sensitivity = 0.25
        self.movement_speed = 0.1
        self.yaw = 0.0
        self.pitch = 0.0

        self.first_mouse = True
        self.lastX = None
        self.lastY = None

        self.camera_projection_matrix = None
        self.camera_view_matrix = None

    def get_view_matrix(self):
        return pyrr.matrix44.create_look_at(self.camera_pos, self.camera_pos + self.camera_front, self.camera_up)

    def process_keyboard(self):
        if keyboard_handling.keys[glfw.KEY_W]:
            self.camera_pos += self.camera_front * self.movement_speed
        if keyboard_handling.keys[glfw.KEY_S]:
            self.camera_pos -= self.camera_front * self.movement_speed
        if keyboard_handling.keys[glfw.KEY_A]:
            self.camera_pos -= self.camera_right * self.movement_speed
        if keyboard_handling.keys[glfw.KEY_D]:
            self.camera_pos += self.camera_right * self.movement_speed
        if keyboard_handling.keys[glfw.KEY_SPACE]:
            self.camera_pos += self.camera_up * self.movement_speed
        if keyboard_handling.keys[glfw.KEY_C]:
            self.camera_pos -= self.camera_up * self.movement_speed

    def turn_camera(self, offset_x, offset_y):
        offset_x *= self.mouse_sensitivity
        offset_y *= self.mouse_sensitivity

        self.yaw += offset_x
        self.pitch += offset_y

        if self.pitch > 89.9:
            self.pitch = 89.9
        if self.pitch < -89.9:
            self.pitch = -89.9

        self.update_camera_vectors()

    def update_camera_vectors(self):
        front = pyrr.Vector3([0.0, 0.0, 0.0])
        front.x = math.cos(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        front.y = math.sin(math.radians(self.pitch))
        front.z = math.sin(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))

        self.camera_front = pyrr.vector.normalise(front)
        self.camera_right = pyrr.vector.normalise(pyrr.vector3.cross(self.camera_front, pyrr.Vector3([0.0, 1.0, 0.0])))
        self.camera_up = pyrr.vector.normalise(pyrr.vector3.cross(self.camera_right, self.camera_front))

    def mouse_callback(self, window, xpos, ypos):
        if self.first_mouse:
            self.lastX = xpos
            self.lastY = ypos
            self.first_mouse = False

        offset_x = xpos - self.lastX
        offset_y = self.lastY - ypos

        self.lastX = xpos
        self.lastY = ypos

        self.turn_camera(offset_x, offset_y)


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

        self.camera_id = camera_id

        self.create(**kwargs)

        context.main_context.load_shaders()

        def sample_function():
            pass

        self.user_function = sample_function

        self.time_pr = time.time_ns()
        self.total_ms = 0
        self.total_frames = 0

    def create(self, **kwargs):
        self.window_width = kwargs.get('width', 800)
        self.window_height = kwargs.get('height', 600)
        self.window_name = kwargs.get('name', "My OpenGL window")
        self.opengl_id = glfw.create_window(self.window_width, self.window_height, self.window_name, None, None)

        glfw.set_window_size_callback(self.opengl_id, self.window_resize)
        glfw.set_key_callback(self.opengl_id, keyboard_handling.key_callback)
        glfw.set_cursor_pos_callback(self.opengl_id, context.main_context.cameras[self.camera_id].mouse_callback)
        glfw.set_input_mode(self.opengl_id, glfw.CURSOR, glfw.CURSOR_DISABLED)\

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
        context.main_context.current_camera = self.camera_id

        self.activate()

        self.user_function()

        cam = context.main_context.cameras[self.camera_id]
        cam.process_keyboard()
        cam.camera_view_matrix = cam.get_view_matrix()

        glfw.poll_events()
        glClearColor(self.background_color_r, self.background_color_g,
                     self.background_color_b, self.background_color_alpha)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        #glCullFace(GL_FRONT)
        context.main_context.num_active_lights = 0
        for i in context.main_context.lights:
            if i.hided == 0:
                i.update_shade_map()
                context.main_context.num_active_lights += 1
        #glCullFace(GL_BACK)

        glViewport(0, 0, self.window_width, self.window_height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        for i in context.main_context.objects:
            if i.hided == 0:
                i.real_draw()

        glfw.swap_buffers(self.opengl_id)

        # TODO: make this not b exit, but just closing the window:
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

        context.main_context.cameras[self.camera_id].camera_projection_matrix = camera_projection_matrix


class TronProgram:
    def __init__(self):
        if not glfw.init():
            print("(!) TRON FATAL ERROR: Failed to init GLFW!")
            sys.exit(1)

    def new_window(self, camera_id, **kwargs):
        context.main_context.windows.append(TronWindow(camera_id, **kwargs))

    def new_camera(self):
        context.main_context.cameras.append(TronCamera())

        return context.main_context.cameras[-1].id

    def main_loop(self):
        glEnable(GL_DEPTH_TEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

        while True:
            for window in context.main_context.windows:
                window.draw()


class FPS:
    def __init__(self, user_interval):
        self.startTime = time.time()
        self.interval = user_interval
        self.counter = 0

    def update(self):
        self.counter += 1

    def print_fps(self):
        if (time.time() - self.startTime) > self.interval:
            print("FPS: ", self.counter / (time.time() - self.startTime))
            self.counter = 0
            self.startTime = time.time()

    def update_and_print(self):
        self.counter += 1
        if (time.time() - self.startTime) > self.interval:
            fps = self.counter / (time.time() - self.startTime)
            print("FPS: ", fps)
            self.counter = 0
            self.startTime = time.time()
            return fps
        return 0

