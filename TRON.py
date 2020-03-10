import sys
import glfw
from OpenGL.GL import *
import time

import shader_handling
import context
import structure_handling
import object_handling
import file_handling
import light_handling
import keyboard_handling
import camera_handling
import window_handling
import mouse_handling
import primitives_creation

from file_handling import TronFileHandler
from object_handling import TronObject, TronObject2D
from context import main_context
from light_handling import TronDirectionalLight
from primitives_creation import *


class TronProgram:
    def __init__(self):
        if not glfw.init():
            print("(!) TRON FATAL ERROR: Failed to init GLFW!")
            sys.exit(1)

    def new_window(self, camera_id, **kwargs):
        context.main_context.windows.append(window_handling.TronWindow(camera_id, **kwargs))

        return context.main_context.windows[-1]

    def new_camera(self):
        context.main_context.cameras.append(camera_handling.TronCamera())

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

